import SwiftUI
import Testing
import UIKit
@testable import UphillAI

@MainActor
struct Phase6CoachScreenshots {
    private let outDir = "/Users/vietvo/.codex/worktrees/ios-native-phase2b/uphill-ai/ios-native/docs/screenshots/phase6"

    private func save<V: View>(_ view: V, name: String, size: CGSize = CGSize(width: 402, height: 874), scale: CGFloat = 2.0) {
        let controller = UIHostingController(rootView: view.frame(width: size.width, height: size.height))
        controller.view.bounds = CGRect(origin: .zero, size: size)
        controller.view.backgroundColor = .systemBackground

        let window = UIWindow(frame: CGRect(origin: .zero, size: size))
        window.rootViewController = controller
        window.makeKeyAndVisible()
        controller.view.layoutIfNeeded()

        let format = UIGraphicsImageRendererFormat()
        format.scale = scale
        let renderer = UIGraphicsImageRenderer(size: size, format: format)
        let img = renderer.image { _ in
            controller.view.drawHierarchy(in: CGRect(origin: .zero, size: size), afterScreenUpdates: true)
        }
        let url = URL(fileURLWithPath: "\(outDir)/\(name).png")
        try? img.pngData()?.write(to: url)
    }

    private func makeApp(isCoach: Bool = true) throws -> AppModel {
        let userJson = """
        {
            "id": 1,
            "email": "coach@uphill.ai",
            "name": "Coach Kylian",
            "role": "coach",
            "onboarding_complete": true,
            "provider": "email",
            "has_password": true,
            "is_coach": \(isCoach)
        }
        """.data(using: .utf8)!
        let user = try JSONCoding.decoder.decode(User.self, from: userJson)
        let base = StubURLProtocol.register { _ in (200, json([:])) }
        let tokenStore = InMemoryTokenStore("tok")
        let app = AppModel(tokenStore: tokenStore, baseURL: { base }, session: StubURLProtocol.session(), cache: .inMemory())
        app.session.setUser(user)
        return app
    }

