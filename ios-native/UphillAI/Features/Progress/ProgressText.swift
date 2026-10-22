import Foundation

/// Card names, symbols, values and notes. The backend sends keys plus numbers; all wording lives here
/// (EN keys, VI in Localizable.xcstrings). Never "risk", never sleep stages.
enum ProgressText {
    static func title(_ key: String) -> String {
        switch key {
        case "sleep": L("Sleep")
        case "resting_hr": L("Resting HR")
        case "hrv": L("HRV")
        case "load": L("Training load")
        case "durability": L("Durability")
        case "volume": L("Volume & climb")
        case "consistency": L("Consistency")
        case "aerobic_speed": L("Aerobic speed")
        case "goal": L("Goal")
        case "coach_read": L("Coach's read")
        default: key
        }
    }

    static func symbol(_ key: String) -> String {
        switch key {
        case "sleep": "bed.double.fill"
        case "resting_hr": "heart.fill"
        case "hrv": "waveform.path.ecg"
        case "load": "chart.bar.fill"
        case "durability": "figure.run"
        case "volume": "mountain.2.fill"
        case "consistency": "checkmark.circle.fill"
        case "aerobic_speed": "speedometer"
        case "goal": "flag.checkered"
        default: "text.bubble.fill"
        }
    }

    /// The headline number with its unit, or nil for cards that lead with a sentence.
    static func value(_ card: ProgressCard) -> (number: String, unit: String)? {
        guard let v = card.value else { return nil }
        switch card.key {
        case "sleep": return (String(format: "%d:%02d", Int(v) / 60, Int(v) % 60), L("h asleep"))
        case "resting_hr": return ("\(Int(v.rounded()))", "bpm")
        case "hrv": return ("\(Int(v.rounded()))", "ms")
        case "durability": return (String(format: "%.1f", v), L("% drift"))
        case "load": return (String(format: "%.2f", v), L("× your usual"))
        case "volume": return (String(format: "%.0f", v), L("km last week"))
        case "consistency": return ("\(Int(v))", L("% done"))
        case "aerobic_speed": return (String(format: "%d:%02d", Int(v), Int((v - v.rounded(.down)) * 60)), "/km")
        default: return nil
        }
    }

    static func note(_ card: ProgressCard) -> String {
        let delta = abs(Int(card.noteNumber("delta") ?? 0))
        switch card.noteKey {
        case "sleep.below": return L("Less sleep than your usual this week")
        case "sleep.within": return L("Sleep is within your usual range")
        case "sleep.above": return L("More sleep than your usual this week")
        case "rhr.below": return L("%lld bpm below your usual", delta)
        case "rhr.within": return L("Resting HR is in your usual range")
        case "rhr.above": return L("%lld bpm above your usual", delta)
        case "hrv.below": return L("HRV is below your normal range")
        case "hrv.within": return L("HRV is in your normal range")
        case "hrv.above": return L("HRV is above your normal range")
        case "load.above": return L("Last 7 days are above your usual load")
        case "load.within": return L("Last 7 days are within your usual load")
        case "load.below": return L("Last 7 days are below your usual load")
        case "durability": return L("Heart rate drift on your last long runs. Lower is steadier.")
        case "volume": return L("Weekly km and climb against your plan")
        case "consistency":
            guard let reason = card.noteString("topMissedReason") else { return L("Planned sessions done in recent weeks") }
            return L("Most missed because: %@", missedReason(reason))
        case "aerobic_speed":
            switch card.noteString("b") {
            case "ahead": return L("Ahead of the path to your B goal")
            case "behind": return L("Behind the path to your B goal")
            default: return L("On the path to your B goal")
            }
        case "health.all_usual": return L("Everything is within your usual range.")
        case "health.off":
            let names = (card.note["contributors"]?.arrayValue ?? []).compactMap(\.stringValue).map(title)
            return L("Outside your usual: %@", names.joined(separator: ", "))
        default: return ""
        }
    }

    static func missedReason(_ reason: String) -> String {
        switch reason {
        case "busy": L("busy")
        case "sick": L("sick")
        case "pain": L("pain")
        case "tired": L("tired")
        case "weather": L("weather")
        default: L("other")
        }
    }

    static func pending(_ p: ProgressPending) -> String {
        switch p.key {
        case "sleep": L("Sleep appears after 7 nights of data")
        case "resting_hr": L("Resting HR appears after 7 days of data")
        case "hrv": L("HRV appears after 14 nights of data")
        case "durability": L("Durability appears after 3 long runs")
        case "load": L("Training load appears after 28 days of data")
        case "consistency": L("Consistency appears after 2 plan weeks")
        case "volume": L("Volume appears after 3 weeks of runs")
        case "aerobic_speed": L("Aerobic speed appears after 3 weeks of easy runs")
        default: ""
        }
    }

    static func explanation(_ key: String) -> String {
        switch key {
        case "sleep": L("Hours asleep each night, naps included, against your own usual range. Duration and timing are what watches measure well.")
        case "resting_hr": L("Your heart rate at rest, against your own usual range. A few beats above usual for several days can mean fatigue, illness or stress.")
        case "hrv": L("Overnight heart rate variability from one device, against its normal range. Use it as a warning sign, not a fitness score. Compare it only with yourself.")
        case "load": L("Your last 7 days of training against your last 6 weeks. Above usual is normal in a build week; several weeks above usual is worth a look.")
        case "durability": L("How much your heart rate drifts against grade-adjusted pace from the first half of a steady long run to the second. Lower and later drift means better endurance.")
        case "volume": L("Kilometres and climb you ran each week, against what the plan asked for.")
        case "consistency": L("Planned sessions you completed in each finished week. Sessions your watch matched count as done.")
        case "aerobic_speed": L("The pace you hold at your aerobic threshold heart rate on easy runs. Getting faster at the same heart rate means your aerobic base is growing.")
        default: ""
        }
    }
}
