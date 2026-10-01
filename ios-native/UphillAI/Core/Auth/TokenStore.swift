import Foundation
import Synchronization

/// Where the backend session token lives. Keychain in the app, memory in tests.
protocol TokenStore: Sendable {
    func read() -> String?
    func write(_ token: String?)
}

final class InMemoryTokenStore: TokenStore {
    private let token: Mutex<String?>

    init(_ initial: String? = nil) {
        token = Mutex(initial)
    }

    func read() -> String? { token.withLock { $0 } }
    func write(_ newValue: String?) { token.withLock { $0 = newValue } }
}
