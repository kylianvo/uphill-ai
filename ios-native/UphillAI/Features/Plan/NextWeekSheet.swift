import SwiftUI

struct NextWeekSheet: View {
    let model: PlanViewModel
    let offer: NextWeekOffer
    @Environment(\.dismiss) private var dismiss
    @State private var rpe: Int?
    @State private var notes = ""
    @State private var isSubmitting = false
    @State private var confirmMessage: String?
    @State private var confirming = false
    @State private var error: String?

    var body: some View {
        NavigationStack {
            Form {
                Section {
                    Stepper(value: Binding(get: { rpe ?? 5 }, set: { rpe = $0 }), in: 1...10) {
                        HStack {
                            Text("Effort (RPE)")
                            Spacer()
                            Text(rpe.map(String.init) ?? "Not set").foregroundStyle(UH.Palette.secondary)
                        }
                    }
                    TextField("Anything Coach Uphill should know?", text: $notes, axis: .vertical)
                        .lineLimit(2...5)
                }
                .listRowBackground(UH.Palette.card)
                Section {
                    if let error { Text(error).font(UH.TextStyle.caption).foregroundStyle(UH.Palette.danger) }
                    Button { Task { await submit(override: false) } } label: {
                        if isSubmitting { ProgressView() } else { Text(offer.title) }
                    }
                    .buttonStyle(.uhPrimary).disabled(isSubmitting).accessibilityIdentifier("nextweek.submit")
                    .listRowBackground(Color.clear).listRowInsets(EdgeInsets())
                }
            }
            .listSectionSpacing(UH.Space.section)
            .scrollContentBackground(.hidden)
            .background(UH.Palette.surface)
            .navigationTitle("How did this week go?")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar { Button("Cancel") { dismiss() } }
            .confirmationDialog("Build the next week anyway?", isPresented: $confirming, titleVisibility: .visible) {
                Button("Build anyway") { Task { await submit(override: true) } }
                Button("Not yet", role: .cancel) {}
            } message: { Text(confirmMessage ?? "") }
        }
        .presentationDetents([.medium, .large])
        .presentationBackground(UH.Palette.surface)
    }

    private func submit(override: Bool) async {
        isSubmitting = true
        error = nil
        defer { isSubmitting = false }
        switch await model.buildNextWeek(rpe: rpe, notes: notes, override: override) {
        case .started: dismiss()
        case .needsConfirmation(let message): confirmMessage = message; confirming = true
        case .failed(let message): error = message
        }
    }
}
