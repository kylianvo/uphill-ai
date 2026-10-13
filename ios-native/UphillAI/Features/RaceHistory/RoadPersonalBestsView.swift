import SwiftUI

struct RoadPersonalBestsView: View {
    let summary: HistorySummary
    var onSelect: ((Int) -> Void)? = nil
    private let distances = [("5k", "5 km"), ("10k", "10 km"), ("hm", "Half marathon"), ("fm", "Marathon")]

    private func best(_ key: String) -> PRTime? {
        if let values = summary.roadPrs { return values[key] ?? nil }
        return key == "hm" ? summary.roadHmPr : key == "fm" ? summary.roadFmPr : nil
    }

    var body: some View {
        VStack(alignment: .leading, spacing: UH.Space.small) {
            Text("Road personal bests").font(UH.TextStyle.sectionTitle).foregroundStyle(UH.Palette.ink)
            LazyVGrid(columns: [GridItem(.flexible()), GridItem(.flexible())], spacing: UH.Space.small) {
                ForEach(distances, id: \.0) { item in
                    let (key, title) = item
                    let record = best(key)
                    Button {
                        if let id = record?.resultId { onSelect?(id) }
                    } label: {
                        VStack(alignment: .leading, spacing: UH.Space.compact) {
                            HStack(alignment: .firstTextBaseline) {
                                Text(title).font(UH.TextStyle.caption).foregroundStyle(UH.Palette.secondary)
                                Spacer(minLength: 4)
                                if record != nil { Image(systemName: "medal.fill").foregroundStyle(UH.Palette.accentInk) }
                            }
                            Text(record.map { DistanceBadge.formatTime($0.timeSec) } ?? "—")
                                .font(UH.TextStyle.metric).foregroundStyle(UH.Palette.ink)
                                .accessibilityIdentifier("race.pb.\(key)")
                            Text(record?.date ?? (record == nil ? "No confirmed result" : "Recorded finish"))
                                .font(UH.TextStyle.caption).foregroundStyle(UH.Palette.secondary)
                        }
                        .frame(maxWidth: .infinity, alignment: .leading)
                        .trainingCard(padding: UH.Space.regular, radius: UH.Radius.panel)
                    }
                    .buttonStyle(.plain)
                    .disabled(record?.resultId == nil || onSelect == nil)
                }
            }
        }
    }
}
