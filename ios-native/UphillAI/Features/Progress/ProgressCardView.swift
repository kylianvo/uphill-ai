import SwiftUI

/// The Apple Health summary-card anatomy: symbol and name in emerald, the as-of date, a large rounded
/// number, a compact chart and one plain sentence.
struct ProgressCardView: View {
    let card: ProgressCard

    var body: some View {
        VStack(alignment: .leading, spacing: UH.Space.small) {
            HStack {
                Label(ProgressText.title(card.key), systemImage: ProgressText.symbol(card.key))
                    .font(UH.TextStyle.label)
                    .foregroundStyle(UH.Palette.accentInk)
                Spacer()
                if let asOf = card.asOf, let date = ProgressPoint.day.date(from: asOf) {
                    Text(date, format: .dateTime.day().month(.abbreviated))
                        .font(UH.TextStyle.caption)
                        .foregroundStyle(UH.Palette.muted)
                }
            }
            if let value = ProgressText.value(card) {
                HStack(alignment: .firstTextBaseline, spacing: 4) {
                    Text(value.number)
                        .font(.system(.largeTitle, design: .rounded).weight(.semibold).monospacedDigit())
                        .foregroundStyle(UH.Palette.ink)
                    Text(value.unit)
                        .font(UH.TextStyle.label)
                        .foregroundStyle(UH.Palette.secondary)
                }
                .accessibilityElement(children: .combine)
            }
            if !card.points.isEmpty {
                ProgressChart(card: card)
            }
            Text(ProgressText.note(card))
                .font(UH.TextStyle.body)
                .foregroundStyle(card.key == "coach_read" ? UH.Palette.ink : UH.Palette.secondary)
                .fixedSize(horizontal: false, vertical: true)
        }
        .uhCard()
    }
}
