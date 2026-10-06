import Foundation

protocol KnowledgeServicing: Sendable {
    func fetchCards(topic: String?, lang: String) async throws -> [KnowledgeCardModel]
    func fetchRandomCards(count: Int, lang: String) async throws -> [KnowledgeCardModel]
    func fetchTopics() async throws -> [String]
    func fetchSources() async throws -> [KnowledgeSource]
    func addLink(url: String) async throws
}

struct KnowledgeService: KnowledgeServicing {
    private let client: APIClient

    init(client: APIClient) {
        self.client = client
    }

    func fetchCards(topic: String? = nil, lang: String = "en") async throws -> [KnowledgeCardModel] {
        var queryItems: [URLQueryItem] = [URLQueryItem(name: "lang", value: lang)]
        if let topic, topic != "All" {
            queryItems.append(URLQueryItem(name: "topic", value: topic))
        }

        do {
            let endpoint = Endpoint<KnowledgeCardsResponse>.get("/api/knowledge/cards", query: queryItems)
            let res = try await client.send(endpoint)
            if !res.cards.isEmpty {
                return res.cards
            }
        } catch {
            // fallback to curated library
        }

        return Self.curatedCards.filter { card in
            guard let topic, topic != "All" else { return true }
            return card.topic.caseInsensitiveCompare(topic) == .orderedSame
        }
    }

    func fetchRandomCards(count: Int = 3, lang: String = "en") async throws -> [KnowledgeCardModel] {
        let queryItems = [
            URLQueryItem(name: "n", value: String(count)),
            URLQueryItem(name: "lang", value: lang)
        ]

        do {
            let endpoint = Endpoint<KnowledgeCardsResponse>.get("/api/knowledge/cards/random", query: queryItems)
            let res = try await client.send(endpoint)
            if !res.cards.isEmpty {
                return res.cards
            }
        } catch {
            // fallback
        }

        return Array(Self.curatedCards.shuffled().prefix(count))
    }

    func fetchTopics() async throws -> [String] {
        do {
            let endpoint = Endpoint<[String]>.get("/api/knowledge/topics")
            return try await client.send(endpoint)
        } catch {
            return ["All", "Training", "Nutrition", "Recovery", "Pacing", "Mindset", "Gear"]
        }
    }

    func fetchSources() async throws -> [KnowledgeSource] {
        do {
            let endpoint = Endpoint<[KnowledgeSource]>.get("/api/rag/sources")
            return try await client.send(endpoint)
        } catch {
            return [
                KnowledgeSource(id: 1, title: "Training for the Uphill Athlete (House, Jornet, Johnston)", type: "pdf"),
                KnowledgeSource(id: 2, title: "Evoke Endurance: Aerobic Deficiency Syndrome", type: "web", url: "https://evokeendurance.com"),
                KnowledgeSource(id: 3, title: "Science of Ultra: Fueling & Hydration", type: "youtube")
            ]
        }
    }

    func addLink(url: String) async throws {
        struct LinkPayload: Codable { let url: String }
        let endpoint = try Endpoint<EmptyResponse>.send(.post, "/api/rag/link", body: LinkPayload(url: url))
        _ = try await client.send(endpoint)
    }

    // MARK: - Curated Mountain & Ultra Running Knowledge Base

