import Foundation

enum ShoeRotationSlot: String, Codable, Sendable, CaseIterable, Identifiable {
    case daily = "daily"
    case tempo = "tempo"
    case race = "race"
    case trail = "trail"

    var id: String { rawValue }

    var title: String {
        switch self {
        case .daily: return "Daily"
        case .tempo: return "Tempo"
        case .race: return "Race"
        case .trail: return "Trail"
        }
    }

    var subtitle: String {
        switch self {
        case .daily: return "Easy & Recovery"
        case .tempo: return "Intervals & Threshold"
        case .race: return "Race Day Carbon"
        case .trail: return "Technical & Mountain"
        }
    }

    var assetName: String {
        switch self {
        case .daily: return "shoe_daily"
        case .tempo: return "shoe_tempo"
        case .race: return "shoe_race"
        case .trail: return "shoe_trail"
        }
    }

    var symbolFallback: String {
        switch self {
        case .daily: return "figure.run"
        case .tempo: return "bolt.fill"
        case .race: return "flag.checkered"
        case .trail: return "mountain.2.fill"
        }
    }

    var popularPresets: [(brand: String, model: String)] {
        switch self {
        case .daily:
            return [
                ("Nike", "Pegasus 41"),
                ("Hoka", "Clifton 10"),
                ("Asics", "Novablast 5"),
                ("Brooks", "Glycerin 23"),
                ("Saucony", "Triumph 23")
            ]
        case .tempo:
            return [
                ("Saucony", "Endorphin Speed 4"),
                ("Hoka", "Mach 7"),
                ("Adidas", "Adizero Boston 13"),
                ("New Balance", "FuelCell Rebel v5"),
                ("Asics", "Superblast 3")
            ]
        case .race:
            return [
                ("Nike", "Vaporfly 3"),
                ("Nike", "Alphafly 3"),
                ("Hoka", "Rocket X 3"),
                ("Saucony", "Endorphin Pro 5"),
                ("Asics", "Metaspeed Sky Tokyo")
            ]
        case .trail:
            return [
                ("Salomon", "S/Lab Genesis"),
                ("Hoka", "Speedgoat 6"),
                ("Saucony", "Peregrine 16"),
                ("Brooks", "Cascadia 19"),
                ("Altra", "Mont Blanc Carbon")
            ]
        }
    }
}

struct ShoeItem: Codable, Sendable, Identifiable, Equatable {
    var id: String { "\(slot.rawValue)_\(brand)_\(model)" }
    var slot: ShoeRotationSlot
    var brand: String
    var model: String
    var distanceKm: Double
    var maxDistanceKm: Double
    var isRetired: Bool
    var notes: String?

    init(
        slot: ShoeRotationSlot,
        brand: String,
        model: String,
        distanceKm: Double = 0,
        maxDistanceKm: Double = 700,
        isRetired: Bool = false,
        notes: String? = nil
    ) {
        self.slot = slot
        self.brand = brand
        self.model = model
        self.distanceKm = distanceKm
        self.maxDistanceKm = maxDistanceKm
        self.isRetired = isRetired
        self.notes = notes
    }

    var wearRatio: Double {
        guard maxDistanceKm > 0 else { return 0 }
        return min(max(distanceKm / maxDistanceKm, 0), 1.0)
    }

    var remainingKm: Double {
        max(maxDistanceKm - distanceKm, 0)
    }
}

struct ShoeRotation: Codable, Sendable, Equatable {
    var shoes: [ShoeItem]

    init(shoes: [ShoeItem] = []) {
        self.shoes = shoes
    }

    func shoe(for slot: ShoeRotationSlot) -> ShoeItem? {
        shoes.first { $0.slot == slot && !$0.isRetired }
    }

    mutating func setShoe(_ shoe: ShoeItem) {
        shoes.removeAll { $0.slot == shoe.slot }
        shoes.append(shoe)
    }

