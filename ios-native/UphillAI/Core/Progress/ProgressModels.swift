import Foundation

/// `GET /api/progress`: only the cards that have enough data (backend services/progress_cards.py).
struct ProgressResponse: Decodable, Equatable, Sendable {
    let section: String
    let connected: Bool
    let hasPlan: Bool
    let planId: Int?
    let cards: [ProgressCard]
    let pending: [ProgressPending]

    func card(_ key: String) -> ProgressCard? { cards.first { $0.key == key } }
}

struct ProgressPending: Decodable, Equatable, Sendable {
    let key: String
    let needs: Int
    let have: Int
}

struct ProgressCard: Decodable, Equatable, Sendable, Identifiable {
    let key: String
    let value: Double?
    let unit: String?
    /// Dictionary keys keep the backend's snake_case: the decoder converts struct keys only.
    let series: [[String: JSONValue]]
    let band: [Double]?
    let note: [String: JSONValue]
    let asOf: String?
    let source: String?

    var id: String { key }
    var noteKey: String { note["key"]?.stringValue ?? key }
    func noteNumber(_ name: String) -> Double? { note[name]?.doubleValue }
    func noteString(_ name: String) -> String? { note[name]?.stringValue }

    /// The series as plottable points: x is a date or plan week, y the card's main measure.
    var points: [ProgressPoint] {
        let field = ["sleep": "value", "resting_hr": "value", "hrv": "value", "durability": "pct",
                     "load": "short", "volume": "km", "aerobic_speed": "pace", "consistency": "done", "response": "hrv"][key] ?? "value"
        return series.compactMap { row in
            guard let y = row[field]?.doubleValue else { return nil }
            if let day = row["date"]?.stringValue, let date = ProgressPoint.day.date(from: day) {
                return ProgressPoint(x: .day(date), y: y, row: row)
            }
            if let week = row["week"]?.doubleValue { return ProgressPoint(x: .week(Int(week)), y: y, row: row) }
            return nil
        }
    }
}

struct ProgressPoint: Equatable, Sendable, Identifiable {
    enum X: Equatable, Sendable, Hashable { case day(Date), week(Int) }
    let x: X
    let y: Double
    let row: [String: JSONValue]
    var id: X { x }

    static let day: DateFormatter = {
        let f = DateFormatter()
        f.calendar = Calendar(identifier: .gregorian)
        f.locale = Locale(identifier: "en_US_POSIX")
        f.timeZone = TimeZone(identifier: "UTC")
        f.dateFormat = "yyyy-MM-dd"
        return f
    }()
}

enum ProgressSection: String, CaseIterable, Sendable { case training, health }
