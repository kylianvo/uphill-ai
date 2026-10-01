import Foundation

enum APIError: Error, Equatable, Sendable {
    case unauthorized
    /// `message` is FastAPI's string `detail`; `code` is `detail.code` on guard errors (e.g. calendar moves).
    case http(status: Int, message: String?, code: String?)
    case decoding(String)
    case transport(String)

    static func from(status: Int, data: Data) -> APIError {
        if status == 401 { return .unauthorized }
        let object = (try? JSONSerialization.jsonObject(with: data)) as? [String: Any]
        switch object?["detail"] {
        case let message as String:
            return .http(status: status, message: message, code: nil)
        case let detail as [String: Any]:
            return .http(status: status, message: detail["message"] as? String, code: detail["code"] as? String)
        default:
            return .http(status: status, message: nil, code: nil)
        }
    }

    var userMessage: String {
        switch self {
        case .unauthorized: "Your session has expired. Please sign in again."
        case .http(_, let message?, _): message
        case .http(let status, nil, _): "Something went wrong (\(status)). Please try again."
        case .decoding: "Unexpected response from the server."
        case .transport: "Can't reach Uphill. Check your connection and try again."
        }
    }
}
