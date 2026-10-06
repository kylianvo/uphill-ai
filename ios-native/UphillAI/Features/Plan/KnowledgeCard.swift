import SwiftUI

struct KnowledgeCardModel: Decodable, Sendable, Identifiable, Equatable {
    let id: Int
    let chapterTitle: String
    let summary: String
    let keyPoints: [String]
    let tags: [String]
    let topic: String
    let sourceLabel: String?

    init(id: Int, chapterTitle: String, summary: String, keyPoints: [String] = [], tags: [String] = [], topic: String = "Training", sourceLabel: String? = nil) {
        self.id = id
        self.chapterTitle = chapterTitle
        self.summary = summary
        self.keyPoints = keyPoints
        self.tags = tags
        self.topic = topic
        self.sourceLabel = sourceLabel
    }

    private enum CodingKeys: String, CodingKey {
        case id, chapterTitle, summary, keyPoints, tags, topic, sourceLabel
    }

    init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        id = try c.decode(Int.self, forKey: .id)
        chapterTitle = try c.decode(String.self, forKey: .chapterTitle)
        summary = try c.decode(String.self, forKey: .summary)
        keyPoints = try c.decodeIfPresent([String].self, forKey: .keyPoints) ?? []
        tags = try c.decodeIfPresent([String].self, forKey: .tags) ?? []
        topic = try c.decodeIfPresent(String.self, forKey: .topic) ?? "Training"
        sourceLabel = try c.decodeIfPresent(String.self, forKey: .sourceLabel)
    }
}

struct KnowledgeCardsResponse: Decodable, Sendable {
    let cards: [KnowledgeCardModel]
}

struct KnowledgeCardView: View {
    let card: KnowledgeCardModel
    @State private var isExpanded = false

    private var topicColor: Color {
        switch card.topic.lowercased() {
        case "training": Color(red: 0.23, green: 0.51, blue: 0.96)
        case "nutrition": Color(red: 0.06, green: 0.72, blue: 0.51)
        case "recovery": Color(red: 0.55, green: 0.36, blue: 0.96)
        case "pacing": Color(red: 0.96, green: 0.62, blue: 0.04)
        case "mindset": Color(red: 0.93, green: 0.28, blue: 0.60)
        case "gear": Color(red: 0.08, green: 0.72, blue: 0.65)
        default: UH.Palette.accentInk
        }
    }

    private var topicIcon: String {
        switch card.topic.lowercased() {
        case "training": "mountain.2.fill"
        case "nutrition": "fork.knife"
        case "recovery": "bed.double.fill"
        case "pacing": "stopwatch.fill"
        case "mindset": "brain.head.profile"
        case "gear": "backpack.fill"
        default: "book.fill"
        }
    }

    var body: some View {
        VStack(alignment: .leading, spacing: UH.Space.small) {
            // Header Row: Topic Badge & Chevron
            HStack {
                HStack(spacing: 5) {
                    Image(systemName: topicIcon)
                        .font(.system(size: 10, weight: .bold))
                    Text(card.topic.uppercased())
                        .font(.system(size: 10, weight: .bold, design: .monospaced))
                        .tracking(0.5)
                }
                .foregroundStyle(topicColor)
                .padding(.horizontal, 8)
                .padding(.vertical, 3)
                .background(topicColor.opacity(0.12), in: Capsule())

                Spacer()

                Image(systemName: isExpanded ? "chevron.up" : "chevron.down")
                    .font(.system(size: 11, weight: .bold))
                    .foregroundStyle(UH.Palette.muted)
            }

            // Chapter Title
            Text(card.chapterTitle)
                .font(UH.TextStyle.sectionTitle)
                .foregroundStyle(UH.Palette.ink)
                .fixedSize(horizontal: false, vertical: true)

            // Summary
            Text(card.summary)
                .font(UH.TextStyle.caption)
                .foregroundStyle(UH.Palette.secondary)
                .lineSpacing(2)
                .fixedSize(horizontal: false, vertical: true)

            // Expanded Key Points
            if isExpanded && !card.keyPoints.isEmpty {
                VStack(alignment: .leading, spacing: 6) {
                    ForEach(card.keyPoints, id: \.self) { point in
                        HStack(alignment: .firstTextBaseline, spacing: 7) {
                            Circle()
                                .fill(topicColor)
                                .frame(width: 4, height: 4)
                                .padding(.top, 4)
                            Text(point)
                                .font(UH.TextStyle.caption)
                                .foregroundStyle(UH.Palette.ink)
                                .fixedSize(horizontal: false, vertical: true)
                        }
                    }
                }
                .padding(.top, 4)
            }

            // Expanded Tags
            if isExpanded && !card.tags.isEmpty {
                HStack(spacing: 5) {
                    ForEach(card.tags, id: \.self) { tag in
                        Text("#\(tag)")
                            .font(.system(size: 10, weight: .medium, design: .monospaced))
                            .foregroundStyle(UH.Palette.muted)
                            .padding(.horizontal, 6)
                            .padding(.vertical, 2)
                            .background(UH.Palette.surface, in: Capsule())
                            .overlay(Capsule().stroke(UH.Palette.line, lineWidth: 1))
                    }
                }
                .padding(.top, 4)
            }
        }
        .trainingCard()
        .contentShape(Rectangle())
        .onTapGesture {
            withAnimation(.spring(response: 0.3, dampingFraction: 0.8)) {
                isExpanded.toggle()
            }
        }
        .accessibilityIdentifier("plan.knowledgeCard")
    }
}
