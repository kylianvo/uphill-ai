import Foundation
import Synchronization
@testable import UphillAI

typealias StubHandler = @Sendable (URLRequest) throws -> (Int, Data)

/// Serves canned responses. Each test registers its own handler under a unique
/// host, so tests running in parallel never see each other's handlers.
final class StubURLProtocol: URLProtocol {
    private static let handlers = Mutex<[String: StubHandler]>([:])

    static func register(_ handler: @escaping StubHandler) -> URL {
        let host = "stub-\(UUID().uuidString.lowercased()).test"
        handlers.withLock { $0[host] = handler }
        return URL(string: "https://\(host)")!
    }

    static func session() -> URLSession {
        let config = URLSessionConfiguration.ephemeral
        config.protocolClasses = [StubURLProtocol.self]
        return URLSession(configuration: config)
    }

    /// URLSession moves httpBody into a stream before it reaches a URLProtocol.
    static func bodyData(_ request: URLRequest) -> Data? {
        if let body = request.httpBody { return body }
        guard let stream = request.httpBodyStream else { return nil }
        stream.open()
        defer { stream.close() }
        var data = Data()
        var buffer = [UInt8](repeating: 0, count: 4096)
        while stream.hasBytesAvailable {
            let n = stream.read(&buffer, maxLength: buffer.count)
            if n <= 0 { break }
            data.append(buffer, count: n)
        }
        return data
    }

    override class func canInit(with request: URLRequest) -> Bool { true }
    override class func canonicalRequest(for request: URLRequest) -> URLRequest { request }

    override func startLoading() {
        let host = request.url?.host() ?? ""
        guard let handler = Self.handlers.withLock({ $0[host] }) else {
            client?.urlProtocol(self, didFailWithError: URLError(.unsupportedURL))
            return
        }
        do {
            let (status, data) = try handler(request)
            let response = HTTPURLResponse(url: request.url!, statusCode: status, httpVersion: nil, headerFields: nil)!
            client?.urlProtocol(self, didReceive: response, cacheStoragePolicy: .notAllowed)
            client?.urlProtocol(self, didLoad: data)
            client?.urlProtocolDidFinishLoading(self)
        } catch {
            client?.urlProtocol(self, didFailWithError: error)
        }
    }

    override func stopLoading() {}
}

func makeStubClient(
    token: String? = "test-token",
    onUnauthorized: @escaping @Sendable () async -> Void = {},
    handler: @escaping StubHandler
) -> APIClient {
    let base = StubURLProtocol.register(handler)
    return APIClient(
        baseURL: { base },
        tokenStore: InMemoryTokenStore(token),
        session: StubURLProtocol.session(),
        onUnauthorized: onUnauthorized
    )
}

func json(_ object: Any) -> Data {
    try! JSONSerialization.data(withJSONObject: object)
}
