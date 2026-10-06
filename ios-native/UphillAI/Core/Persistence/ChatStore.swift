import Foundation

protocol ChatStore: Sendable {
    func loadMessages(for planId: Int) -> [ChatMessage]
    func saveMessages(_ messages: [ChatMessage], for planId: Int)
    func clearMessages(for planId: Int)
}

final class UserDefaultsChatStore: ChatStore, @unchecked Sendable {
    private let defaults: UserDefaults
    private let keyPrefix: String

    init(defaults: UserDefaults = .standard, keyPrefix: String = "coach_chat_messages_") {
        self.defaults = defaults
        self.keyPrefix = keyPrefix
    }

    func loadMessages(for planId: Int) -> [ChatMessage] {
        guard let data = defaults.data(forKey: key(for: planId)) else { return [] }
        return (try? JSONCoding.decoder.decode([ChatMessage].self, from: data)) ?? []
    }

    func saveMessages(_ messages: [ChatMessage], for planId: Int) {
        let capped = Array(messages.suffix(50))
        guard let data = try? JSONCoding.encoder.encode(capped) else { return }
        defaults.set(data, forKey: key(for: planId))
    }

    func clearMessages(for planId: Int) {
        defaults.removeObject(forKey: key(for: planId))
    }

    private func key(for planId: Int) -> String {
        "\(keyPrefix)\(planId)"
    }
}
