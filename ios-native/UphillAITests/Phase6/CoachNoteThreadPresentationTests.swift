import Testing
@testable import UphillAI

struct CoachNoteThreadPresentationTests {
    private let athleteId = 7
    private func note(by coachId: Int, id: Int = 1) -> CoachNote {
        CoachNote(id: id, coachId: coachId, athleteId: 7, targetType: "workout", targetId: 3, note: "Keep it easy.")
    }
    private func presentation(_ audience: CoachNoteThreadPresentation.Audience, _ notes: [CoachNote]) -> CoachNoteThreadPresentation {
        CoachNoteThreadPresentation(audience: audience, athleteId: athleteId, targetType: "workout", notes: notes)
    }

    @Test func athleteSeesCoachWordingNotTheCoachFacingPrompt() {
        let p = presentation(.athlete, [note(by: 99)])
        #expect(p.title == "Notes from your coach")
        #expect(p.placeholder == "Reply to your coach…")
        #expect(p.postLabel == "Reply")
        #expect(p.title.contains("Coach Notes") == false)
    }

    @Test func athleteWithNoNotesSeesNoSection() {
        #expect(presentation(.athlete, []).isVisible == false)
    }

    @Test func athletesOwnPostsAloneDoNotCountAsALinkedCoach() {
        #expect(presentation(.athlete, [note(by: athleteId)]).isVisible == false)
    }

    @Test func athleteSeesSectionOnceACoachHasWritten() {
        let p = presentation(.athlete, [note(by: athleteId, id: 1), note(by: 99, id: 2)])
        #expect(p.isVisible)
        #expect(p.authorLabel(for: p.notes[0]) == "You")
        #expect(p.authorLabel(for: p.notes[1]) == "Coach")
    }

    @Test func coachAlwaysSeesTheThreadWithTheOriginalCopy() {
        let p = presentation(.coach, [])
        #expect(p.isVisible)
        #expect(p.title == "Coach Notes (0)")
        #expect(p.emptyText.contains("Leave training feedback"))
        #expect(p.postLabel == "Post")
        #expect(p.authorLabel(for: note(by: 99)) == nil)
    }
}
