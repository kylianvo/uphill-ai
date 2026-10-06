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

    var title: String { isAthlete ? "Notes from your coach" : "Coach Notes (\(notes.count))" }
    var emptyText: String { "No coach notes yet. Leave training feedback or execution advice here." }
    var placeholder: String { isAthlete ? "Reply to your coach…" : "Add a note for this \(targetType)..." }
    var postLabel: String { isAthlete ? "Reply" : "Post" }

    func authorLabel(for note: CoachNote) -> String? {
        guard isAthlete else { return nil }
        return note.coachId == athleteId ? "You" : "Coach"
    }
}