    static let curatedCards: [KnowledgeCardModel] = [
        KnowledgeCardModel(
            id: 1,
            chapterTitle: "Aerobic Deficiency Syndrome (ADS)",
            summary: "When aerobic capacity is undertrained, the body burns glycogen even at walking paces. Building a deep Zone 1-2 aerobic base shifts your metabolism to burn fat as the primary fuel source.",
            keyPoints: [
                "Keep 80-85% of weekly volume below AeT (conversational nose-breathing pace).",
                "Testing AeT via heart rate drift test: HR should rise less than 5% over an hour at constant speed.",
                "Patience is key: rebuilding mitochondrial density takes 12 to 24 weeks of consistent low-intensity volume."
            ],
            tags: ["aerobic", "mitochondria", "zone2", "metabolism"],
            topic: "Training",
            sourceLabel: "Training for the Uphill Athlete"
        ),
        KnowledgeCardModel(
            id: 2,
            chapterTitle: "Gut Training: 60-90g Carbs / Hour",
            summary: "During ultras longer than 4 hours, exogenous carbohydrate oxidation preserves liver and muscle glycogen. The gut must be systematically trained in long runs to tolerate high carb flux.",
            keyPoints: [
                "Utilize a 2:1 or 1:0.8 glucose-to-fructose ratio to utilize separate intestinal transporters (SGLT1 and GLUT5).",
                "Practice race-day fueling frequency: 20-30g every 20 minutes with 150ml water.",
                "Avoid high-fat or high-protein solids during steep high-exertion climbs when blood flow is diverted from the gut."
            ],
            tags: ["fueling", "carbs", "gut-training", "ultra"],
            topic: "Nutrition",
            sourceLabel: "Jeukendrup Sports Nutrition"
        ),
        KnowledgeCardModel(
            id: 3,
            chapterTitle: "Minetti Gradient Cost & The Hike Threshold",
            summary: "Metabolic cost per meter rises exponentially once gradient exceeds 15%. Efficient ultra runners transition from running to power hiking at ~18-20% grade to conserve glycogen.",
            keyPoints: [
                "On grades steeper than 20%, running burns up to 35% more energy per vertical meter than power hiking for negligible speed gain.",
                "Use trekking poles to engage latissimus and core musculature, offloading knee extensors.",
                "Shorten stride cadence on climbs to keep heart rate strictly clamped below AeT."
            ],
            tags: ["minetti", "grade", "hike-threshold", "pacing"],
            topic: "Pacing",
            sourceLabel: "Minetti (2002) Energetics of Locomotion"
        ),
        KnowledgeCardModel(
            id: 4,
            chapterTitle: "Tendon Remodeling & Sleep Architecture",
            summary: "Connective tissue collagen synthesis and neuromuscular recovery peak during deep slow-wave sleep (NREM Stage 3/4) through pulsatile human growth hormone release.",
            keyPoints: [
                "Prioritize consistent sleep schedules: 8-9 hours per night during peak training weeks.",
                "Track resting HR and HRV trends: sustained multi-day drops in HRV indicate sympathetic fatigue.",
                "Magnesium glycinate (300-400mg) and tart cherry extract promote muscle relaxation and reduce inflammatory soreness."
            ],
            tags: ["recovery", "sleep", "hrv", "collagen"],
            topic: "Recovery",
            sourceLabel: "Matthew Walker: Why We Sleep"
        ),
        KnowledgeCardModel(
            id: 5,
            chapterTitle: "Segmenting 100K: The 3-Aid-Station Horizon",
            summary: "Never run 100 kilometers in your head. Psychological overwhelm triggers early central governor fatigue. Anchor your mind solely to the immediate aid station ahead.",
            keyPoints: [
                "Break the race into bite-sized 8-12km micro-goals.",
                "When the dark low-point strikes between 50-70km, recognize that mood follows blood sugar: eat 200 kcal and wait 15 minutes before any decision.",
                "Focus on process execution (cadence, breath, fueling rhythm) rather than elapsed time or field position."
            ],
            tags: ["mindset", "central-governor", "mental-toughness"],
            topic: "Mindset",
            sourceLabel: "Endure: Cameron Elson"
        ),
        KnowledgeCardModel(
            id: 6,
            chapterTitle: "Outsole Compound & Lug Depth Selection",
            summary: "Traction dictates braking muscle fatigue. Matching lug depth and rubber compound to course terrain saves thousands of micro-slips over an ultra.",
            keyPoints: [
                "Deep 5.0mm+ lugs with wide channel spacing are essential for wet clay, mud, and loose tropical scree.",
                "Vibram Megagrip and Contagrip wet-traction compounds excel on slick river rock and damp limestone roots.",
                "For dry hardpack or runnable fire roads, 3.5-4.0mm lugs reduce ground-contact drag and foot fatigue."
            ],
            tags: ["gear", "shoes", "traction", "vibram"],
            topic: "Gear",
            sourceLabel: "Uphill AI Gear Vault"
        ),
        KnowledgeCardModel(
            id: 7,
            chapterTitle: "Muscular Endurance: Vertical Intervals",
            summary: "Uphill running economy requires high mechanical power at low velocity. ME training develops fatigue-resistant slow-twitch motor units in the calves, quads, and glutes.",
            keyPoints: [
                "Perform continuous steep hill repeats (15-25% gradient) at Zone 3 effort with easy walk-down recovery.",
                "Incorporate weighted uphill treadmill or stair climbs (10-15% body weight vest) once weekly in the base block.",
                "Preserve structural form: tall posture, forward chest lean from ankles rather than bending at the waist."
            ],
            tags: ["muscular-endurance", "vert", "hill-intervals"],
            topic: "Training",
            sourceLabel: "Training for the Uphill Athlete"
        ),
        KnowledgeCardModel(
            id: 8,
            chapterTitle: "Sodium Balance & Exercise-Associated Hyponatremia",
            summary: "Over-drinking plain water without sodium dilutes blood plasma osmolality. Maintain 500-800mg sodium per liter of fluid consumed during hot mountain races.",
            keyPoints: [
                "Sweat sodium concentration varies widely (400mg to 1,800mg per liter): test your sweat rate in warm training runs.",
                "Carry chewable salt caps for hot humid mid-day sections.",
                "Signs of sodium deficit include brain fog, swollen fingers, and nausea despite feeling thirsty."
            ],
            tags: ["electrolytes", "hydration", "sodium", "heat"],
            topic: "Nutrition",
            sourceLabel: "Tim Noakes: Waterlogged"
        )
    ]
}
