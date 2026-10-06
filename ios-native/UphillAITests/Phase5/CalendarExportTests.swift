import Testing
import Foundation
@testable import UphillAI

@Suite("CalendarExportTests")
struct CalendarExportTests {

    private func makeTestPlan() -> Plan {
        Plan(
            id: 42,
            raceName: "Vietnam Mountain Marathon 50K",
            raceDate: "2026-10-18",
            goalType: "finish",
            targetTimeHours: 7.5,
            totalWeeks: 8,
            currentWeek: 1,
            courseDistanceKm: 50.0,
            courseElevationGainM: 2200.0,
            startDate: "2026-08-24",
            planStatus: "active",
            createdAt: "2026-08-20T10:00:00Z"
        )
    }

    private func makeTestWorkouts(planId: Int = 42) -> [Workout] {
        let json = """
        [
            {
                "id": 101,
                "plan_id": \(planId),
                "week_number": 1,
                "day_of_week": "Monday",
                "phase": "Base",
                "title": "Easy Aerobic Run",
                "type": "Easy",
                "duration_minutes": 50.0,
                "distance_km": 8.0,
                "target_zone": "Zone 2",
                "target_hr_range": "130-142 bpm",
                "target_pace": "6:15/km",
                "description": "Keep conversation pace, flat terrain.",
                "fueling_tip": "Hydrate well with 500ml water + electrolytes.",
                "is_priority": false
            },
            {
                "id": 102,
                "plan_id": \(planId),
                "week_number": 1,
                "day_of_week": "Wednesday",
                "phase": "Base",
                "title": "Hill Repeats",
                "type": "Workout",
                "duration_minutes": 60.0,
                "distance_km": 10.0,
                "target_zone": "Zone 4",
                "target_hr_range": "165-175 bpm",
                "elevation_gain_m": 400.0,
                "description": "6x 2-min hill charges at 8% grade.",
                "is_priority": true
            },
            {
                "id": 103,
                "plan_id": \(planId),
                "week_number": 1,
                "day_of_week": "Sunday",
                "phase": "Base",
                "title": "Rest & Mobility",
                "type": "Rest",
                "duration_minutes": 0.0,
                "target_zone": "Zone 1",
                "description": "Full rest day; 15 mins foam rolling.",
                "is_priority": false
            }
        ]
        """
        let decoder = JSONCoding.decoder
        return try! decoder.decode([Workout].self, from: json.data(using: .utf8)!)
    }

    @Test func testEscapeText() {
        let raw = "Run on trail, then hill; rest\\mobility\nDone"
        let escaped = CalendarExportManager.escapeText(raw)
        #expect(escaped.contains("\\,"))
        #expect(escaped.contains("\\;"))
        #expect(escaped.contains("\\\\"))
        #expect(escaped.contains("\\n"))
    }

    @Test func testFoldLine() {
        let longLine = "DESCRIPTION:This is a very long line of workout instructions meant to test RFC 5545 line folding at 75 bytes."
        let folded = CalendarExportManager.foldLine(longLine)
        #expect(folded.contains("\r\n "))
    }

    @Test func testGenerateAllDayIcs() {
        let plan = makeTestPlan()
        let workouts = makeTestWorkouts()
        let manager = CalendarExportManager.shared

        let ics = manager.generateIcsString(plan: plan, workouts: workouts, timePref: "all_day")

        #expect(ics.contains("BEGIN:VCALENDAR"))
        #expect(ics.contains("VERSION:2.0"))
        #expect(ics.contains("PRODID:-//Uphill AI//Workout Scheduler//EN"))
        #expect(ics.contains("BEGIN:VEVENT"))
        #expect(ics.contains("SUMMARY:Uphill AI: Easy Aerobic Run"))
        #expect(ics.contains("DTSTART;VALUE=DATE:"))
        #expect(ics.contains("DTEND;VALUE=DATE:"))
        #expect(ics.contains("SUMMARY:Uphill AI: Rest & Mobility (Rest)"))
        #expect(ics.contains("END:VCALENDAR"))
    }

    @Test func testGenerateTimedIcs() {
        let plan = makeTestPlan()
        let workouts = makeTestWorkouts()
        let manager = CalendarExportManager.shared

        let ics = manager.generateIcsString(plan: plan, workouts: workouts, timePref: "morning")

        #expect(ics.contains("BEGIN:VCALENDAR"))
        #expect(ics.contains("DTSTART:"))
        #expect(ics.contains("T060000"))
        #expect(ics.contains("DTEND:"))
    }

    @Test func testExportToTemporaryFile() throws {
        let plan = makeTestPlan()
        let workouts = makeTestWorkouts()
        let manager = CalendarExportManager.shared

        let url = try manager.exportToTemporaryIcsFile(plan: plan, workouts: workouts, timePref: "all_day")
        #expect(FileManager.default.fileExists(atPath: url.path))
        #expect(url.pathExtension == "ics")

        let fileData = try Data(contentsOf: url)
        #expect(!fileData.isEmpty)
        let fileContent = String(data: fileData, encoding: .utf8)!
        #expect(fileContent.contains("BEGIN:VCALENDAR"))
    }
}
