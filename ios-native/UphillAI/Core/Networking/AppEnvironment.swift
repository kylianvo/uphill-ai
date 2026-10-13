import Foundation

enum AppEnvironment: String, CaseIterable, Identifiable, Sendable {
    case production, staging, local

    var id: String { rawValue }

    var baseURL: URL {
        switch self {
        case .production: return URL(string: "https://api.uphill-ai.io.vn")!
        case .staging: return URL(string: "https://staging-api.uphill-ai.io.vn")!
        case .local:
            #if DEBUG
            return Self.localURL(port: ProcessInfo.processInfo.environment["UPHILL_LOCAL_API_PORT"])
            #else
            return URL(string: "http://localhost:8000")!
            #endif
        }
    }

    static func localURL(port: String?) -> URL {
        let number = port.flatMap(Int.init).flatMap { (1...65535).contains($0) ? $0 : nil } ?? 8000
        return URL(string: "http://localhost:\(number)")!
    }

    #if DEBUG
    static func uiTestSessionToken(url: URL, environment: [String: String]) -> String? {
        guard url.scheme == "http", ["localhost", "127.0.0.1"].contains(url.host ?? ""),
              url.user == nil, url.password == nil,
              let token = environment["UITEST_SESSION_TOKEN"], !token.isEmpty else { return nil }
        return token
    }
    #endif

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
