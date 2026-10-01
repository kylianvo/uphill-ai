import Foundation
import Testing
@testable import UphillAI

struct KeychainTokenStoreTests {
    @Test func writesReadsAndClears() {
        let store = KeychainTokenStore(service: "ai.uphill.app.tests.\(UUID().uuidString)")
        #expect(store.read() == nil)
        store.write("t1")
        #expect(store.read() == "t1")
        store.write("t2")
        #expect(store.read() == "t2")
        store.write(nil)
        #expect(store.read() == nil)
    }
}
