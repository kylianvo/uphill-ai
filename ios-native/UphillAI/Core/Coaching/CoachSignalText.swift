import Foundation

/// Words a coach signal (code + params from /api/coaching/overview) as one short sentence.
enum CoachSignalText {
    static let codes = [
        "reported_pain", "reported_sick", "missed_many", "overload", "plan_to_review", "needs_plan",
        "draft_unpublished", "next_block_due", "changes_to_approve", "no_sync", "missed_key", "adherence_drop",
        "hrv_low", "hard_easy_days", "race_soon", "phase_start", "longest_long_run", "block_done", "new_result",
    ]

    static func sentence(_ s: CoachSignal, lang: AppLanguage = .current) -> String {
        func str(_ k: String) -> String { if case .string(let v) = s.params[k] { return v }; return "" }
        func int(_ k: String) -> Int? {
            switch s.params[k] {
            case .int(let v): v
            case .double(let v): Int(v.rounded())
            default: nil
            }
        }
        func n(_ k: String) -> Int { int(k) ?? 0 }
        func day(_ k: String) -> String { L(str(k), in: lang) }
        func phase(_ k: String) -> String { str(k).capitalized } // phase names stay English (Base, Build, Peak, Taper)

        switch s.code {
        case "reported_pain": return L("Logged pain on %@", in: lang, day("day"))
        case "reported_sick": return L("Logged illness on %@", in: lang, day("day"))
        case "missed_many": return L("Missed %lld sessions this week", in: lang, n("count"))
        case "overload": return L("Did %lld min vs %lld planned", in: lang, n("done_min"), n("planned_min"))
        case "plan_to_review":
            if let h = int("waiting_hours") { return L("New plan · waiting %lld h", in: lang, h) }
            return L("Week %lld to review", in: lang, n("week"))
        case "needs_plan": return L("No plan yet", in: lang)
        case "draft_unpublished": return L("Draft plan not published", in: lang)
        case "next_block_due": return L("Next week due in %lld days", in: lang, n("days"))
        case "changes_to_approve": return L("%lld changes to approve", in: lang, n("count"))
        case "no_sync": return L("No watch sync for %lld days", in: lang, n("days"))
        case "missed_key": return L("Missed %@ on %@", in: lang, str("title"), day("day"))
        case "adherence_drop":
            if let from = int("from_pct") { return L("Done %lld%% → %lld%%", in: lang, from, n("to_pct")) }
            return L("Done %lld%%", in: lang, n("to_pct"))
        case "hrv_low": return L("HRV low %lld of the last 3 days", in: lang, n("days"))
        case "hard_easy_days": return L("%lld easy days felt hard", in: lang, n("count"))
        case "race_soon": return L("Races %1$@ in %2$lld days", in: lang, str("race"), n("days"))
        case "phase_start":
            let key = str("when") == "this_week" ? "Starts %@ this week" : "Starts %@ next week"
            return L(key, in: lang, phase("phase"))
        case "longest_long_run":
            let m = n("minutes")
            return L("Longest Long Run: %@", in: lang, String(format: "%d h %02d", m / 60, m % 60))
        case "block_done": return L("Finished %@ phase", in: lang, phase("phase"))
        case "new_result":
            guard let sec = int("finish_time_sec") else { return L("New result: %@", in: lang, str("race")) }
            let time = String(format: "%d:%02d:%02d", sec / 3600, sec / 60 % 60, sec % 60)
            return L("New result: %@ %@", in: lang, str("race"), time)
        default: return s.code
        }
    }
}
