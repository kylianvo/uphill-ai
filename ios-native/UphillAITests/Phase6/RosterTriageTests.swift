import Foundation
import Testing
@testable import UphillAI

@Suite("RosterTriageTests")
struct RosterTriageTests {
    private func sig(_ code: String, _ sev: CoachSeverity, _ params: [String: JSONValue] = [:]) -> CoachSignal {
        CoachSignal(code: code, severity: sev, params: params)
    }

    private func stats(_ planned: Int, _ done: Int, key: (Int, Int) = (0, 0), min: (Int, Int) = (0, 0)) -> CoachWeekStats {
        CoachWeekStats(sessionsPlanned: planned, sessionsDone: done, keyPlanned: key.0, keyDone: key.1,
                       minutesPlanned: min.0, minutesDone: min.1)
    }

    private func athlete(_ id: Int, _ name: String, status: String, signals: [CoachSignal] = [], planType: String = "review",
                         race: String? = "VMM 42K", level: String = "intermediate", phase: String? = "build",
                         week: CoachWeekStats? = nil, prev: [CoachWeekStats] = []) -> CoachOverviewAthlete {
        var a = CoachOverviewAthlete(
            athleteId: id, name: name, runnerLevel: level,
            activePlan: race.map { CoachAthleteActivePlan(planId: id, raceName: $0, raceDate: "2026-12-19", currentWeek: 4, totalWeeks: 12) }
        )
        a.status = status
        a.signals = signals
        a.planType = planType
        a.phase = phase
        a.week = week
        a.prevWeeks = prev
        return a
    }

    private var roster: [CoachOverviewAthlete] {
        [
            athlete(1, "Minh", status: "act_now", signals: [sig("reported_pain", .actNow, ["day": .string("Tuesday")])],
                    planType: "coached", week: stats(6, 3, key: (2, 1), min: (300, 150))),
            athlete(2, "Huy", status: "review_build", signals: [sig("plan_to_review", .reviewBuild, ["week": .int(1), "waiting_hours": .int(31)])],
                    race: "Dalat 50K", week: stats(4, 4, key: (1, 1), min: (200, 210))),
            athlete(3, "Thao", status: "review_build", signals: [sig("needs_plan", .reviewBuild)], planType: "coached", race: nil, phase: nil),
            athlete(4, "Quan", status: "check_in", signals: [sig("no_sync", .checkIn, ["days": .int(6)])], level: "beginner",
                    week: stats(5, 2, min: (250, 100)), prev: [stats(5, 5), stats(5, 4), stats(5, 5)]),
            athlete(5, "Anh", status: "on_track", signals: [sig("race_soon", .highlight, ["race": .string("VMM 42K"), "days": .int(9)])],
                    week: stats(5, 5, key: (2, 2), min: (250, 260))),
        ]
    }

    @Test func testEveryAthleteInExactlyOneSection() {
        let t = RosterTriage(athletes: roster, filter: RosterFilter(), weekOffset: 0)
        let ids = TriageSection.allCases.flatMap { t.athletes(in: $0).map(\.athleteId) }
        #expect(ids.sorted() == t.visible.map(\.athleteId).sorted())
        #expect(Set(ids).count == ids.count)
        #expect(t.athletes(in: .actNow).map(\.name) == ["Minh"])
        #expect(t.athletes(in: .reviewBuild).map(\.name) == ["Huy", "Thao"])
        #expect(t.athletes(in: .checkIn).map(\.name) == ["Quan"])
        #expect(t.athletes(in: .onTrack).map(\.name) == ["Anh"])
    }

    @Test func testActNowAthleteNeverOnTrack() {
        let filters = [RosterFilter(), RosterFilter(planType: "coached"), RosterFilter(race: "VMM 42K"),
                       RosterFilter(level: "intermediate"), RosterFilter(phase: "build")]
        for f in filters {
            let t = RosterTriage(athletes: roster, filter: f, weekOffset: 0)
            #expect(!t.athletes(in: .onTrack).contains { $0.name == "Minh" })
        }
    }

    @Test func testFiltersNarrowEverything() {
        let t = RosterTriage(athletes: roster, filter: RosterFilter(planType: "coached"), weekOffset: 0)
        #expect(t.visible.map(\.name) == ["Minh", "Thao"])
        #expect(t.counts.all == 5 && t.counts.review == 3 && t.counts.coached == 2)
        #expect(t.sessionsDonePct == 0.5)
    }

