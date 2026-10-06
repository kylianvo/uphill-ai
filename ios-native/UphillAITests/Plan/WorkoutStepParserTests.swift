import Testing
@testable import UphillAI

@Suite("WorkoutStepParserTests")
struct WorkoutStepParserTests {
    private func makeWorkout(
        title: String = "Hill Repeats",
        type: String = "Interval",
        duration: Double = 60,
        pace: String? = "5:30 /km",
        reps: Int? = 6,
        repVal: Double? = 3,
        repUnit: String? = "min",
        walkVal: Double? = 2,
        desc: String? = "Overall: Build uphill power.\nProcess: 15 min warm-up → 6 x 3 min uphill intervals → 10 min cool-down.\nBenefit: Improves VO2 max and fatigue resistance.\nWarning: Do not sprint the first 30 seconds."
    ) -> Workout {
        let json = """
        {
            "id": 10,
            "plan_id": 1,
            "week_number": 1,
            "day_of_week": "Tuesday",
            "phase": "Base",
            "title": "\(title)",
            "type": "\(type)",
            "duration_minutes": \(duration),
            "target_zone": "Z4",
            "target_pace": \(pace != nil ? "\"\(pace!)\"" : "null"),
            "interval_reps": \(reps != nil ? String(reps!) : "null"),
            "interval_rep_value": \(repVal != nil ? String(repVal!) : "null"),
            "interval_rep_unit": \(repUnit != nil ? "\"\(repUnit!)\"" : "null"),
            "walk_interval_value": \(walkVal != nil ? String(walkVal!) : "null"),
            "description": \(desc != nil ? "\"\(desc!.replacingOccurrences(of: "\n", with: "\\n"))\"" : "null")
        }
        """.data(using: .utf8)!
        return try! JSONCoding.decoder.decode(Workout.self, from: json)
    }

    @Test func parseStructuredDescription() {
        let w = makeWorkout()
        let parsed = WorkoutStepParser.parseDescription(w.description)
        #expect(parsed.benefit == "Improves VO2 max and fatigue resistance.")
        #expect(parsed.warning == "Do not sprint the first 30 seconds.")
        #expect(parsed.process?.contains("15 min warm-up") == true)
    }

    @Test func parseExecutionStepsTimeline() {
        let w = makeWorkout()
        let parsed = WorkoutStepParser.parseDescription(w.description)
        let steps = WorkoutStepParser.parseSteps(workout: w, description: parsed, isTreadmill: false)

        #expect(steps.count == 3)
        #expect(steps[0].phase == .warmup)
        #expect(steps[1].phase == .main)
        #expect(steps[1].target.contains("6 × 3 min"))
        #expect(steps[1].recovery?.contains("2 min") == true)
        #expect(steps[2].phase == .cooldown)
    }

    @Test func treadmillToggleCalculatesSpeed() {
        let w = makeWorkout(pace: "6:00 /km")
        let parsed = WorkoutStepParser.parseDescription(w.description)
        let tmSteps = WorkoutStepParser.parseSteps(workout: w, description: parsed, isTreadmill: true)
        #expect(tmSteps[1].target.contains("km/h"))
    }

    // MARK: - Real production description (labels on their own lines, or flattened with " / ")

    private static let production = "Warm up 5 min easy jogging / 25 min steady continuous running @ Zone 1-2 / Target pace: 6:24 - 5:42 /km / Overall: Short, non-fatiguing morning aerobic run… / Reason: Acts as an aerobic primer… / Benefit: Enhances capillary circulation… / Warning: Strictly keep heart rate below 140 bpm; do not push pace on flat stretches. / Cool-down 5-10 min"

    private func productionWorkout(newlines: Bool = false) -> Workout {
        let text = newlines ? Self.production.replacingOccurrences(of: " / ", with: "\n") : Self.production
        return TestData.workout(["duration_minutes": 35.0, "target_pace": "6:24 - 5:42 /km", "type": "Easy Run",
                                 "target_zone": "Zone 1", "description": text])
    }

    @Test(arguments: [false, true])
    func productionNotesLandInTheirOwnSections(newlines: Bool) {
        let parsed = WorkoutStepParser.parseDescription(productionWorkout(newlines: newlines).description)
        #expect(parsed.intent == "Short, non-fatiguing morning aerobic run…")
        #expect(parsed.benefit == "Acts as an aerobic primer…\nEnhances capillary circulation…")
        #expect(parsed.warning == "Strictly keep heart rate below 140 bpm; do not push pace on flat stretches.")
        #expect(parsed.coachNotes == nil)
        #expect(parsed.process == "Warm up 5 min easy jogging\n25 min steady continuous running @ Zone 1-2\nTarget pace: 6:24 - 5:42 /km\nCool-down 5-10 min")
    }

    @Test(arguments: [false, true])
    func productionStepsKeepOnlyTheirOwnLine(newlines: Bool) {
        let w = productionWorkout(newlines: newlines)
        let steps = WorkoutStepParser.parseSteps(workout: w, description: WorkoutStepParser.parseDescription(w.description), isTreadmill: false)
        #expect(steps.map(\.phase) == [.warmup, .main, .cooldown])
        #expect(steps[0].steps == ["Warm up 5 min easy jogging"])
        #expect(steps[1].steps == ["25 min steady continuous running @ Zone 1-2", "Target pace: 6:24 - 5:42 /km"])
        #expect(steps[2].steps == ["Cool-down 5-10 min"])
        let everyLine = steps.flatMap(\.steps).joined(separator: " ")
        for leaked in ["Overall", "Reason", "Benefit", "Warning", "Strictly keep heart rate"] {
            #expect(!everyLine.contains(leaked))
        }
    }

    @Test func mainSetDurationUsesTheDescriptionsOwnNumber() {
        let w = productionWorkout()
        let steps = WorkoutStepParser.parseSteps(workout: w, description: WorkoutStepParser.parseDescription(w.description), isTreadmill: false)
        #expect(steps[1].duration == "25 min")   // text says 25; the old duration-20 arithmetic said 15
    }

    @Test func mainSetDurationFallsBackToTotalMinusWarmupAndCooldown() {
        let w = TestData.workout(["duration_minutes": 60.0, "description": "Warm up 10 min easy\nSteady climbing at Zone 2\nCool-down 5 min"])
        let steps = WorkoutStepParser.parseSteps(workout: w, description: WorkoutStepParser.parseDescription(w.description), isTreadmill: false)
        #expect(steps[1].duration == "45 min")
    }

    @Test func intervalSetDurationIsNotTakenFromTheRepLength() {
        let w = TestData.workout(["duration_minutes": 60.0, "interval_reps": 6, "interval_rep_value": 3.0, "interval_rep_unit": "min",
                                  "description": "Warm up 15 min easy\n6 x 3 min uphill\nCool-down 10 min"])
        let steps = WorkoutStepParser.parseSteps(workout: w, description: WorkoutStepParser.parseDescription(w.description), isTreadmill: false)
        #expect(steps[1].duration == "35 min")
    }

    @Test func plainDescriptionWithoutLabelsStaysUnstructured() {
        let parsed = WorkoutStepParser.parseDescription("Easy aerobic run on rolling trail.")
        #expect(parsed.overview == "Easy aerobic run on rolling trail.")
        #expect(parsed.process == "Easy aerobic run on rolling trail.")
        #expect(parsed.intent == nil && parsed.benefit == nil && parsed.warning == nil)
    }
}
