import SwiftUI

struct KnowledgeDetailScreen: View {
    let service: any KnowledgeServicing
    let cardID: Int
    let language: String
    var onDisplayed: () -> Void = {}
    @State private var card: KnowledgeCardModel?
    @State private var error: String?

    var body: some View {
        ScrollView {
            if let card { KnowledgeCardView(card: card).padding() }
            else if let error {
                ContentUnavailableView {
                    Label("Knowledge card unavailable", systemImage: "book.closed")
                } description: { Text(error) } actions: {
                    Button("Try again") { Task { await load() } }
                }
            } else { ProgressView().padding() }
        }
        .navigationTitle("Knowledge Hub")
        .task { await load() }
    }

    private func load() async {
        do {
            card = try await service.fetchCard(id: cardID, lang: language)
            error = nil
            onDisplayed()
            try? await service.markOpened(id: cardID, lang: language)
        } catch { self.error = L("This card is unavailable. Check your connection and try again.") }
    }
}
