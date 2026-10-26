import SwiftUI
import Testing
import UIKit
@testable import UphillAI

/// Connected accounts with Garmin on, not connected and connected. Written only when
/// SCREENSHOT_DIR is set; SCREENSHOT_VI renders Vietnamese.
@MainActor
struct GarminScreenshots {
    private let outDir = ProcessInfo.processInfo.environment["SCREENSHOT_DIR"]

    private func save<V: View>(_ view: V, name: String) {
        guard let outDir else { return }
        let suffix = ProcessInfo.processInfo.environment["SCREENSHOT_VI"] != nil ? "-vi" : ""
        let size = CGSize(width: 402, height: 620)
        let controller = UIHostingController(rootView: view.padding().frame(width: size.width, height: size.height, alignment: .top))
        let window = UIWindow(frame: CGRect(origin: .zero, size: size))
        window.rootViewController = controller
        window.makeKeyAndVisible()
        controller.view.layoutIfNeeded()
        RunLoop.main.run(until: Date().addingTimeInterval(0.3))
        let format = UIGraphicsImageRendererFormat()
        format.scale = 2
        let img = UIGraphicsImageRenderer(size: size, format: format).image { _ in
            controller.view.drawHierarchy(in: CGRect(origin: .zero, size: size), afterScreenUpdates: true)
        }
        try? img.pngData()?.write(to: URL(fileURLWithPath: "\(outDir)/garmin-\(name)\(suffix).png"))
    }

    @Test func renderGarminRow() {
        if ProcessInfo.processInfo.environment["SCREENSHOT_VI"] != nil {
            UserDefaults.standard.set("vi", forKey: AppLanguage.storageKey)
        }
        defer { UserDefaults.standard.removeObject(forKey: AppLanguage.storageKey) }
        let states: [(String, GarminConnectionStatus)] = [
            ("not-connected", GarminConnectionStatus(enabled: true, connected: false, lastSyncAt: nil)),
            ("connected", GarminConnectionStatus(enabled: true, connected: true, lastSyncAt: "2026-10-24T05:00:00Z")),
        ]
        save(
            VStack(alignment: .leading, spacing: 6) {
                Text("YOUR PLAN ON GARMIN")
                    .font(.system(size: 10, weight: .bold, design: .monospaced))
                    .foregroundStyle(UH.Palette.muted)
                CorosPushButton(service: NoCalls(),
                                initialStatus: CorosPushStatus(connected: true, lastPushedAt: "2026-10-26T04:00:00Z", outOfDate: true),
                                provider: .garmin)
            }
            .environment(\.locale, AppLanguage.current.locale),
            name: "push"
        )
        for (name, garmin) in states {
            let status = DeviceConnectionStatus(coros: CorosConnectionStatus(connected: false), garmin: garmin)
            save(
                ConnectedAccountsView(service: NoCalls(), initialStatus: status)
                    .environment(\.locale, AppLanguage.current.locale),
                name: name
            )
        }
    }
}

@MainActor
struct GarminCourseScreenshots {
    @Test func renderSendCourseToGarmin() async throws {
        guard let outDir = ProcessInfo.processInfo.environment["SCREENSHOT_DIR"] else { return }
        let points = (0..<200).map { i in
            "<trkpt lat=\"\(22.0 + Double(i) * 0.0009)\" lon=\"103.8\"><ele>\(1000 + i * 5)</ele></trkpt>"
        }.joined()
        let data = Data("<gpx version=\"1.1\"><trk><trkseg>\(points)</trkseg></trk></gpx>".utf8)
        let gpx = try GpxCourseParser.parse(data: data, fileName: "vietnam-trail-50k.gpx")
        let view = ScrollView {
            PaceStrategySheet(service: PacingService(client: makeStubClient { _ in (200, json([:])) }),
                              initialGpxResult: gpx, initialGpxData: data, deviceService: GarminConnected())
        }
        let size = CGSize(width: 402, height: 900)
        let controller = UIHostingController(rootView: view.frame(width: size.width, height: size.height))
        let window = UIWindow(frame: CGRect(origin: .zero, size: size))
        window.rootViewController = controller
        window.makeKeyAndVisible()
        controller.view.layoutIfNeeded()
        try await Task.sleep(for: .milliseconds(600))
        let img = UIGraphicsImageRenderer(size: size).image { _ in
            controller.view.drawHierarchy(in: CGRect(origin: .zero, size: size), afterScreenUpdates: true)
        }
        try img.pngData()?.write(to: URL(fileURLWithPath: "\(outDir)/garmin-pace-course.png"))
    }
}

private struct GarminConnected: DeviceConnectionServicing {
    struct Unused: Error {}
    func fetchStatus() async throws -> DeviceConnectionStatus {
        DeviceConnectionStatus(garmin: GarminConnectionStatus(enabled: true, connected: true, lastSyncAt: nil))
    }
    func connectCorosURL() async throws -> URL { throw Unused() }
    func completeCoros(state: String, token: String) async throws -> Bool { false }
    func syncNow(days: Int) async throws -> DeviceSyncResult { throw Unused() }
    func syncFitness() async throws -> FitnessSyncResult { throw Unused() }
    func disconnectCoros() async throws {}
    func fetchPushStatus(clientToday: String) async throws -> CorosPushStatus { throw Unused() }
    func pushToCoros(clientToday: String, lang: String) async throws -> CorosPushOutcome { throw Unused() }
}

/// The view gets its status up front, so no call reaches the service.
private struct NoCalls: DeviceConnectionServicing {
    struct Unused: Error {}
    func fetchStatus() async throws -> DeviceConnectionStatus { throw Unused() }
    func connectCorosURL() async throws -> URL { throw Unused() }
    func completeCoros(state: String, token: String) async throws -> Bool { false }
    func syncNow(days: Int) async throws -> DeviceSyncResult { throw Unused() }
    func syncFitness() async throws -> FitnessSyncResult { throw Unused() }
    func disconnectCoros() async throws {}
    func fetchPushStatus(clientToday: String) async throws -> CorosPushStatus { throw Unused() }
    func pushToCoros(clientToday: String, lang: String) async throws -> CorosPushOutcome { throw Unused() }
}
