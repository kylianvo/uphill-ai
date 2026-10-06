import Testing
@testable import UphillAI

@Suite("WorkoutDescriptionParserTests")
struct WorkoutDescriptionParserTests {

    @Test func extractDescriptionSectionsAllSections() {
        let description = """
        Process: Warm up 10m → Run 30m → Cool down 5m.
        Overall: Great run.
        Reason: Recovery day.
        Benefit: Aerobic base.
        Warning: Don't sprint.
        """
        let sections = WorkoutDescriptionParser.extractDescriptionSections(description)
        #expect(sections.process == "Warm up 10m → Run 30m → Cool down 5m.")
        #expect(sections.overall == "Great run.")
        #expect(sections.reason == "Recovery day.")
        #expect(sections.benefit == "Aerobic base.")
        #expect(sections.warning == "Don't sprint.")
    }

    @Test func extractDescriptionSectionsMissingSections() {
        let description = "Process: Warm up 10m → Run 30m."
        let sections = WorkoutDescriptionParser.extractDescriptionSections(description)
        #expect(sections.process == "Warm up 10m → Run 30m.")
        #expect(sections.overall == nil)
        #expect(sections.reason == nil)
        #expect(sections.benefit == nil)
        #expect(sections.warning == nil)
    }

    @Test func extractDescriptionSectionsSingleProcessOnly() {
        let description = "Process: Just the steps."
        let sections = WorkoutDescriptionParser.extractDescriptionSections(description)
        #expect(sections.process == "Just the steps.")
        #expect(sections.overall == nil)
        #expect(sections.reason == nil)
        #expect(sections.benefit == nil)
        #expect(sections.warning == nil)
    }

    @Test func extractDescriptionSectionsUnstructuredText() {
        let sections = WorkoutDescriptionParser.extractDescriptionSections("Just run easy today, whatever feels good.")
        #expect(sections.overall == nil)
        #expect(sections.process == nil)
        #expect(sections.reason == nil)
        #expect(sections.benefit == nil)
        #expect(sections.warning == nil)
    }