    @Test func testFilterToNobodyGivesNilStats() {
        let t = RosterTriage(athletes: roster, filter: RosterFilter(race: "Nowhere 10K"), weekOffset: 0)
        #expect(t.visible.isEmpty)
        #expect(t.sessionsDonePct == nil && t.keyDonePct == nil && t.volumePct == nil)
        #expect(t.groups(by: .race).isEmpty)
    }

    @Test func testStatsSumVisibleWeeks() {
        let t = RosterTriage(athletes: roster, filter: RosterFilter(), weekOffset: 0)
        #expect(t.sessionsDonePct == 14.0 / 20.0)
        #expect(t.keyDonePct == 4.0 / 5.0)
        #expect(t.volumePct == 720.0 / 1000.0)
    }

    @Test func testWeekOffsetUsesPrevWeeks() {
        let t = RosterTriage(athletes: roster, filter: RosterFilter(level: "beginner"), weekOffset: 2)
        #expect(t.sessionsDonePct == 4.0 / 5.0)
    }

    @Test func testGroupsByPlanType() {
        let t = RosterTriage(athletes: roster, filter: RosterFilter(), weekOffset: 0)
        let groups = t.groups(by: .planType)
        #expect(groups.map(\.label) == ["review", "coached"])
        #expect(groups.map(\.count) == [3, 2])
        #expect(groups[1].donePct == 0.5)
    }

    @Test func testHighlightsCollected() {
        let t = RosterTriage(athletes: roster, filter: RosterFilter(), weekOffset: 0)
        #expect(t.highlights.map(\.athlete.name) == ["Anh"])
    }

    @Test func testPrimaryActionMapping() {
        let cases: [(String, CoachSeverity, CoachAction?)] = [
            ("reported_pain", .actNow, .adaptWeek), ("reported_sick", .actNow, .adaptWeek),
            ("overload", .actNow, .adaptWeek), ("missed_many", .actNow, .adaptWeek),
            ("plan_to_review", .reviewBuild, .reviewPlan), ("needs_plan", .reviewBuild, .buildPlan),
            ("draft_unpublished", .reviewBuild, .openDraft), ("next_block_due", .reviewBuild, .buildNextWeek),
            ("changes_to_approve", .reviewBuild, .reviewChanges), ("no_sync", .checkIn, .note),
            ("missed_key", .checkIn, .note), ("race_soon", .highlight, nil),
        ]
        for (code, sev, action) in cases {
            #expect(athlete(9, "X", status: "x", signals: [sig(code, sev)]).primaryAction == action, "\(code)")
        }
    }

    @Test func testSentenceEnVi() {
        let pain = sig("reported_pain", .actNow, ["day": .string("Tuesday")])
        #expect(CoachSignalText.sentence(pain, lang: .en) == "Logged pain on Tuesday")
        #expect(CoachSignalText.sentence(pain, lang: .vi) == "Báo đau vào Thứ Ba")
        let review = sig("plan_to_review", .reviewBuild, ["week": .int(1), "waiting_hours": .int(31)])
        #expect(CoachSignalText.sentence(review, lang: .en) == "New plan · waiting 31 h")
        #expect(CoachSignalText.sentence(review, lang: .vi) == "Plan mới · chờ 31 giờ")
        let week5 = sig("plan_to_review", .reviewBuild, ["week": .int(5), "waiting_hours": .null])
        #expect(CoachSignalText.sentence(week5, lang: .en) == "Week 5 to review")
        let race = sig("race_soon", .highlight, ["race": .string("VMM 42K"), "days": .int(9)])
        #expect(CoachSignalText.sentence(race, lang: .en) == "Races VMM 42K in 9 days")
        let drop = sig("adherence_drop", .checkIn, ["from_pct": .int(70), "to_pct": .int(40)])
        #expect(CoachSignalText.sentence(drop, lang: .en) == "Done 70% → 40%")
        let longRun = sig("longest_long_run", .highlight, ["minutes": .int(250)])
        #expect(CoachSignalText.sentence(longRun, lang: .en) == "Longest Long Run: 4 h 10")
        // Every code has an EN and a VI sentence, and none fall back to the raw code.
        for code in CoachSignalText.codes {
            for lang in AppLanguage.allCases {
                let text = CoachSignalText.sentence(sig(code, .checkIn), lang: lang)
                #expect(!text.isEmpty && text != code, "\(code) \(lang)")
            }
        }
    }
}