    mutating func removeShoe(for slot: ShoeRotationSlot) {
        shoes.removeAll { $0.slot == slot }
    }

    mutating func addDistance(_ km: Double, for slot: ShoeRotationSlot) {
        if let idx = shoes.firstIndex(where: { $0.slot == slot && !$0.isRetired }) {
            shoes[idx].distanceKm += km
        }
    }

    static var defaultRotation: ShoeRotation { previewDefault }

    var daily: ShoeItem? { shoe(for: .daily) }
    var tempo: ShoeItem? { shoe(for: .tempo) }
    var race: ShoeItem? { shoe(for: .race) }
    var trail: ShoeItem? { shoe(for: .trail) }

    static var previewDefault: ShoeRotation {
        ShoeRotation(shoes: [
            ShoeItem(slot: .daily, brand: "Nike", model: "Pegasus 41", distanceKm: 280, maxDistanceKm: 750),
            ShoeItem(slot: .tempo, brand: "Saucony", model: "Endorphin Speed 4", distanceKm: 145, maxDistanceKm: 650),
            ShoeItem(slot: .race, brand: "Nike", model: "Vaporfly 3", distanceKm: 42, maxDistanceKm: 400),
            ShoeItem(slot: .trail, brand: "Salomon", model: "S/Lab Genesis", distanceKm: 210, maxDistanceKm: 700)
        ])
    }
}

struct ShoeRecommendation: Codable, Sendable, Identifiable, Equatable {
    var id: String { "\(brand)_\(model)" }
    let model: String
    let brand: String
    let foamMaterial: String
    let outsoleCompound: String
    let lugDepth: String
    let drop: String
    let stack: String
    let weight: String
    let price: String
    let pros: String
    let cons: String

    init(
        model: String,
        brand: String,
        foamMaterial: String,
        outsoleCompound: String,
        lugDepth: String,
        drop: String,
        stack: String,
        weight: String,
        price: String,
        pros: String,
        cons: String
    ) {
        self.model = model
        self.brand = brand
        self.foamMaterial = foamMaterial
        self.outsoleCompound = outsoleCompound
        self.lugDepth = lugDepth
        self.drop = drop
        self.stack = stack
        self.weight = weight
        self.price = price
        self.pros = pros
        self.cons = cons
    }
}

struct GearPlan: Codable, Sendable, Equatable {
    let recommendations: [ShoeRecommendation]
    let tips: [String]
    let feedbackToken: String?

    init(
        recommendations: [ShoeRecommendation],
        tips: [String],
        feedbackToken: String? = nil
    ) {
        self.recommendations = recommendations
        self.tips = tips
        self.feedbackToken = feedbackToken
    }
}

struct GearParams: Codable, Sendable {
    var surface: String?
    var cushioning: String?
    var width: String?
    var carbonPlate: String?
    var budget: String?
    var terrain: [String]?
    var useCase: String?
    var preferredBrands: String?
    var additionalContext: String?
    var raceDistance: String?
    var raceName: String?
    var userProfile: String?
    var activePlanContext: String?

    init(
        surface: String? = "trail",
        cushioning: String? = "balanced",
        width: String? = "normal",
        carbonPlate: String? = "unknown",
        budget: String? = nil,
        terrain: [String]? = ["runnable"],
        useCase: String? = nil,
        preferredBrands: String? = nil,
        additionalContext: String? = nil,
        raceDistance: String? = nil,
        raceName: String? = nil,
        userProfile: String? = nil,
        activePlanContext: String? = nil
    ) {
        self.surface = surface
        self.cushioning = cushioning
        self.width = width
        self.carbonPlate = carbonPlate
        self.budget = budget
        self.terrain = terrain
        self.useCase = useCase
        self.preferredBrands = preferredBrands
        self.additionalContext = additionalContext
        self.raceDistance = raceDistance
        self.raceName = raceName
        self.userProfile = userProfile
        self.activePlanContext = activePlanContext
    }
}
