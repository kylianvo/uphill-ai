import SwiftUI

/// The plan's races, opened from Manage: the Next races card with its add, edit and debrief sheets.
struct RacesSheet: View {
    let model: PlanViewModel
    var app: AppModel? = nil
    @State private var raceSheet: RaceSheet?
    @Environment(\.dismiss) private var dismiss

    var body: some View {
        NavigationStack {
            ScrollView {
                NextRacesCard(model: model,
                              onAdd: { raceSheet = .add },
                              onOpen: { raceSheet = .edit($0) },
                              onDebrief: { raceSheet = .debrief($0) })
                    .padding(UH.Space.regular)
            }
            .background(UH.Palette.surface)
            .navigationTitle(L("Next races"))
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .confirmationAction) {
                    Button("Done") { dismiss() }
                }
            }
            .sheet(item: $raceSheet) { $0.content(model, app: app) }
        }
        .presentationDetents([.medium, .large])
        .presentationBackground(UH.Palette.surface)
        .accessibilityIdentifier("races.sheet")
    }
}
