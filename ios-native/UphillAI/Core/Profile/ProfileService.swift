import Foundation

/// Only athlete training settings; no bring-your-own-key field.
struct ProfileDraft: Encodable, Sendable {
    var age: Int
    var maxHr: Int
    var restingHr: Int
    var aetHr: Int
    var antHr: Int
    var gender: String?
    var heightCm: Double?
    var weightKg: Double?
    var zone2PaceMin: String?
    var zone2PaceMax: String?
    var thresholdPace: String?
    var paceZoneModel: String
    var athleteNotes: String?

    init(user: User) {
        age = user.age ?? 30
        maxHr = user.maxHr ?? 185
        restingHr = user.restingHr ?? 60
        aetHr = user.aetHr ?? 135
        antHr = user.antHr ?? 165
        gender = user.gender
        heightCm = user.heightCm
        weightKg = user.weightKg
        zone2PaceMin = user.zone2PaceMin
        zone2PaceMax = user.zone2PaceMax
        thresholdPace = user.thresholdPace
        paceZoneModel = user.paceZoneModel ?? "5_zone"
        athleteNotes = user.athleteNotes
    }

    func body(merging user: User, section: TrainingDestination) -> ProfileDraft {
        var body = ProfileDraft(user: user)
        switch section {
        case .aboutYou:
            body.age = age; body.gender = gender; body.heightCm = heightCm; body.weightKg = weightKg
            body.athleteNotes = athleteNotes
        case .heartRate:
            body.maxHr = maxHr; body.restingHr = restingHr; body.aetHr = aetHr; body.antHr = antHr
        case .paces:
            body.zone2PaceMin = zone2PaceMin; body.zone2PaceMax = zone2PaceMax
            body.thresholdPace = thresholdPace; body.paceZoneModel = paceZoneModel
        case .trainingZones:
            body.maxHr = maxHr; body.restingHr = restingHr; body.aetHr = aetHr; body.antHr = antHr
            body.zone2PaceMin = zone2PaceMin; body.zone2PaceMax = zone2PaceMax
            body.thresholdPace = thresholdPace; body.paceZoneModel = paceZoneModel
        case .schedule, .raceHistory, .nutritionLab, .gearVault, .goalDeterminer, .paceStrategy, .knowledgeHub: break
        }
        return body
    }

    var heartRateError: String? {
        if aetHr >= antHr { return L("Aerobic threshold (AeT) must be below anaerobic threshold (AnT).") }
        if antHr > maxHr { return L("Anaerobic threshold (AnT) must not exceed max heart rate.") }
        if restingHr >= aetHr { return L("Resting heart rate must be below aerobic threshold (AeT).") }
        return nil
    }
}

struct PaceZoneRow: Identifiable {
    let id: Int
    let pace: String
    let hr: String?
}

struct PaceZones: Decodable, Sendable {
    let model: String?
    let zone1Pace: String?
    let zone2Pace: String?
    let zone3Pace: String?
    let zone4Pace: String?
    let zone5Pace: String?
    let zone1Hr: String?
    let zone2Hr: String?
    let zone3Hr: String?
    let zone4Hr: String?
    let zone5Hr: String?

    var rows: [PaceZoneRow] {
        let paces = [zone1Pace, zone2Pace, zone3Pace, zone4Pace, zone5Pace]
        let hrs = [zone1Hr, zone2Hr, zone3Hr, zone4Hr, zone5Hr]
        return (0..<(model == "4_zone" ? 4 : 5)).compactMap { i in
            paces[i].map { PaceZoneRow(id: i + 1, pace: $0, hr: hrs[i]) }
        }
    }
}

struct ProfileService: Sendable {
    let client: APIClient
    func update(_ body: ProfileDraft) async throws -> User {
        try await client.send(.send(.post, "/api/auth/update-profile", body: body))
    }
    func zones(model: String) async throws -> PaceZones {
        try await client.send(.get("/api/auth/pace-zones", query: [URLQueryItem(name: "model", value: model)]))
    }
    func changePassword(_ password: String) async throws {
        struct Body: Encodable { let password: String }
        let _: EmptyResponse = try await client.send(.send(.post, "/api/auth/set-password", body: Body(password: password)))
    }
}
