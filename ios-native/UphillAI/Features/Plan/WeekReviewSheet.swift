import SwiftUI

struct WeekReviewSheet: View {
    let model: PlanViewModel
    let week: Int
    @Environment(\.dismiss) private var dismiss
    @State private var phase = Phase.loading

    private enum Phase { case loading, loaded(WeekReview), failed(String) }

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: UH.Space.section) {
                    switch phase {
                    case .loading: placeholder.redacted(reason: .placeholder)
                    case .loaded(let review): content(review)
                    case .failed(let message):
                        VStack(spacing: UH.Space.regular) {
                            Text(message).foregroundStyle(UH.Palette.secondary).multilineTextAlignment(.center)
                            Button("Try again") { Task { await load() } }.buttonStyle(.uhPrimary).frame(maxWidth: 220)
                        }.frame(maxWidth: .infinity)
                    }
                }
                .padding(UH.Space.section)
            }
            .background(UH.Palette.surface)
            .navigationTitle("Week \(week) review")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar { Button("Done") { dismiss() } }
            .task { await load() }
        }
        .presentationDetents([.medium, .large])
        .presentationBackground(UH.Palette.surface)
    }

    private var placeholder: some View {
        VStack(alignment: .leading, spacing: UH.Space.regular) {
            Circle().frame(width: 96, height: 96)
            Text("Week summary text that is still loading from the coach.")
            ForEach(0..<3, id: \.self) { _ in Text("Easy Run on Wednesday").frame(maxWidth: .infinity, alignment: .leading) }
        }
    }

    private func content(_ review: WeekReview) -> some View {
        let pct = review.checkboxCompletionPct ?? review.completionPct
        return VStack(alignment: .leading, spacing: UH.Space.section) {
            HStack(spacing: UH.Space.regular) {
                Gauge(value: min(max(pct, 0), 100), in: 0...100) { Text("Sessions done") } currentValueLabel: { Text("\(Int(pct))%") }
                    .gaugeStyle(.accessoryCircularCapacity).tint(UH.Palette.accent).scaleEffect(1.3).frame(width: 72, height: 72)
                Text("sessions done").font(UH.TextStyle.label)
            }
            if let summary = review.narrative?.summary { Text(summary).font(UH.TextStyle.body) }
            if let items = review.narrative?.highlights, !items.isEmpty {
                list("Went well", items, symbol: "checkmark", tint: UH.Palette.accentInk)
            }
            if let items = review.narrative?.watch, !items.isEmpty {
                list("Keep an eye on", items, symbol: "exclamationmark.triangle", tint: UH.Palette.secondary)
            }
            VStack(alignment: .leading, spacing: UH.Space.small) {
                ForEach(review.perWorkout) { entry in
                    HStack(alignment: .firstTextBaseline) {
                        VStack(alignment: .leading, spacing: 2) {
                            Text(entry.title ?? entry.type ?? "Workout").font(UH.TextStyle.label)
                            if let day = entry.dayOfWeek { Text(day).font(UH.TextStyle.caption).foregroundStyle(UH.Palette.secondary) }
                        }
                        Spacer()
                        Text(Self.stateLabel(entry.actual.state)).font(UH.TextStyle.caption).foregroundStyle(UH.Palette.secondary)
                    }
                    .frame(minHeight: 44)
                }
            }
            .padding(UH.Space.regular).uhCard()
        }
    }

    private func list(_ title: String, _ items: [String], symbol: String, tint: Color) -> some View {
        VStack(alignment: .leading, spacing: UH.Space.compact) {
            Text(title).font(UH.TextStyle.sectionTitle)
            ForEach(items, id: \.self) { Label($0, systemImage: symbol).symbolRenderingMode(.monochrome).foregroundStyle(tint == UH.Palette.accentInk ? UH.Palette.ink : tint).tint(tint) }
        }
    }

    static func stateLabel(_ state: String) -> String {
        switch state {
        case "matched": "Synced"
        case "checkbox_only": "Done"
        case "missed": "Missed"
        default: "Not yet"
        }
    }

    private func load() async {
        phase = .loading
        switch await model.weekReview(week) {
        case .success(let review): phase = .loaded(review)
        case .failure(let error): phase = .failed(error.userMessage)
        }
    }
}
