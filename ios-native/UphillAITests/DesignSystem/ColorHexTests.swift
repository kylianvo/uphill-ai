import SwiftUI
import Testing
@testable import UphillAI

struct ColorHexTests {
    @Test func parsesHashedHex() throws {
        let c = try #require(Color.rgbComponents("#19ce8b"))
        #expect(abs(c.r - 25.0 / 255) < 0.0001)
        #expect(abs(c.g - 206.0 / 255) < 0.0001)
        #expect(abs(c.b - 139.0 / 255) < 0.0001)
    }

    @Test func parsesBareHex() {
        #expect(Color.rgbComponents("ffffff") != nil)
    }

    @Test(arguments: ["", "#fff", "#19ce8", "#19ce8bz", "zzzzzz"])
    func rejectsMalformed(_ input: String) {
        #expect(Color.rgbComponents(input) == nil)
    }
}
