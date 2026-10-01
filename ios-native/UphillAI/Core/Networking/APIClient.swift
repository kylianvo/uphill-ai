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
            let error = APIError.from(status: status, data: data)
            if error == .unauthorized, endpoint.requiresAuth {
                await onUnauthorized()
            }
            throw error
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
