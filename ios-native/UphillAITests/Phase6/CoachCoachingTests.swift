import Testing
import Foundation
@testable import UphillAI

@Suite("CoachCoachingTests")
struct CoachCoachingTests {

    @Test func testWorkoutTypeOptions() {
        #expect(CoachWorkoutTypeOption.all.count == 10)
        let easy = CoachWorkoutTypeOption.find("Easy")
        #expect(easy != nil)
        #expect(easy?.labelEn == "Easy")

        let tempo = CoachWorkoutTypeOption.find("Tempo")
        #expect(tempo != nil)
        #expect(tempo?.labelVi == "Tempo")

        let me = CoachWorkoutTypeOption.find("Muscular Endurance")
        #expect(me != nil)
        #expect(me?.labelVi == "Muscular Endurance (ME)")

        let unknown = CoachWorkoutTypeOption.find("NonExistent")
        #expect(unknown == nil)
    }

    // The decoding tests below read responses recorded from the local backend
    // (ios-native/scripts/record_fixtures.sh x coach). Never hand-edit them: if a type
    // stops matching, fix the type.

    @Test func testCoachOverviewDecoding() throws {
        let overview = try Fixture.decode(CoachOverview.self, "coaching_overview.json")
        #expect(overview.athletes.count == 1)
        let athlete = try #require(overview.athletes.first)
        #expect(athlete.name == "Preview Runner")
        #expect(athlete.runnerLevel == "intermediate")
        // The backend sends adherence as a fraction of 1.
        let adherence = try #require(athlete.adherencePct)
        #expect((0...1).contains(adherence))
        #expect(CoachFormat.wholePercent(adherence).hasSuffix("%"))
        #expect(!CoachFormat.wholePercent(adherence).contains("."))
        #expect(athlete.activePlan?.raceName == "Vietnam Mountain Marathon 42K")
        #expect(overview.actionItems.draftPlans.count == 1)
        #expect(overview.actionItems.draftPlans.first?.raceName == "Dalat Ultra Trail 50K")
        // The backend counts the coach-added workout and every workout of the draft plan as pending.
        #expect(overview.actionItems.pendingWorkoutApprovals.contains { $0.planId == athlete.activePlan?.planId })
        #expect(overview.workoutTypeMix.allSatisfy { (0...1).contains($0.pct) })
        #expect(overview.adherenceTrend.allSatisfy { (0...1).contains($0.adherencePct) })
        #expect(overview.rosterTotals != nil)
    }

    @Test func testWholePercentFormatting() {
        #expect(CoachFormat.wholePercent(0.94) == "94%")
        #expect(CoachFormat.wholePercent(0.087) == "9%")
        #expect(CoachFormat.wholePercent(1) == "100%")
        #expect(CoachFormat.wholePercent(0) == "0%")
    }

    @Test func testCoachRosterDecoding() throws {
        let roster = try Fixture.decode([CoachedAthleteRow].self, "coaching_roster.json")
        #expect(roster.count == 2)
        let active = try #require(roster.first { $0.isActive })
        #expect(active.displayName == "Preview Runner")
        let invited = try #require(roster.first { !$0.isActive })
        #expect(invited.status == "invited")
        #expect(invited.displayName == "Pending Invitee")
    }

    @Test func testCoachNotesDecoding() throws {
        let res = try Fixture.decode(CoachNotesResponse.self, "coaching_notes.json")
        #expect(res.notes.count == 3)
        #expect(Set(res.notes.map(\.targetType)) == ["general", "plan", "workout"])
        #expect(res.notes.allSatisfy { !$0.note.isEmpty && $0.createdAt != nil })
    }

    @Test func testMyInvitesDecoding() throws {
        let invites = try Fixture.decode([CoachingInvite].self, "coaching_my_invites.json")
        #expect(invites.count == 1)
        #expect(invites[0].displayCoachName == "Coach Kylian")
        #expect(invites[0].status == "invited")
    }

    @Test func testAthleteProfileDecoding() throws {
        let profile = try Fixture.decode(User.self, "coaching_athlete_profile.json")
        #expect(profile.email == "ios-preview@uphill.ai")
        #expect(profile.isCoach == false)
    }

    @Test func testCoachUserDecoding() throws {
        let coach = try Fixture.decode(User.self, "coaching_coach_me.json")
        #expect(coach.isCoach == true)
    }

    @Test func testAthleteActivePlanDecoding() throws {
        let res = try Fixture.decode(ActivePlanResponse.self, "coaching_athlete_active_plan.json")
        let snapshot = try #require(res.snapshot)
        #expect(snapshot.plan.raceName == "Vietnam Mountain Marathon 42K")
        #expect(snapshot.workouts.contains { $0.approvedAt == nil })
        #expect(snapshot.workouts.contains { $0.approvedAt != nil })
    }

    @Test func testAthleteDraftPlanDecoding() throws {
        let res = try Fixture.decode(DraftPlanResponse.self, "coaching_athlete_draft_plan.json")
        let snapshot = try #require(res.snapshot)
        #expect(snapshot.plan.raceName == "Dalat Ultra Trail 50K")
        #expect(snapshot.workouts.allSatisfy { $0.approvedAt == nil })
    }

    @Test func testCoachingServiceAPI() async throws {
        let rosterData = try Fixture.data("coaching_roster.json")
        let invitesData = try Fixture.data("coaching_my_invites.json")
        let notesData = try Fixture.data("coaching_notes.json")
        let planData = try Fixture.data("coaching_athlete_active_plan.json")
        let plan = try Fixture.decode(ActivePlanResponse.self, "coaching_athlete_active_plan.json")
        let workout = try #require(plan.workouts?.first { $0.approvedAt != nil })
        let workoutData = try JSONEncoder().encode(workout)

        let client = makeStubClient { request in
            let url = request.url?.absoluteString ?? ""
            if url.contains("/api/coaching/roster") { return (200, rosterData) }
            if url.contains("/api/coaching/my-invites") { return (200, invitesData) }
            if url.contains("/notes") { return (200, notesData) }
            if url.contains("/active-plan") { return (200, planData) }
            if url.contains("/approve") { return (200, workoutData) }
            return (200, Data())
        }

        let service = CoachingService(client: client)
        let roster = try await service.fetchRoster()
        #expect(roster.count == 2)

        let invites = try await service.fetchMyInvites()
        #expect(invites.first?.displayCoachName == "Coach Kylian")

        let notes = try await service.fetchNotes(athleteId: roster[0].athleteId)
        #expect(notes.count == 3)

        let snapshot = try await service.fetchAthleteActivePlan(athleteId: roster[0].athleteId)
        #expect(snapshot?.workouts.isEmpty == false)

        let approved = try await service.approveWorkout(athleteId: roster[0].athleteId, planId: plan.plan?.id ?? 0, workoutId: workout.id)
        #expect(approved.id == workout.id)
        #expect(approved.title == workout.title)
    }
}
