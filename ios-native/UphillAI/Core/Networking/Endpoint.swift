import Foundation

enum HTTPMethod: String, Sendable {
    case get = "GET", post = "POST", put = "PUT", patch = "PATCH", delete = "DELETE"
}

struct Endpoint<Response: Decodable & Sendable>: Sendable {
    var method: HTTPMethod
    var path: String
    var query: [URLQueryItem] = []
    var body: Data?
    var requiresAuth = true

    static func delete(_ path: String, query: [URLQueryItem] = [], requiresAuth: Bool = true) -> Endpoint {
        Endpoint(method: .delete, path: path, query: query, requiresAuth: requiresAuth)
    }

    static func get(_ path: String, query: [URLQueryItem] = [], requiresAuth: Bool = true) -> Endpoint {
        Endpoint(method: .get, path: path, query: query, requiresAuth: requiresAuth)
    }

    static func send(_ method: HTTPMethod, _ path: String, body: some Encodable, requiresAuth: Bool = true) throws -> Endpoint {
        Endpoint(method: method, path: path, body: try JSONCoding.encoder.encode(body), requiresAuth: requiresAuth)
    }
}

/// For endpoints whose response body we don't read.
struct EmptyResponse: Decodable, Sendable {}
