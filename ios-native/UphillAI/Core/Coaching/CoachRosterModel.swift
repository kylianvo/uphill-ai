import Foundation

struct CoachedAthleteRow: Codable, Sendable, Identifiable, Equatable {
    let id: Int // relationship link id
    let athleteId: Int
    let athleteName: String?
    let athleteEmail: String
    let status: String // "active" | "invited"
    let invitedAt: String?
    let respondedAt: String?

    var displayName: String {
        if let name = athleteName, !name.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty {
            return name
        }
        return athleteEmail
    }

    var isActive: Bool {
        status.lowercased() == "active"
    }

    init(
        id: Int,
        athleteId: Int,
        athleteName: String? = nil,
        athleteEmail: String,
        status: String = "active",
        invitedAt: String? = nil,
        respondedAt: String? = nil
    ) {
        self.id = id
        self.athleteId = athleteId
        self.athleteName = athleteName
        self.athleteEmail = athleteEmail
        self.status = status
        self.invitedAt = invitedAt
        self.respondedAt = respondedAt
    }
}

struct CoachingInvite: Codable, Sendable, Identifiable, Equatable {
    let id: Int // relationship link id
    let coachId: Int
    let coachName: String?
    let coachEmail: String
    let status: String
    let invitedAt: String?

    var displayCoachName: String {
        if let name = coachName, !name.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty {
            return name
        }
        return coachEmail
    }

    init(
        id: Int,
        coachId: Int,
        coachName: String? = nil,
        coachEmail: String,
        status: String = "invited",
        invitedAt: String? = nil
    ) {
        self.id = id
        self.coachId = coachId
        self.coachName = coachName
        self.coachEmail = coachEmail
        self.status = status
        self.invitedAt = invitedAt
    }
}
