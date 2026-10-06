import Foundation
import Testing
@testable import UphillAI

struct SmokeTests {
    @Test func hostAppHasProductionBundleID() {
        #expect(Bundle.main.bundleIdentifier == "uphill.ai.app")
    }
}
