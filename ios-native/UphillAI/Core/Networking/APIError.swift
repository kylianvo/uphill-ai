import Foundation

enum APIError: Error, Equatable, Sendable {
    case unauthorized
    /// `message` is FastAPI's string `detail`; `code` is `detail.code` on guard errors (e.g. calendar moves).
    case http(status: Int, message: String?, code: String?)
    case scheduleGuard(status: Int, code: String, params: [String: String])
    case decoding(String)
    case transport(String)

    static func from(status: Int, data: Data, treating401AsSessionExpiry: Bool = true) -> APIError {
        if status == 401, treating401AsSessionExpiry { return .unauthorized }
        let object = (try? JSONSerialization.jsonObject(with: data)) as? [String: Any]
        switch object?["detail"] {
        case let message as String:
            return .http(status: status, message: message, code: nil)
        case let detail as [String: Any]:
            if status == 422, let code = detail["code"] as? String {
                let params = (detail["params"] as? [String: Any] ?? [:]).mapValues { $0 is NSNull ? "" : String(describing: $0) }
                return .scheduleGuard(status: status, code: code, params: params)
            }
            return .http(status: status, message: detail["message"] as? String, code: detail["code"] as? String)
        default:
            return .http(status: status, message: nil, code: nil)
        }
    }

    var userMessage: String {
        switch self {
        case .unauthorized: L("Your session has expired. Please sign in again.")
        case .http(_, let message?, _): message
        case .http(let status, nil, _): L("Something went wrong (%lld). Please try again.", status)
        case .scheduleGuard(_, let code, let params): ScheduleMessages.guardText(code: code, params: params)
        case .decoding: L("Unexpected response from the server.")
        case .transport: L("Can't reach Uphill. Check your connection and try again.")
        }
    }
}
