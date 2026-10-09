import Foundation

enum ProductFormat: String, Codable, Sendable, CaseIterable, Identifiable {
    case gel = "gel"
    case chews = "chews"
    case drinkMix = "drink_mix"
    case solid = "solid"

    var id: String { rawValue }

    var displayName: String {
        switch self {
        case .gel: return "Gel"
        case .chews: return "Chews"
        case .drinkMix: return L("Drink Mix")
        case .solid: return L("Solid")
        }
    }

    var assetName: String {
        switch self {
        case .gel: return "nutrition_gel"
        case .chews: return "nutrition_chews"
        case .drinkMix: return "nutrition_drink_mix"
        case .solid: return "nutrition_solid"
        }
    }

    var symbolFallback: String {
        switch self {
        case .gel: return "drop.fill"
        case .chews: return "square.grid.2x2.fill"
        case .drinkMix: return "waterbottle.fill"
        case .solid: return "takeoutbag.and.cup.and.straw.fill"
        }
    }
}

struct NutritionProduct: Codable, Sendable, Identifiable, Equatable {
    var id: String { "\(brand)_\(name)" }
    let brand: String
    let name: String
    let totalQuantity: Int
    let carbsPerUnit: Double
    let sodiumPerUnit: Double
    let proteinPerUnit: Double
    let techNotes: String

    init(
        brand: String,
        name: String,
        totalQuantity: Int,
        carbsPerUnit: Double,
        sodiumPerUnit: Double,
        proteinPerUnit: Double = 0,
        techNotes: String = ""
    ) {
        self.brand = brand
        self.name = name
        self.totalQuantity = totalQuantity
        self.carbsPerUnit = carbsPerUnit
        self.sodiumPerUnit = sodiumPerUnit
        self.proteinPerUnit = proteinPerUnit
        self.techNotes = techNotes
    }

    var format: ProductFormat {
        let combined = "\(name) \(techNotes)".lowercased()
        if combined.contains("solid") || combined.contains("bar") || combined.contains("waffle") {
            return .solid
        } else if combined.contains("drink") || combined.contains("mix") || combined.contains("hydration") || combined.contains("scoop") {
            return .drinkMix
        } else if combined.contains("chew") {
            return .chews
        } else {
            return .gel
        }
    }
}

struct HourlyEntry: Codable, Sendable, Identifiable, Equatable {
    var id: Int { hour }
    let hour: Int
    let action: String
    let carbs: Double
    let sodium: Double

    init(hour: Int, action: String, carbs: Double, sodium: Double) {
        self.hour = hour
        self.action = action
        self.carbs = carbs
        self.sodium = sodium
    }
}

struct NutritionPlan: Codable, Sendable, Equatable {
    let products: [NutritionProduct]
    let hourlyPlan: [HourlyEntry]
    let tips: [String]
    let feedbackToken: String?

    init(
        products: [NutritionProduct],
        hourlyPlan: [HourlyEntry],
        tips: [String],
        feedbackToken: String? = nil
    ) {
        self.products = products
        self.hourlyPlan = hourlyPlan
        self.tips = tips
        self.feedbackToken = feedbackToken
    }

    var totalCarbs: Double {
        hourlyPlan.reduce(0) { $0 + $1.carbs }
    }

    var totalSodium: Double {
        hourlyPlan.reduce(0) { $0 + $1.sodium }
    }

    var avgCarbsPerHour: Double {
        guard !hourlyPlan.isEmpty else { return 0 }
        return totalCarbs / Double(hourlyPlan.count)
    }

    var avgSodiumPerHour: Double {
        guard !hourlyPlan.isEmpty else { return 0 }
        return totalSodium / Double(hourlyPlan.count)
    }
}

struct NutritionParams: Codable, Sendable {
    var distanceKm: Double?
    var elevationGainM: Double?
    var targetTimeHours: Double?
    var weatherTemp: String?
    var preferredBrands: String?
    var targetCarbH: Double?
    var targetSodiumH: Double?
    var preferredFormat: [String]?
    var athleteLevel: String?
    var additionalContext: String?
    var userProfile: String?
    var activePlanContext: String?

    init(
        distanceKm: Double? = nil,
        elevationGainM: Double? = nil,
        targetTimeHours: Double? = nil,
        weatherTemp: String? = nil,
        preferredBrands: String? = nil,
        targetCarbH: Double? = nil,
        targetSodiumH: Double? = nil,
        preferredFormat: [String]? = nil,
        athleteLevel: String? = nil,
        additionalContext: String? = nil,
        userProfile: String? = nil,
        activePlanContext: String? = nil
    ) {
        self.distanceKm = distanceKm
        self.elevationGainM = elevationGainM
        self.targetTimeHours = targetTimeHours
        self.weatherTemp = weatherTemp
        self.preferredBrands = preferredBrands
        self.targetCarbH = targetCarbH
        self.targetSodiumH = targetSodiumH
        self.preferredFormat = preferredFormat
        self.athleteLevel = athleteLevel
        self.additionalContext = additionalContext
        self.userProfile = userProfile
        self.activePlanContext = activePlanContext
    }
}

struct CatalogProduct: Codable, Sendable, Identifiable, Equatable {
    let id: Int
    let brand: String
    let name: String
    let type: String
    let carbsGrams: Double
    let sodiumMg: Double
    let caffeineMg: Double?
    let waterRatioMl: Double?

    init(
        id: Int,
        brand: String,
        name: String,
        type: String,
        carbsGrams: Double,
        sodiumMg: Double,
        caffeineMg: Double? = nil,
        waterRatioMl: Double? = nil
    ) {
        self.id = id
        self.brand = brand
        self.name = name
        self.type = type
        self.carbsGrams = carbsGrams
        self.sodiumMg = sodiumMg
        self.caffeineMg = caffeineMg
        self.waterRatioMl = waterRatioMl
    }
}