    @Test func extractDescriptionSectionsRescuesMisplacedExercises() {
        let description =
            "Process: Warm-up with gentle floor mobility movements for 5 minutes → " +
            "Perform the bodyweight mobility strength circuit for 20 minutes → " +
            "Cool-down with passive stretching for 5 minutes. " +
            "Overall: A low-load, bodyweight strength session. " +
            "Reason: Placed on Thursday to avoid extra fatigue. " +
            "Benefit: Encourages pelvic stability. " +
            "Warning: Focus strictly on slow, controlled movement with perfect posture. " +
            "Perform 2 sets of 10 repetitions of bodyweight Squats with 60 seconds of rest between sets. " +
            "Perform 2 sets of 30-second Planks with 45 seconds of rest between sets."

        let sections = WorkoutDescriptionParser.extractDescriptionSections(description)

        #expect(sections.process ==
            "Warm-up with gentle floor mobility movements for 5 minutes → " +
            "Perform 2 sets of 10 repetitions of bodyweight Squats with 60 seconds of rest between sets → " +
            "Perform 2 sets of 30-second Planks with 45 seconds of rest between sets → " +
            "Cool-down with passive stretching for 5 minutes."
        )
        #expect(sections.warning == "Focus strictly on slow, controlled movement with perfect posture.")
    }

    @Test func extractDescriptionSectionsLeavesCleanWarningUntouched() {
        let description = """
        Process: Warm up 10 min easy → 20 min @ tempo pace → cool down 10 min.
        Warning: Stop if calf tightness returns.
        """
        let sections = WorkoutDescriptionParser.extractDescriptionSections(description)
        #expect(sections.process == "Warm up 10 min easy → 20 min @ tempo pace → cool down 10 min.")
        #expect(sections.warning == "Stop if calf tightness returns.")
    }

    @Test func parseExecutionStepsArrowSeparated() {
        let result = WorkoutDescriptionParser.parseExecutionSteps(
            "Warm up 10 min easy jog → 4 x 6min @ Zone 4, 2min jog recovery → cool down 10 min stretch"
        )
        #expect(result.warmup == "Warm up 10 min easy jog")
        #expect(result.mainSteps == ["4 x 6min @ Zone 4, 2min jog recovery"])
        #expect(result.cooldown == "cool down 10 min stretch")
    }

    @Test func parseExecutionStepsSentenceFallback() {
        let result = WorkoutDescriptionParser.parseExecutionSteps(
            "Warm up with 10 minutes of easy jogging. Complete 4 sets of 12 squats with 90 seconds rest between sets. Cool down and stretch for 10 minutes."
        )
        #expect(result.warmup?.contains("Warm up") == true)
        #expect(result.mainSteps.joined(separator: " ").contains("4 sets of 12 squats") == true)
        #expect(result.cooldown?.contains("Cool down") == true)
    }

    @Test func parseExecutionStepsExpandsSemicolonMainSteps() {
        let result = WorkoutDescriptionParser.parseExecutionSteps(
            "Warm up with 5 minutes of mobility. " +
            "Complete 5 sets of 10 reps of Squats with 45 seconds rest between sets; " +
            "perform 5 sets of 10 reps of Lunges with 45 seconds rest between sets; " +
            "perform 5 sets of 12 reps of Glute Bridges with 30 seconds rest between sets. " +
            "Cool down with 5 minutes of stretching."
        )
        #expect(result.mainSteps == [
            "Complete 5 sets of 10 reps of Squats with 45 seconds rest between sets",
            "perform 5 sets of 10 reps of Lunges with 45 seconds rest between sets",
            "perform 5 sets of 12 reps of Glute Bridges with 30 seconds rest between sets."
        ])
    }

    @Test func selectMainSetTextPrefersAISections() {
        let library = LibraryExecutionInfo(
            execution: "3-4 sets of 8-12 reps at moderate weight.",
            overview: "Strength work builds durability for the descents."
        )
        let description = """
        Overall: Today's specific strength focus.
        Process: 5 sets of 10 reps weighted step-ups → 3 sets of 12 lunges each leg.
        """
        let result = WorkoutDescriptionParser.selectMainSetText(library: library, description: description)
        #expect(result.executionText == "5 sets of 10 reps weighted step-ups → 3 sets of 12 lunges each leg.")
        #expect(result.overviewText == "Today's specific strength focus.")
    }

    @Test func selectMainSetTextFallsBackWhenNil() {
        let library = LibraryExecutionInfo(
            execution: "3-4 sets of 8-12 reps at moderate weight.",
            overview: "Strength work builds durability for the descents."
        )
        let result = WorkoutDescriptionParser.selectMainSetText(library: library, description: nil)
        #expect(result.executionText == library.execution)
        #expect(result.overviewText == library.overview)
    }

    @Test func selectMainSetTextFallsBackWhenWhitespaceOnly() {
        let library = LibraryExecutionInfo(
            execution: "3-4 sets of 8-12 reps at moderate weight.",
            overview: "Strength work builds durability for the descents."
        )
        let description = """
        Reason: Scheduled for recovery.
        Process:
        Overall:
        """
        let result = WorkoutDescriptionParser.selectMainSetText(library: library, description: description)
        #expect(result.executionText == library.execution)
        #expect(result.overviewText == library.overview)
    }

    @Test func buildCoachNotesContentExcludesProcess() {
        let description = """
        Overall: Summary.
        Process: Steps that belong in Main Set only.
        Reason: Because of last week's RPE.
        Benefit: Adaptation.
        Warning: Watch your knees.
        """
        let content = WorkoutDescriptionParser.buildCoachNotesContent(description)
        #expect(content.hasSections == true)
        #expect(content.overall == "Summary.")
        #expect(content.reason == "Because of last week's RPE.")
        #expect(content.benefit == "Adaptation.")
        #expect(content.warning == "Watch your knees.")
    }

    @Test func buildCoachNotesContentFallbackToRaw() {
        let description = "Just take it easy today."
        let content = WorkoutDescriptionParser.buildCoachNotesContent(description)
        #expect(content.hasSections == false)
        #expect(content.fallbackText == description)
    }

    @Test func extractLeadingMinutesFindsNumber() {
        #expect(WorkoutDescriptionParser.extractLeadingMinutes("15-minute easy Zone 1/2 warm-up.") == 15)
        #expect(WorkoutDescriptionParser.extractLeadingMinutes("Warmup 10m.") == 10)
        #expect(WorkoutDescriptionParser.extractLeadingMinutes("Easy warm-up jog.") == nil)
        #expect(WorkoutDescriptionParser.extractLeadingMinutes(nil) == nil)
    }

    @Test func mainDurationMinutesCalculation() {
        let steps = ExecutionSteps(
            warmup: "15-minute easy warm-up.",
            mainSteps: ["Run tempo."],
            cooldown: "10-minute cool-down."
        )
        #expect(WorkoutDescriptionParser.mainDurationMinutes(totalMinutes: 60, steps: steps) == 35)

        let stepsMissingWarm = ExecutionSteps(warmup: nil, mainSteps: ["Run tempo."], cooldown: "10-minute cool-down.")
        #expect(WorkoutDescriptionParser.mainDurationMinutes(totalMinutes: 60, steps: stepsMissingWarm) == 60)

        let stepsNoCooldownNum = ExecutionSteps(warmup: "15-minute easy warm-up.", mainSteps: ["Run tempo."], cooldown: "Easy jog to finish.")
        #expect(WorkoutDescriptionParser.mainDurationMinutes(totalMinutes: 60, steps: stepsNoCooldownNum) == 60)

        let stepsClamped = ExecutionSteps(warmup: "40-minute warm-up.", mainSteps: ["Run tempo."], cooldown: "40-minute cool-down.")
        #expect(WorkoutDescriptionParser.mainDurationMinutes(totalMinutes: 60, steps: stepsClamped) == 0)
    }
}
