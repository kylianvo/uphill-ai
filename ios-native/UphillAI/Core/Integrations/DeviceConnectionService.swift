import AuthenticationServices
import Foundation
import UIKit

public protocol DeviceConnectionServicing: Sendable {
    func fetchStatus() async throws -> DeviceConnectionStatus
    func connectCorosURL() async throws -> URL
    func completeCoros(state: String, token: String) async throws -> Bool
    func syncNow(days: Int) async throws -> DeviceSyncResult
    func syncFitness() async throws -> FitnessSyncResult
    func disconnectCoros() async throws
    func fetchPushStatus(clientToday: String) async throws -> CorosPushStatus
    func pushToCoros(clientToday: String, lang: String) async throws -> CorosPushOutcome
}

final class DeviceConnectionService: DeviceConnectionServicing {
    private let client: APIClient

    init(client: APIClient) {
        self.client = client
    }

    struct ConnectResponse: Decodable, Sendable {
        let authorizeUrl: String
    }

    private struct CompleteBody: Encodable {
        let state: String
        let token: String
    }

    struct CompleteResponse: Decodable, Sendable {
        let connected: Bool
    }

    private struct PushBody: Encodable {
        let client_today: String
        let lang: String
    }

    struct PushApiResponse: Decodable, Sendable {
        let status: String
        let summary: CorosPushSummary?
        let lastPushedAt: String?
    }

    private struct EmptyResponse: Decodable {}

    func fetchStatus() async throws -> DeviceConnectionStatus {
        try await client.send(.get("/api/integrations/status"))
    }

    func connectCorosURL() async throws -> URL {
        let resp: ConnectResponse = try await client.send(
            .get("/api/integrations/coros/connect", query: [URLQueryItem(name: "platform", value: "native")])
        )
        guard let url = URL(string: resp.authorizeUrl) else {
            throw APIError.decoding("Invalid authorization URL from COROS")
        }
        return url
    }

    /// The completion token is single-use, so this posts exactly once.
    func completeCoros(state: String, token: String) async throws -> Bool {
        let resp: CompleteResponse = try await client.send(
            .send(.post, "/api/integrations/coros/complete", body: CompleteBody(state: state, token: token))
        )
        return resp.connected
    }

    func syncNow(days: Int = 30) async throws -> DeviceSyncResult {
        let result: DeviceSyncResult = try await client.send(
            .post("/api/integrations/coros/sync", query: [URLQueryItem(name: "days", value: "\(days)")])
        )
        // Sync only stores activities; matching links them to planned workouts.
        let _: EmptyResponse = try await client.send(.post("/api/integrations/matching/run", query: [
            URLQueryItem(name: "days", value: "\(days)"),
            URLQueryItem(name: "tz_offset_minutes", value: "\(TimeZone.current.secondsFromGMT() / 60)"),
        ]))
        return result
    }

    func syncFitness() async throws -> FitnessSyncResult {
        try await client.send(.post("/api/integrations/coros/sync-fitness"))
    }

    func disconnectCoros() async throws {
        let _: EmptyResponse = try await client.send(.delete("/api/integrations/coros"))
    }

    func fetchPushStatus(clientToday: String) async throws -> CorosPushStatus {
        try await client.send(
            .get("/api/integrations/coros/push-status", query: [URLQueryItem(name: "client_today", value: clientToday)])
        )
    }

    /// A refusal the backend explains with a `detail.code` comes back as an
    /// unsuccessful outcome; anything else (network, 500) throws.
    func pushToCoros(clientToday: String, lang: String = AppLanguage.code) async throws -> CorosPushOutcome {
        do {
            let resp: PushApiResponse = try await client.send(
                .send(.post, "/api/integrations/coros/push", body: PushBody(client_today: clientToday, lang: lang))
            )
            return CorosPushOutcome(
                isSuccess: resp.status == "sent" || resp.status == "partial",
                status: resp.status,
                summary: resp.summary,
                lastPushedAt: resp.lastPushedAt
            )
        } catch let APIError.http(_, _, code?), let APIError.scheduleGuard(_, code, _) {
            return CorosPushOutcome(
                isSuccess: false,
                status: "error",
                errorCode: code,
                errorMessage: Self.pushErrorMessage(code)
            )
        }
    }

