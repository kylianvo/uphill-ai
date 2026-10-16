import Foundation

protocol NotificationServicing: Sendable {
    func preferences() async throws -> NotificationPreferences
    func updatePreferences(_ value: NotificationPreferences) async throws -> NotificationPreferences
    func registerInstallation(id: UUID, token: String, permission: String) async throws
    func removeInstallation(id: UUID) async throws
    func opened(id: UUID) async throws
}

struct NotificationService: NotificationServicing {
    let client: APIClient

    func preferences() async throws -> NotificationPreferences {
        try await client.send(.get("/api/notifications/preferences"))
    }

    func updatePreferences(_ value: NotificationPreferences) async throws -> NotificationPreferences {
        var object = try JSONSerialization.jsonObject(with: JSONCoding.encoder.encode(value)) as! [String: Any]
        // Optional clears must reach PATCH; synthesized Codable omits nil values.
        for key in ["paused_until", "checklist_snoozed_until", "timezone"] where object[key] == nil { object[key] = NSNull() }
        let endpoint = Endpoint<NotificationPreferences>(method: .patch, path: "/api/notifications/preferences", body: try JSONSerialization.data(withJSONObject: object))
        return try await client.send(endpoint)
    }

    func registerInstallation(id: UUID, token: String, permission: String) async throws {
        struct Body: Encodable { let token: String; let environment: String; let permission: String }
        #if DEBUG
        let environment = "sandbox"
        #else
        let environment = "production"
        #endif
        let endpoint = try Endpoint<EmptyResponse>.send(.put, "/api/notifications/installations/\(id.uuidString)", body: Body(token: token, environment: environment, permission: permission))
        _ = try await client.send(endpoint)
    }

    func removeInstallation(id: UUID) async throws {
        let _: EmptyResponse = try await client.send(.delete("/api/notifications/installations/\(id.uuidString)"))
    }

    func opened(id: UUID) async throws {
        let _: EmptyResponse = try await client.send(.post("/api/notifications/\(id.uuidString)/opened"))
    }
}
