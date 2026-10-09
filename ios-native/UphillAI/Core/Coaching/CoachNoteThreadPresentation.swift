import Foundation

/// What a note thread shows, depending on who is looking at it. An athlete reading their own
/// workout sees "Notes from your coach", not the coach-facing "leave feedback" copy.
///
/// The backend's `require_athlete_access` lets an athlete post on their own id, so the reply
/// box stays for athletes. No endpoint tells an athlete who their coach is (`my-invites` only
/// lists pending invites), so "a coach is linked" is inferred from a note someone else wrote.
struct CoachNoteThreadPresentation: Equatable {
    enum Audience: Equatable { case coach, athlete }

    var audience: Audience
    var athleteId: Int
    var targetType: String
    var notes: [CoachNote]

    private var isAthlete: Bool { audience == .athlete }

    var hasCoachNotes: Bool { notes.contains { $0.coachId != athleteId } }

    /// Athletes see nothing until a coach has written; coaches always see the thread.
    var isVisible: Bool { !isAthlete || hasCoachNotes }

    var title: String { isAthlete ? L("Notes from your coach") : L("Coach Notes (%lld)", notes.count) }
    var emptyText: String { L("No coach notes yet. Leave training feedback or execution advice here.") }
    var placeholder: String { isAthlete ? L("Reply to your coach…") : L("Add a note for this %@...", L(targetType)) }
    var postLabel: String { isAthlete ? L("Reply") : L("Post") }

    /// The backend sends `created_at` as ISO 8601 with microseconds ("2026-10-06T08:50:49.566735+00:00").
    /// Shown as a short local date and time; anything unparseable is hidden rather than shown raw.
    static func timestampLabel(_ raw: String, timeZone: TimeZone = .current, locale: Locale = .current) -> String? {
        let trimmed = raw.replacingOccurrences(of: #"(\.\d{3})\d+"#, with: "$1", options: .regularExpression)
        let parser = ISO8601DateFormatter()
        parser.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
        guard let date = parser.date(from: trimmed) ?? ISO8601DateFormatter().date(from: trimmed) else { return nil }
        var style = Date.FormatStyle(date: .abbreviated, time: .shortened, locale: locale)
        style.timeZone = timeZone
        return date.formatted(style)
    }

    func authorLabel(for note: CoachNote) -> String? {
        guard isAthlete else { return nil }
        return note.coachId == athleteId ? L("You") : "Coach"
    }
}
