import Foundation
import Testing
@testable import UphillAI

@MainActor
struct OfflineCacheTests {
    @Test func roundTripsAPlanSnapshot() throws {
        let cache = OfflineCache.inMemory()
        let snapshot = try #require(try Fixture.decode(ActivePlanResponse.self, "active_plan.json").snapshot)
        let saved = Date(timeIntervalSince1970: 1_000)
        cache.save(snapshot, as: .plan, now: saved)
        let loaded = try #require(cache.load(PlanSnapshot.self, .plan))
        #expect(loaded.value == snapshot)
        #expect(loaded.savedAt == saved)
    }

    @Test func saveOverwrites() throws {
        let cache = OfflineCache.inMemory()
        let user = try Fixture.decode(User.self, "auth_me.json")
        cache.save(user, as: .user)
        cache.save(user, as: .user)
        #expect(cache.load(User.self, .user)?.value == user)
    }

    @Test func clearAllRemovesEverything() throws {
        let cache = OfflineCache.inMemory()
        cache.save(try Fixture.decode(User.self, "auth_me.json"), as: .user)
        cache.clearAll()
        #expect(cache.load(User.self, .user) == nil)
    }
}
