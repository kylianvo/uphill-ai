import Foundation
import Testing
@testable import UphillAI

struct LocalAPIURLTests {
    @Test func previewSessionOnlyAcceptedForLocalHTTP() {
        let environment = ["UITEST_SESSION_TOKEN": "local-test-token"]
        #expect(AppEnvironment.uiTestSessionToken(url: URL(string: "http://localhost:8014")!, environment: environment) == "local-test-token")
        #expect(AppEnvironment.uiTestSessionToken(url: URL(string: "http://127.0.0.1:8014")!, environment: environment) == "local-test-token")
        #expect(AppEnvironment.uiTestSessionToken(url: AppEnvironment.production.baseURL, environment: environment) == nil)
        #expect(AppEnvironment.uiTestSessionToken(url: AppEnvironment.staging.baseURL, environment: environment) == nil)
        #expect(AppEnvironment.uiTestSessionToken(url: URL(string: "http://localhost@example.org")!, environment: environment) == nil)
        #expect(AppEnvironment.uiTestSessionToken(url: URL(string: "http://localhost:8014")!, environment: [:]) == nil)
    }
    @Test func alternateLocalPortDoesNotChangeProduction() {
        #expect(AppEnvironment.localURL(port: "8014").absoluteString == "http://localhost:8014")
        #expect(AppEnvironment.localURL(port: "65536").absoluteString == "http://localhost:8000")
        #expect(AppEnvironment.localURL(port: nil).absoluteString == "http://localhost:8000")
        #expect(AppEnvironment.production.baseURL.absoluteString == "https://api.uphill-ai.io.vn")
    }
}
