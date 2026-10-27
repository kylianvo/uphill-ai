import Foundation
import SwiftUI
import Testing
import UIKit
@testable import UphillAI

/// kb_search gear results arrive as card_type "shoe_recommendations" in the Gear Vault shoe shape.
struct ChatShoeCardTests {
    /// What the server sends for "Norda 005 for my race?" (extra keys included: the decoder must ignore them).
    static let serverCardData = #"""
    {"query": "Norda 005 for My race?", "exact_match": true, "tips": [],
     "recommendations": [{"brand": "Norda", "model": "005", "foam_material": "Supercritical EVA",
       "outsole_compound": "Vibram Megagrip Litebase", "lug_depth": "3.5 mm", "drop": "6 mm", "stack": "30 mm",
       "weight": "9.4 oz / 266 g", "price": "$295", "pros": "Grippy and stable", "cons": "Pricey",
       "best_for": "long technical trail", "terrain": "Technical/rocky trails"}]}
    """#

    static func payload() throws -> ToolResultPayload {
        let data = try JSONDecoder().decode([String: JSONValue].self, from: Data(serverCardData.utf8))
        return ToolResultPayload(toolCallId: "c-1", name: "kb_search", cardType: "shoe_recommendations", cardData: data)
    }

    @Test func serverShoeResultDecodesToTheGearVaultShoe() throws {
        let plan = try #require(try Self.payload().decodeGearPlan())
        let shoe = try #require(plan.recommendations.first)
        #expect((shoe.brand, shoe.model, shoe.lugDepth, shoe.drop) == ("Norda", "005", "3.5 mm", "6 mm"))
        #expect(plan.tips.isEmpty)
    }

    /// Written only when SCREENSHOT_DIR is set: the chat shoe card, collapsed and with one shoe open.
    @MainActor @Test func renderChatShoeCard() async throws {
        guard let outDir = ProcessInfo.processInfo.environment["SCREENSHOT_DIR"] else { return }
        let plan = try #require(try Self.payload().decodeGearPlan())
        let two = GearPlan(recommendations: plan.recommendations + [ShoeRecommendation(
            model: "Mont Blanc Carbon", brand: "Altra", foamMaterial: "Ego Pro / Ego Max",
            outsoleCompound: "Vibram Megagrip Litebase", lugDepth: "4.0 mm", drop: "0 mm", stack: "33 mm",
            weight: "9.3 oz / 264 g", price: "$260", pros: "Great Vibram traction", cons: "Very expensive")], tips: [])
        let size = CGSize(width: 402, height: 640)
        let controller = UIHostingController(rootView: ScrollView { ChatGearCard(plan: two).padding() }
            .frame(width: size.width, height: size.height).background(UH.Palette.surface))
        let window = UIWindow(frame: CGRect(origin: .zero, size: size))
        window.rootViewController = controller
        window.makeKeyAndVisible()
        defer { window.isHidden = true }
        controller.view.layoutIfNeeded()
        try await Task.sleep(for: .milliseconds(400))
        let img = UIGraphicsImageRenderer(size: size).image { _ in
            controller.view.drawHierarchy(in: CGRect(origin: .zero, size: size), afterScreenUpdates: true)
        }
        try img.pngData()?.write(to: URL(fileURLWithPath: "\(outDir)/chat-shoe-card.png"))
    }
}
