import Foundation

final class APIClient: Sendable {
    private let baseURL: @Sendable () -> URL
    private let tokenStore: any TokenStore
    private let session: URLSession
    private let onUnauthorized: @Sendable () async -> Void

    init(
        baseURL: @escaping @Sendable () -> URL,
        tokenStore: any TokenStore,
        session: URLSession = .shared,
        onUnauthorized: @escaping @Sendable () async -> Void = {}
    ) {
        self.baseURL = baseURL
        self.tokenStore = tokenStore
        self.session = session
        self.onUnauthorized = onUnauthorized
    }


    func stream<R>(_ endpoint: Endpoint<R>) async throws -> (URLSession.AsyncBytes, HTTPURLResponse) {
        let request = makeRequest(endpoint)
        let bytes: URLSession.AsyncBytes
        let response: URLResponse
        do {
            (bytes, response) = try await session.bytes(for: request)
        } catch {
            throw APIError.transport(error.localizedDescription)
        }
        guard let http = response as? HTTPURLResponse else {
            throw APIError.transport("Expected HTTPURLResponse")
        }
        let status = http.statusCode
        guard (200..<300).contains(status) else {
            if status == 401, endpoint.requiresAuth {
                await onUnauthorized()
                throw APIError.unauthorized
            }
            var errData = Data()
            for try await byte in bytes {
                errData.append(byte)
                if errData.count > 4096 { break }
            }
            throw APIError.from(status: status, data: errData, treating401AsSessionExpiry: endpoint.requiresAuth)
        }
        return (bytes, http)
    }

    func send<R>(_ endpoint: Endpoint<R>) async throws -> R {
        let request = makeRequest(endpoint)
        let data: Data
        let response: URLResponse
        do {
            (data, response) = try await session.data(for: request)
        } catch {
            throw APIError.transport(error.localizedDescription)
        }
        let status = (response as? HTTPURLResponse)?.statusCode ?? 0
        guard (200..<300).contains(status) else {
            // A 401 from an endpoint that sends no token (login, register) is a credential
            // failure with the server's own message, not an expired session.
            if status == 401, endpoint.requiresAuth {
                await onUnauthorized()
                throw APIError.unauthorized
            }
            throw APIError.from(status: status, data: data, treating401AsSessionExpiry: endpoint.requiresAuth)
        }
        do {
            return try JSONCoding.decoder.decode(R.self, from: data)
        } catch {
            throw APIError.decoding(String(describing: error))
        }
    }

    private func makeRequest<R>(_ endpoint: Endpoint<R>) -> URLRequest {
        var components = URLComponents(url: baseURL().appending(path: endpoint.path), resolvingAgainstBaseURL: false)!
        if !endpoint.query.isEmpty { components.queryItems = endpoint.query }
        var request = URLRequest(url: components.url!, timeoutInterval: 30)
        request.httpMethod = endpoint.method.rawValue
        request.setValue("application/json", forHTTPHeaderField: "Accept")
        if let body = endpoint.body {
            request.httpBody = body
            request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        }
        if endpoint.requiresAuth, let token = tokenStore.read() {
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }
        return request
    }
}
