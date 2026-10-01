import Foundation
import SwiftData

enum CacheKey: String {
    case user, plan
}

struct Cached<Value> {
    let value: Value
    let savedAt: Date
}

@Model
final class CacheEntry {
    @Attribute(.unique) var key: String
    var payload: Data
    var savedAt: Date

    init(key: String, payload: Data, savedAt: Date) {
        self.key = key
        self.payload = payload
        self.savedAt = savedAt
    }
}

/// Last-known user and plan, for read-only offline viewing. One signed-in user
/// per device, so entries are keyed by kind only; sign-out clears everything.
@MainActor
final class OfflineCache {
    private let context: ModelContext

    private init(container: ModelContainer) {
        context = ModelContext(container)
    }

    static func onDisk() -> OfflineCache {
        let container = try! ModelContainer(for: CacheEntry.self)
        return OfflineCache(container: container)
    }

    static func inMemory() -> OfflineCache {
        let container = try! ModelContainer(for: CacheEntry.self, configurations: ModelConfiguration(isStoredInMemoryOnly: true))
        return OfflineCache(container: container)
    }

    func save<T: Encodable>(_ value: T, as key: CacheKey, now: Date = .now) {
        guard let payload = try? JSONCoding.encoder.encode(value) else { return }
        if let entry = entry(key) {
            entry.payload = payload
            entry.savedAt = now
        } else {
            context.insert(CacheEntry(key: key.rawValue, payload: payload, savedAt: now))
        }
        try? context.save()
    }

    func load<T: Decodable>(_ type: T.Type, _ key: CacheKey) -> Cached<T>? {
        guard let entry = entry(key),
              let value = try? JSONCoding.decoder.decode(T.self, from: entry.payload) else { return nil }
        return Cached(value: value, savedAt: entry.savedAt)
    }

    func remove(_ key: CacheKey) {
        if let entry = entry(key) { context.delete(entry) }
        try? context.save()
    }

    func clearAll() {
        try? context.delete(model: CacheEntry.self)
        try? context.save()
    }

    private func entry(_ key: CacheKey) -> CacheEntry? {
        let raw = key.rawValue
        var descriptor = FetchDescriptor<CacheEntry>(predicate: #Predicate { $0.key == raw })
        descriptor.fetchLimit = 1
        return try? context.fetch(descriptor).first
    }
}