    /// English copy from the web's corosPush.ts, without its {placeholders}.
    static func pushErrorMessage(_ code: String) -> String {
        switch code {
        case "COROS_not_connected": "COROS isn't connected. Reconnect it in your profile."
        case "NOTHING_to_push": "Nothing to send: there are no upcoming runs in your plan."
        case "RACE_too_far": "COROS plans cover up to 16 weeks. Send to COROS opens closer to your race."
        case "RACE_too_close": "COROS plans must be at least 4 weeks long."
        case "PUSH_in_progress": "A send is already running. Try again in a moment."
        case "PUSH_limit": "You've reached today's limit for sending to COROS. Try again tomorrow."
        case "COROS_rejected": "COROS didn't accept the plan. Nothing changed on your watch."
        default: "Couldn't reach COROS. Nothing changed. Try again shortly."
        }
    }
}

// MARK: - COROS Native OAuth Coordinator

/// Manages native OAuth 2.0 PKCE authorization flow with COROS using ASWebAuthenticationSession.
/// Conforms to RFC 6749 and Uphill AI one-time completion token contract.
@MainActor
public final class CorosOAuthCoordinator: NSObject, ASWebAuthenticationPresentationContextProviding, Sendable {
    public static let shared = CorosOAuthCoordinator()

    public func presentationAnchor(for session: ASWebAuthenticationSession) -> ASPresentationAnchor {
        let scenes = UIApplication.shared.connectedScenes
        let activeScene = scenes.first(where: { $0.activationState == .foregroundActive }) as? UIWindowScene
        let windowScene = activeScene ?? (scenes.first as? UIWindowScene)
        if let window = windowScene?.windows.first(where: { $0.isKeyWindow }) ?? windowScene?.windows.first {
            return window
        }
        return ASPresentationAnchor()
    }

    public enum AuthResult: Equatable, Sendable {
        case success
        case cancelled
        case failed(String)
    }

    /// Performs the complete in-app OAuth authorization flow:
    /// 1. Requests the PKCE authorize URL from Uphill backend (?platform=native)
    /// 2. Opens ASWebAuthenticationSession with callbackURLScheme "uphillai"
    /// 3. Intercepts uphillai://coros/callback?state=...&token=...
    /// 4. Validates state matches the request state
    /// 5. Posts state and token to /api/integrations/coros/complete
    public func connect(via service: any DeviceConnectionServicing) async -> AuthResult {
        do {
            let authURL = try await service.connectCorosURL()
            let expectedState = URLComponents(url: authURL, resolvingAgainstBaseURL: false)?
                .queryItems?.first(where: { $0.name == "state" })?.value

            let callbackURL: URL
            do {
                callbackURL = try await authenticate(url: authURL, callbackScheme: "uphillai")
            } catch let error as ASWebAuthenticationSessionError where error.code == .canceledLogin {
                return .cancelled
            } catch {
                return .failed(error.localizedDescription)
            }

            guard let params = Self.parseCallbackURL(callbackURL) else {
                return .failed("Invalid callback response from COROS.")
            }

            if params.isError {
                return .failed("COROS authorization was declined or cancelled.")
            }

            guard let state = params.state, let token = params.token else {
                return .failed("Missing authorization tokens from COROS.")
            }

            if let expected = expectedState, state != expected {
                return .failed("Authorization security check failed (state mismatch).")
            }

            let completed = try await service.completeCoros(state: state, token: token)
            return completed ? .success : .failed("Could not complete COROS connection.")
        } catch {
            return .failed(error.localizedDescription)
        }
    }

    private func authenticate(url: URL, callbackScheme: String) async throws -> URL {
        try await withCheckedThrowingContinuation { continuation in
            let session = ASWebAuthenticationSession(
                url: url,
                callbackURLScheme: callbackScheme
            ) { callbackURL, error in
                if let error = error {
                    continuation.resume(throwing: error)
                } else if let callbackURL = callbackURL {
                    continuation.resume(returning: callbackURL)
                } else {
                    continuation.resume(throwing: URLError(.badServerResponse))
                }
            }
            session.presentationContextProvider = self
            session.prefersEphemeralWebBrowserSession = false
            session.start()
        }
    }

    public struct CallbackParams: Equatable, Sendable {
        public let state: String?
        public let token: String?
        public let isError: Bool
    }

    public nonisolated static func parseCallbackURL(_ url: URL) -> CallbackParams? {
        guard let components = URLComponents(url: url, resolvingAgainstBaseURL: false),
              components.scheme == "uphillai",
              components.host == "coros" || url.absoluteString.contains("coros/callback") else {
            return nil
        }
        let items = components.queryItems ?? []
        let state = items.first(where: { $0.name == "state" })?.value
        let token = items.first(where: { $0.name == "token" })?.value
        let result = items.first(where: { $0.name == "result" })?.value
        let isError = result == "error" || (state == nil && token == nil)
        return CallbackParams(state: state, token: token, isError: isError)
    }
}
