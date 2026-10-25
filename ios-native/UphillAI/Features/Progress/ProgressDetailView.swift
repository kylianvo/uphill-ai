import SwiftUI

/// A card's larger chart with axes, a 4W / 3M range and what the measure means.
struct ProgressDetailView: View {
    let card: ProgressCard
    let model: ProgressViewModel

    @State private var days = 28
    @State private var shown: ProgressCard?

    /// Weekly cards don't change with the range.
    private var hasRange: Bool { ["sleep", "resting_hr", "hrv", "load"].contains(card.key) }

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: UH.Space.section) {
                if hasRange {
                    Picker(L("Range"), selection: $days) {
                        Text(L("4W")).tag(28)
                        Text(L("3M")).tag(90)
                    }
                    .pickerStyle(.segmented)
                }
                let current = shown ?? card
                VStack(alignment: .leading, spacing: UH.Space.small) {
                    if let value = ProgressText.value(current) {
                        HStack(alignment: .firstTextBaseline, spacing: 4) {
                            Text(value.number).font(.system(.largeTitle, design: .rounded).weight(.semibold).monospacedDigit())
                            Text(value.unit).font(UH.TextStyle.label).foregroundStyle(UH.Palette.secondary)
                        }
                    }
                    ProgressChart(card: current, detailed: true)
                    Text(ProgressText.note(current)).foregroundStyle(UH.Palette.secondary)
                    if let source = current.source {
                        Text(L("Source: %@", deviceSourceName(source)))
                            .font(UH.TextStyle.caption).foregroundStyle(UH.Palette.muted)
                    }
                }
                .uhCard()
                VStack(alignment: .leading, spacing: UH.Space.compact) {
                    Text(L("What this means")).font(UH.TextStyle.sectionTitle)
                    Text(ProgressText.explanation(card.key)).foregroundStyle(UH.Palette.secondary)
                }
            }
            .padding(UH.Space.regular)
        }
        .background(Color(.systemGroupedBackground))
        .navigationTitle(ProgressText.title(card.key))
        .navigationBarTitleDisplayMode(.inline)
        .task(id: days) {
            guard hasRange else { return }
            shown = days == 28 ? card : (try? await model.detail(days: days))?.card(card.key)
        }
    }
}