    private var sampleOverview: CoachOverview {
        CoachOverview(
            athletes: [
                CoachOverviewAthlete(
                    athleteId: 42,
                    name: "Minh Tran",
                    runnerLevel: "intermediate",
                    needsAttention: false,
                    activePlan: CoachAthleteActivePlan(
                        planId: 101,
                        raceName: "Dalat Ultra Trail 50K",
                        raceDate: "2026-11-15",
                        currentWeek: 6,
                        totalWeeks: 16
                    ),
                    adherencePct: 94.0,
                    lastCompleted: CoachLastCompletedWorkout(
                        weekNumber: 6,
                        dayOfWeek: "Sunday"
                    ),
                    missedStreak: 0
                ),
                CoachOverviewAthlete(
                    athleteId: 48,
                    name: "Linh Nguyen",
                    runnerLevel: "advanced",
                    needsAttention: false,
                    activePlan: CoachAthleteActivePlan(
                        planId: 102,
                        raceName: "UTMB CCC 100K",
                        raceDate: "2026-12-05",
                        currentWeek: 3,
                        totalWeeks: 20
                    ),
                    adherencePct: 87.0,
                    lastCompleted: CoachLastCompletedWorkout(
                        weekNumber: 3,
                        dayOfWeek: "Saturday"
                    ),
                    missedStreak: 1
                )
            ],
            actionItems: CoachActionItems(
                draftPlans: [
                    CoachDraftPlanItem(
                        planId: 105,
                        athleteId: 55,
                        athleteName: "Huy Le",
                        raceName: "Vietnam Mountain Marathon 70K"
                    )
                ],
                pendingWorkoutApprovals: [
                    CoachPendingApprovalItem(
                        workoutId: 301,
                        planId: 101,
                        athleteId: 42,
                        athleteName: "Minh Tran",
                        title: "Hill Intervals 8x3min"
                    )
                ]
            ),
            phaseAlerts: [
                CoachPhaseAlert(
                    athleteId: 42,
                    athleteName: "Minh Tran",
                    phase: "Taper",
                    starts: "2026-10-25"
                )
            ],
            workoutTypeMix: [
                WorkoutTypeMixEntry(type: "Easy", count: 28, pct: 45.0),
                WorkoutTypeMixEntry(type: "Long Run", count: 16, pct: 25.0),
                WorkoutTypeMixEntry(type: "Tempo", count: 10, pct: 15.0),
                WorkoutTypeMixEntry(type: "Interval", count: 10, pct: 15.0)
            ],
            adherenceTrend: [
                AdherenceTrendEntry(weekNumber: 1, adherencePct: 82.0),
                AdherenceTrendEntry(weekNumber: 2, adherencePct: 86.5),
                AdherenceTrendEntry(weekNumber: 3, adherencePct: 91.0),
                AdherenceTrendEntry(weekNumber: 4, adherencePct: 88.5)
            ],
            missedByDay: [
                MissedByDayEntry(dayOfWeek: "Mon", count: 1),
                MissedByDayEntry(dayOfWeek: "Tue", count: 0),
                MissedByDayEntry(dayOfWeek: "Wed", count: 2),
                MissedByDayEntry(dayOfWeek: "Thu", count: 0),
                MissedByDayEntry(dayOfWeek: "Fri", count: 1),
                MissedByDayEntry(dayOfWeek: "Sat", count: 0),
                MissedByDayEntry(dayOfWeek: "Sun", count: 0)
            ],
            races: [
                RaceBreakdownEntry(
                    raceName: "Dalat Ultra Trail 50K",
                    raceDate: "2026-11-15",
                    count: 6,
                    athletes: [RaceBreakdownAthlete(athleteId: 42, name: "Minh Tran")]
                ),
                RaceBreakdownEntry(
                    raceName: "UTMB CCC 100K",
                    raceDate: "2026-12-05",
                    count: 3,
                    athletes: [RaceBreakdownAthlete(athleteId: 48, name: "Linh Nguyen")]
                ),
                RaceBreakdownEntry(
                    raceName: "Vietnam Mountain Marathon",
                    raceDate: "2026-10-20",
                    count: 3,
                    athletes: [RaceBreakdownAthlete(athleteId: 55, name: "Huy Le")]
                )
            ],
            rosterTotals: CoachRosterTotals(
                distanceKm: 420.5,
                durationHours: 38.5,
                elevationGainM: 12500,
                workoutCount: 48
            ),
            athletesWithoutRace: 0
        )
    }

    private var sampleRoster: [CoachedAthleteRow] {
        [
            CoachedAthleteRow(
                id: 1,
                athleteId: 42,
                athleteName: "Minh Tran",
                athleteEmail: "minh@example.com",
                status: "active",
                invitedAt: "2026-09-01T10:00:00Z",
                respondedAt: "2026-09-02T11:00:00Z"
            ),
            CoachedAthleteRow(
                id: 2,
                athleteId: 48,
                athleteName: "Linh Nguyen",
                athleteEmail: "linh@example.com",
                status: "active",
                invitedAt: "2026-09-10T10:00:00Z",
                respondedAt: "2026-09-11T12:00:00Z"
            ),
            CoachedAthleteRow(
                id: 3,
                athleteId: 99,
                athleteName: nil,
                athleteEmail: "hoang.runner@test.com",
                status: "invited",
                invitedAt: "2026-10-05T12:00:00Z",
                respondedAt: nil
            )
        ]
    }

    @Test func renderCoachDashboardOverview() throws {
        let app = try makeApp(isCoach: true)
        let view = NavigationStack {
            CoachDashboardView(
                app: app,
                initialSection: .overview,
                initialOverview: sampleOverview,
                initialRoster: sampleRoster
            )
        }
        save(view, name: "phase6-coach-dashboard-overview")
    }

