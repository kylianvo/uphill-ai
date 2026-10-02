import Foundation
import Testing
@testable import UphillAI

struct ScheduleMessagesTests {
    @Test func everyGuardUsesExactWebCopy() {
        let expected = [
            "G1_not_owner": "This workout isn't in your active plan.",
            "G2_history": "This workout is already completed or matched to an activity, so it can't be moved.",
            "G3_past_target": "You can't move a workout to a day that has already passed.",
            "G4_window": "Workouts can only move between this week and next week.",
            "G5_out_of_plan": "That week is outside your plan.",
            "G6_coach_linked": "You have a coach — ask them to change your schedule.",
            "G7_no_dates": "This plan has no start date, so only same-week day swaps are possible.",
            "STALE_changed": "Your plan changed since this was proposed.",
            "NOTHING_to_move": "Nothing would change.",
            "INVALID_operation": "That change isn't valid.",
            "unknown": "That change couldn't be made.",
        ]
        for (code, text) in expected { #expect(ScheduleMessages.guardText(code: code) == text) }
        #expect(ScheduleMessages.guardText(code: "future-code") == expected["unknown"])
    }
    @Test func warningParametersUseFullWeekdayAndVolume() {
        #expect(ScheduleMessages.warningText(ScheduleWarning(code: "W1_hard_stacking", params: ["day": "Tuesday", "week": "2"])) == "Two hard sessions on Tuesday (week 2).")
        #expect(ScheduleMessages.warningText(ScheduleWarning(code: "W1_hard_stacking", params: ["kind": "before_long_run", "day": "Saturday", "week": "3"])) == "Hard session on Saturday (week 3) right before the long run.")
        #expect(ScheduleMessages.warningText(ScheduleWarning(code: "W2_volume_shift", params: ["week": "2", "before_minutes": "180", "after_minutes": "225"])) == "Week 2 volume changes from 180 to 225 min.")
        #expect(ScheduleMessages.warningText(ScheduleWarning(code: "W3_pending_draft", params: ["title": "Easy Run"])) == "“Easy Run” is still pending coach review.")
    }
    @Test func decodesNumericParametersFromMoveResponse() throws {
        let result = try JSONCoding.decoder.decode(CalendarMoveResult.self, from: json(["workouts": [], "warnings": [["code": "W2_volume_shift", "params": ["week": 2, "before_minutes": 180, "after_minutes": 225]]]]))
        #expect(result.warnings.first?.params["week"] == "2")
    }
    @Test func structured422KeepsParameters() {
        let error = APIError.from(status: 422, data: json(["detail": ["code": "G4_window", "params": ["week": 9]]]))
        #expect(error == .scheduleGuard(status: 422, code: "G4_window", params: ["week": "9"]))
        #expect(error.userMessage == "Workouts can only move between this week and next week.")
    }
}
