import Foundation

struct CoachNote: Codable, Sendable, Identifiable, Equatable {
    let id: Int
    let coachId: Int
    let athleteId: Int
    let targetType: String // "workout", "week", "plan", "general"
    let targetId: Int?
    let note: String
    let createdAt: String?

    init(
        id: Int,
        coachId: Int,
        athleteId: Int,
        targetType: String,
        targetId: Int? = nil,
        note: String,
        createdAt: String? = nil
    ) {
        self.id = id
        self.coachId = coachId
        self.athleteId = athleteId
        self.targetType = targetType
        self.targetId = targetId
        self.note = note
        self.createdAt = createdAt
    }
}

struct CoachNotesResponse: Codable, Sendable {
    let notes: [CoachNote]
}

struct CoachNoteCreatePayload: Codable, Sendable {
    let targetType: String
    let targetId: Int?
    let note: String

    init(targetType: String, targetId: Int? = nil, note: String) {
        self.targetType = targetType
        self.targetId = targetId
        self.note = note
    }
}