    @Test func renderCoachDashboardRoster() throws {
        let app = try makeApp(isCoach: true)
        let view = NavigationStack {
            CoachDashboardView(
                app: app,
                initialSection: .roster,
                initialOverview: sampleOverview,
                initialRoster: sampleRoster
            )
        }
        save(view, name: "phase6-coach-dashboard-roster")
    }

    @Test func renderCoachedAthleteProfile() throws {
        let athlete = sampleRoster[0]
        let userJson = """
        {
            "id": 42,
            "email": "minh@example.com",
            "name": "Minh Tran",
            "role": "user",
            "onboarding_complete": true,
            "provider": "email",
            "has_password": true,
            "max_hr": 188,
            "ant_hr": 172,
            "aet_hr": 151,
            "current_weekly_km": 65.0,
            "preferred_run_days": "[\\"Tuesday\\", \\"Wednesday\\", \\"Thursday\\", \\"Saturday\\", \\"Sunday\\"]",
            "long_run_day": "Saturday",
            "injury_history": "Mild Achilles tendon tightness after prolonged technical descents. Manages with eccentric calf drops.",
            "athlete_notes": "Targeting sub-6:30 at Dalat 50K. Wants to improve uphill pacing and hydration strategy.",
            "is_coach": false
        }
        """.data(using: .utf8)!
        let profile = try JSONCoding.decoder.decode(User.self, from: userJson)

        let client = makeStubClient { _ in (200, json([:])) }
        let service = CoachingService(client: client)

        let view = NavigationStack {
            CoachedAthleteProfileView(
                athlete: athlete,
                profile: profile,
                service: service
            )
        }
        save(view, name: "phase6-coached-athlete-profile")
    }

    @Test func renderCoachedAthleteBanner() throws {
        let athlete = sampleRoster[0]
        let view = VStack(spacing: 16) {
            CoachedAthleteBanner(athlete: athlete) {}
            Spacer()
        }
        .padding(16)
        .background(UH.Palette.surface)
        save(view, name: "phase6-coached-athlete-banner", size: CGSize(width: 402, height: 200))
    }

    @Test func renderCoachAddWorkoutSheet() throws {
        let client = makeStubClient { _ in (200, json([:])) }
        let service = CoachingService(client: client)

        let view = CoachAddWorkoutSheet(
            athleteId: 42,
            planId: 101,
            initialWeek: 4,
            initialDay: "Thursday",
            service: service,
            onAdded: { _ in }
        )
        save(view, name: "phase6-coach-add-workout")
    }

    @Test func renderCoachEditWorkoutSheet() throws {
        let client = makeStubClient { _ in (200, json([:])) }
        let service = CoachingService(client: client)

        let workout = TestData.workout([
            "id": 301,
            "week_number": 4,
            "day_of_week": "Thursday",
            "title": "Hill Intervals 8x3min",
            "type": "Interval",
            "duration_minutes": 65,
            "distance_km": 11.5,
            "target_zone": "Zone 4",
            "description": "Warm-up 15 min Zone 2. 8 reps of 3 min uphill surge at 10-12% grade in Zone 4. Jog back down easy for recovery. Cool down 10 min.",
            "phase": "Build"
        ])

        let view = CoachEditWorkoutSheet(
            athleteId: 42,
            planId: 101,
            workout: workout,
            service: service,
            onSaved: { _ in }
        )
        save(view, name: "phase6-coach-edit-workout")
    }

    @Test func renderPendingInviteBanner() throws {
        let invites = [
            CoachingInvite(
                id: 1,
                coachId: 7,
                coachName: "Coach Kylian",
                coachEmail: "kylian@uphill.ai",
                status: "pending",
                invitedAt: "2026-10-05T09:00:00Z"
            )
        ]

        let view = VStack(spacing: 16) {
            PendingInviteBanner(
                invites: invites,
                onAccept: { _ in },
                onDecline: { _ in }
            )
            Spacer()
        }
        .padding(.vertical, 24)
        .background(UH.Palette.surface)
        save(view, name: "phase6-pending-invite-banner", size: CGSize(width: 402, height: 260))
    }
}
