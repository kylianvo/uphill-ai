import SwiftUI

struct ChatSourcesSheet: View {
    let sources: MessageSourcesResponse
    @Environment(\.dismiss) private var dismiss

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: UH.Space.section) {
                    // Citations Section
                    if !sources.citations.isEmpty {
                        VStack(alignment: .leading, spacing: UH.Space.regular) {
                            Text("Scientific Literature & Principles")
                                .font(UH.TextStyle.sectionTitle)
                                .foregroundStyle(UH.Palette.ink)

                            ForEach(sources.citations) { citation in
                                citationRow(citation)
                            }
                        }
                    }

                    // Evidence Section
                    if !sources.evidence.isEmpty {
                        VStack(alignment: .leading, spacing: UH.Space.regular) {
                            Text("Retrieved Context")
                                .font(UH.TextStyle.sectionTitle)
                                .foregroundStyle(UH.Palette.ink)

                            ForEach(Array(sources.evidence.enumerated()), id: \.offset) { _, ev in
                                evidenceRow(ev)
                            }
                        }
                    }
                }
                .padding(UH.Space.regular)
            }
            .background(UH.Palette.surface.ignoresSafeArea())
            .navigationTitle("Sources & Evidence")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .topBarTrailing) {
                    Button("Done") {
                        dismiss()
                    }
                    .accessibilityIdentifier("chat.sourcesDone")
                    .font(UH.TextStyle.label)
                    .foregroundStyle(UH.Palette.accentInk)
                }
            }
        }
    }

    private func citationRow(_ citation: CitationItem) -> some View {
        VStack(alignment: .leading, spacing: UH.Space.compact) {
            if let book = citation.book {
                Text(book)
                    .font(UH.TextStyle.label)
                    .foregroundStyle(UH.Palette.accentInk)
            }

            if let chapter = citation.chapter {
                Text(chapter)
                    .font(UH.TextStyle.caption)
                    .foregroundStyle(UH.Palette.secondary)
            }

            if let quote = citation.quote, !quote.isEmpty {
                HStack(alignment: .top, spacing: 8) {
                    Rectangle()
                        .fill(UH.Palette.accent)
                        .frame(width: 3)

                    Text(quote)
                        .font(UH.TextStyle.body)
                        .foregroundStyle(UH.Palette.ink)
                        .italic()
                }
                .padding(.vertical, 4)
            }

            if let urlString = citation.url, let url = URL(string: urlString) {
                Link(destination: url) {
                    HStack(spacing: 4) {
                        Image(systemName: "arrow.up.right.square")
                        Text("View Original Source")
                    }
                    .font(UH.TextStyle.caption)
                    .foregroundStyle(UH.Palette.accentInk)
                }
                .padding(.top, 2)
            }
        }
        .uhCard()
    }

    private func evidenceRow(_ ev: JSONValue) -> some View {
        VStack(alignment: .leading, spacing: 6) {
            if let title = ev["title"]?.stringValue {
                Text(title)
                    .font(UH.TextStyle.label)
                    .foregroundStyle(UH.Palette.ink)
            }

            if let content = ev["content"]?.stringValue {
                Text(content)
                    .font(UH.TextStyle.caption)
                    .foregroundStyle(UH.Palette.secondary)
            }
        }
        .uhCard()
    }
}
