import SwiftUI
import Testing
import UIKit
@testable import UphillAI

@MainActor
struct Phase6CoachScreenshots {
    /// Screenshots are only written when SCREENSHOT_DIR is set, so ordinary test runs leave the
    /// working tree alone. Re-render with:
    ///   TEST_RUNNER_SCREENSHOT_DIR=$PWD/docs/screenshots/phase6 ios-native/scripts/test.sh -only-testing:UphillAITests/Phase6CoachScreenshots
    private let outDir = ProcessInfo.processInfo.environment["SCREENSHOT_DIR"]

    // Every screen renders recorded backend responses (ios-native/scripts/record_fixtures.sh x coach).
    private let overview = try! Fixture.decode(CoachOverview.self, "coaching_overview.json")
    private let roster = try! Fixture.decode([CoachedAthleteRow].self, "coaching_roster.json")
    private let invites = try! Fixture.decode([CoachingInvite].self, "coaching_my_invites.json")
    private let athletePlan = try! Fixture.decode(ActivePlanResponse.self, "coaching_athlete_active_plan.json")

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
        guard let data = img.pngData() else {
            Issue.record("Could not encode \(name)")
            return
        }
        guard let outDir else { return }
        let url = URL(fileURLWithPath: "\(outDir)/\(name).png")
        do { try data.write(to: url) } catch { Issue.record("Could not write \(url.path): \(error)") }
    }

    private func makeApp() throws -> AppModel {
        let user = try Fixture.decode(User.self, "coaching_coach_me.json")
        let base = StubURLProtocol.register { _ in (200, json([:])) }
        let tokenStore = InMemoryTokenStore("tok")
        let app = AppModel(tokenStore: tokenStore, baseURL: { base }, session: StubURLProtocol.session(), cache: .inMemory())
        app.session.setUser(user)
        return app
    }

    private var athlete: CoachedAthleteRow { roster.first { $0.isActive }! }

    @Test func renderCoachDashboardOverview() throws {
        let app = try makeApp()
        let view = NavigationStack {
            CoachDashboardView(
                app: app,
                initialSection: .overview,
                initialOverview: overview,
                initialRoster: roster
            )
        }
        save(view, name: "phase6-coach-dashboard-overview")
    }

    /// The whole Overview scroll content (adherence badges, charts) in one tall frame.
    @Test func renderCoachDashboardOverviewFull() throws {
        let app = try makeApp()
        let view = NavigationStack {
            CoachDashboardView(
                app: app,
                initialSection: .overview,
                initialOverview: overview,
                initialRoster: roster
            )
        }
        save(view, name: "phase6-coach-dashboard-overview-full", size: CGSize(width: 402, height: 1780))
    }

    @Test func renderCoachDashboardRoster() throws {
        let app = try makeApp()
        let view = NavigationStack {
            CoachDashboardView(
                app: app,
                initialSection: .roster,
                initialOverview: overview,
                initialRoster: roster
            )
        }
        save(view, name: "phase6-coach-dashboard-roster")
    }

    @Test func renderCoachedAthleteProfile() throws {
        let profile = try Fixture.decode(User.self, "coaching_athlete_profile.json")
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
        let plan = try #require(athletePlan.plan)

        let view = CoachAddWorkoutSheet(
            athleteId: athlete.athleteId,
            planId: plan.id,
            initialWeek: 3,
            initialDay: "Thursday",
            service: service,
            onAdded: { _ in }
        )
        save(view, name: "phase6-coach-add-workout")
    }

    @Test func renderCoachEditWorkoutSheet() throws {
        let client = makeStubClient { _ in (200, json([:])) }
        let service = CoachingService(client: client)
        let plan = try #require(athletePlan.plan)
        // The coach-added workout still waiting for approval.
        let workout = try #require(athletePlan.workouts?.first { $0.approvedAt == nil })

        let view = CoachEditWorkoutSheet(
            athleteId: athlete.athleteId,
            planId: plan.id,
            workout: workout,
            service: service,
            onSaved: { _ in }
        )
        save(view, name: "phase6-coach-edit-workout")
    }

    @Test func renderPendingInviteBanner() throws {
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
