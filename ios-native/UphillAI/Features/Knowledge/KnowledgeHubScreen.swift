import SwiftUI

struct KnowledgeHubScreen: View {
    @Environment(\.dismiss) private var dismiss
    let service: any KnowledgeServicing

    // State
    @State private var cards: [KnowledgeCardModel] = []
    @State private var dailyCards: [KnowledgeCardModel] = []
    @State private var selectedTopic: String = "All"
    @State private var topics: [String] = ["All", "Training", "Nutrition", "Recovery", "Pacing", "Mindset", "Gear"]
    @State private var searchText: String = ""
    @State private var isLoading: Bool = false
    @State private var showSourcesSection: Bool = false
    @State private var sources: [KnowledgeSource] = []
    @State private var newLinkInput: String = ""
    @State private var isSubmittingLink: Bool = false
    @State private var statusMessage: String? = nil

    init(
        service: any KnowledgeServicing,
        initialCards: [KnowledgeCardModel]? = nil
    ) {
        self.service = service
        if let initialCards {
            _cards = State(initialValue: initialCards)
            _dailyCards = State(initialValue: Array(initialCards.prefix(2)))
        }
    }

    private var filteredCards: [KnowledgeCardModel] {
        cards.filter { card in
            let matchesTopic = (selectedTopic == "All") || (card.topic.caseInsensitiveCompare(selectedTopic) == .orderedSame)
            if !matchesTopic { return false }

            if searchText.trimmingCharacters(in: .whitespaces).isEmpty {
                return true
            }

            let q = searchText.lowercased()
            let titleMatch = card.chapterTitle.lowercased().contains(q)
            let summaryMatch = card.summary.lowercased().contains(q)
            let tagMatch = card.tags.contains { $0.lowercased().contains(q) }
            let pointMatch = card.keyPoints.contains { $0.lowercased().contains(q) }
            return titleMatch || summaryMatch || tagMatch || pointMatch
        }
    }

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: UH.Space.section) {
                // Header & Search
                headerAndSearchSection

                // Daily Insight Widget
                if !dailyCards.isEmpty && searchText.isEmpty && selectedTopic == "All" {
                    dailyInsightSection
                }

                // Topic Filter Bar
                topicFilterBar

                // Cards Count & Filter Status
                HStack {
                    Text("\(filteredCards.count) INSIGHTS")
                        .font(.system(size: 11, weight: .bold, design: .monospaced))
                        .foregroundStyle(UH.Palette.muted)
                    Spacer()
                    if selectedTopic != "All" {
                        Text(selectedTopic.uppercased())
                            .font(.system(size: 10, weight: .bold, design: .monospaced))
                            .foregroundStyle(UH.Palette.accentInk)
                    }
                }
                .padding(.horizontal, 4)

                // Cards List
                if filteredCards.isEmpty {
                    emptyStateView
                } else {
                    LazyVStack(spacing: 12) {
                        ForEach(filteredCards) { card in
                            KnowledgeCardView(card: card)
                        }
                    }
                }

                // Indexed Sources / Ingestion Footer
                sourcesAccordionSection
                    .padding(.bottom, UH.Space.reading)
            }
            .padding(UH.Space.regular)
        }
        .background(UH.Palette.surface.ignoresSafeArea())
        .navigationTitle("Knowledge Hub")
        .navigationBarTitleDisplayMode(.inline)
        .task {
            if cards.isEmpty {
                await loadKnowledgeData()
            }
        }
    }

    // MARK: - Header & Search

    private var headerAndSearchSection: some View {
        VStack(alignment: .leading, spacing: 10) {
            VStack(alignment: .leading, spacing: 4) {
                Text("SCIENCE & PRACTICE")
                    .font(.system(size: 11, weight: .bold, design: .monospaced))
                    .tracking(0.8)
                    .foregroundStyle(UH.Palette.accentInk)
                Text("Mountain Running Library")
                    .font(UH.TextStyle.sectionTitle)
                    .foregroundStyle(UH.Palette.ink)
                Text("Curated endurance physiology, gut training protocol, uphill biomechanics, and mental models from verified sport science.")
                    .font(UH.TextStyle.caption)
                    .foregroundStyle(UH.Palette.secondary)
            }

            // Search Bar
            HStack(spacing: 8) {
                Image(systemName: "magnifyingglass")
                    .foregroundStyle(UH.Palette.muted)
                    .font(.system(size: 14))

                TextField("Search topics, keywords or #tags...", text: $searchText)
                    .font(UH.TextStyle.body)

                if !searchText.isEmpty {
                    Button {
                        searchText = ""
                    } label: {
                        Image(systemName: "xmark.circle.fill")
                            .foregroundStyle(UH.Palette.muted)
                            .font(.system(size: 14))
                    }
                }
            }
            .padding(10)
            .background(UH.Palette.surface, in: RoundedRectangle(cornerRadius: UH.Radius.control))
            .overlay(RoundedRectangle(cornerRadius: UH.Radius.control).stroke(UH.Palette.line))
        }
    }

    // MARK: - Daily Insight Widget

    private var dailyInsightSection: some View {
        VStack(alignment: .leading, spacing: 10) {
            HStack {
                HStack(spacing: 6) {
                    Image(systemName: "lightbulb.fill")
                        .font(.system(size: 14))
                        .foregroundStyle(UH.Palette.accentInk)
                    Text("DAILY INSIGHT")
                        .font(.system(size: 11, weight: .bold, design: .monospaced))
                        .foregroundStyle(UH.Palette.accentInk)
                }

                Spacer()

                Button {
                    UIImpactFeedbackGenerator(style: .light).impactOccurred()
                    Task {
                        dailyCards = Array(cards.shuffled().prefix(1))
                    }
                } label: {
                    HStack(spacing: 4) {
                        Image(systemName: "shuffle")
                        Text("Shuffle")
                    }
                    .font(.system(size: 11, weight: .bold, design: .monospaced))
                    .foregroundStyle(UH.Palette.ink)
                    .padding(.horizontal, 10)
                    .padding(.vertical, 4)
                    .background(UH.Palette.surface, in: Capsule())
                    .overlay(Capsule().stroke(UH.Palette.line))
                }
            }

            if let featured = dailyCards.first {
                KnowledgeCardView(card: featured)
            }
        }
        .padding(12)
        .background(
            LinearGradient(
                colors: [UH.Palette.accentInk.opacity(0.08), UH.Palette.surface],
                startPoint: .topLeading,
                endPoint: .bottomTrailing
            ),
            in: RoundedRectangle(cornerRadius: UH.Radius.panel)
        )
        .overlay(RoundedRectangle(cornerRadius: UH.Radius.panel).stroke(UH.Palette.accentInk.opacity(0.3), lineWidth: 1))
    }

    // MARK: - Topic Filter Bar

    private var topicFilterBar: some View {
        ScrollView(.horizontal, showsIndicators: false) {
            HStack(spacing: 8) {
                ForEach(topics, id: \.self) { topic in
                    let isSelected = selectedTopic.caseInsensitiveCompare(topic) == .orderedSame
                    Button {
                        selectedTopic = topic
                        UIImpactFeedbackGenerator(style: .light).impactOccurred()
                    } label: {
                        HStack(spacing: 5) {
                            if topic != "All" {
                                Image(systemName: iconForTopic(topic))
                                    .font(.system(size: 11))
                            }
                            Text(topic)
                                .font(UH.TextStyle.caption.weight(isSelected ? .bold : .medium))
                        }
                        .foregroundStyle(isSelected ? Color.white : UH.Palette.ink)
                        .padding(.horizontal, 12)
                        .padding(.vertical, 7)
                        .background(isSelected ? UH.Palette.ink : UH.Palette.surface, in: Capsule())
                        .overlay(Capsule().stroke(isSelected ? UH.Palette.ink : UH.Palette.line))
                    }
                }
            }
            .padding(.horizontal, 2)
            .padding(.vertical, 4)
        }
    }

    private func iconForTopic(_ topic: String) -> String {
        switch topic.lowercased() {
        case "training": return "mountain.2.fill"
        case "nutrition": return "fork.knife"
        case "recovery": return "bed.double.fill"
        case "pacing": return "stopwatch.fill"
        case "mindset": return "brain.head.profile"
        case "gear": return "backpack.fill"
        default: return "book.fill"
        }
    }

    // MARK: - Empty State

    private var emptyStateView: some View {
        VStack(spacing: 12) {
            Image(systemName: "text.book.closed")
                .font(.system(size: 32))
                .foregroundStyle(UH.Palette.muted)
            Text("No cards matching \"\(searchText)\"")
                .font(UH.TextStyle.body.weight(.medium))
                .foregroundStyle(UH.Palette.ink)
            Text("Try searching for terms like aerobic, carbs, sodium, sleep, or poles.")
                .font(UH.TextStyle.caption)
                .foregroundStyle(UH.Palette.secondary)
                .multilineTextAlignment(.center)
        }
        .frame(maxWidth: .infinity)
        .padding(.vertical, 36)
        .trainingCard()
    }

    // MARK: - Sources & Ingestion

    private var sourcesAccordionSection: some View {
        VStack(alignment: .leading, spacing: 8) {
            Button {
                withAnimation(UH.Motion.standard) {
                    showSourcesSection.toggle()
                }
            } label: {
                HStack {
                    Image(systemName: "folder")
                        .foregroundStyle(UH.Palette.muted)
                    Text("Indexed Sources & Documentation")
                        .font(UH.TextStyle.caption.weight(.bold))
                        .foregroundStyle(UH.Palette.secondary)
                    Spacer()
                    Image(systemName: showSourcesSection ? "chevron.up" : "chevron.down")
                        .font(.system(size: 11, weight: .bold))
                        .foregroundStyle(UH.Palette.muted)
                }
            }
            .buttonStyle(.plain)

            if showSourcesSection {
                VStack(alignment: .leading, spacing: 10) {
                    Divider().padding(.vertical, 2)

                    ForEach(sources) { src in
                        HStack(spacing: 8) {
                            Image(systemName: src.type == "pdf" ? "doc.text.fill" : (src.type == "youtube" ? "play.rectangle.fill" : "globe"))
                                .font(.system(size: 13))
                                .foregroundStyle(src.type == "youtube" ? Color.red : UH.Palette.accentInk)
                            Text(src.title)
                                .font(UH.TextStyle.caption)
                                .foregroundStyle(UH.Palette.ink)
                                .lineLimit(1)
                            Spacer()
                            Text(src.type.uppercased())
                                .font(.system(size: 9, weight: .bold, design: .monospaced))
                                .foregroundStyle(UH.Palette.muted)
                        }
                        .padding(.vertical, 4)
                    }

                    // Ingest URL field
                    HStack(spacing: 8) {
                        TextField("Add link: https://uphillathlete.com/...", text: $newLinkInput)
                            .font(UH.TextStyle.caption)
                            .padding(8)
                            .background(UH.Palette.surface, in: RoundedRectangle(cornerRadius: UH.Radius.control))
                            .overlay(RoundedRectangle(cornerRadius: UH.Radius.control).stroke(UH.Palette.line))

                        Button {
                            guard !newLinkInput.trimmingCharacters(in: .whitespaces).isEmpty else { return }
                            Task {
                                isSubmittingLink = true
                                try? await service.addLink(url: newLinkInput)
                                newLinkInput = ""
                                isSubmittingLink = false
                                statusMessage = "Source added to indexing queue"
                            }
                        } label: {
                            Text(isSubmittingLink ? "..." : "Ingest")
                                .font(UH.TextStyle.caption.weight(.bold))
                                .foregroundStyle(Color.white)
                                .padding(.horizontal, 12)
                                .padding(.vertical, 8)
                                .background(UH.Palette.ink, in: RoundedRectangle(cornerRadius: UH.Radius.control))
                        }
                    }
                    .padding(.top, 4)

                    if let msg = statusMessage {
                        Text(msg)
                            .font(UH.TextStyle.disclosure)
                            .foregroundStyle(UH.Palette.accentInk)
                    }
                }
            }
        }
        .trainingCard()
    }

    // MARK: - Loader

    private func loadKnowledgeData() async {
        isLoading = true
        do {
            async let loadedCards = service.fetchCards(topic: nil, lang: AppLanguage.code)
            async let loadedTopics = service.fetchTopics()
            async let loadedSources = service.fetchSources()

            let (c, t, s) = try await (loadedCards, loadedTopics, loadedSources)
            self.cards = c
            self.topics = t.contains("All") ? t : (["All"] + t)
            self.sources = s
            self.dailyCards = Array(c.shuffled().prefix(1))
        } catch {
            // Curated fallback
            self.cards = KnowledgeService.curatedCards
            self.dailyCards = Array(KnowledgeService.curatedCards.shuffled().prefix(1))
        }
        isLoading = false
    }
}
