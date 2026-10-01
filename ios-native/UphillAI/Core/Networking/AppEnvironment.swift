import Foundation

enum AppEnvironment: String, CaseIterable, Identifiable, Sendable {
    case production, staging, local

    var id: String { rawValue }

    var baseURL: URL {
        switch self {
        case .production: URL(string: "https://api.uphill-ai.io.vn")!
        case .staging: URL(string: "https://staging-api.uphill-ai.io.vn")!
        case .local: URL(string: "http://localhost:8000")!
        }
    }

    static let defaultsKey = "UPHILL_ENVIRONMENT"

    /// Release builds always talk to production. Debug builds use the
    /// developer-menu choice, defaulting to the local Docker backend.
    static func current(defaults: UserDefaults = .standard) -> AppEnvironment {
        #if DEBUG
        return defaults.string(forKey: defaultsKey).flatMap(AppEnvironment.init(rawValue:)) ?? .local
        #else
        return .production
        #endif
    }
}
