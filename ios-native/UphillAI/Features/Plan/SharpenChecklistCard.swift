import SwiftUI

/// Phase 2b design-baseline.md: one follow-up per row, no missing-data alerts.
struct SharpenChecklistCard: View {
    let user: User
    let plan: Plan
    let onOpen: (TrainingDestination) -> Void
    @State private var hidden = false
    private var key: String { "UPHILL_SHARPEN_HIDDEN_\(plan.id)" }
    private var items: [SharpenItem] { SharpenChecklist.items(user: user, plan: plan) }

    var body: some View {
        Group {
        if !hidden && items.contains(where: { !$0.done }) {
            VStack(alignment: .leading, spacing: UH.Space.small) {
                Text("Sharpen your plan").font(UH.TextStyle.sectionTitle)
                Text("\(items.filter(\.done).count) of \(items.count) done · each one makes your next week more accurate")
                    .font(UH.TextStyle.caption).foregroundStyle(UH.Palette.secondary)
                ForEach(items) { item in
                    Button { onOpen(item.destination) } label: {
                        HStack(spacing: UH.Space.small) {
                            Image(systemName: item.done ? "checkmark.circle.fill" : "circle")
                                .foregroundStyle(item.done ? UH.Palette.accentInk : UH.Palette.muted)
                            Text(item.title).multilineTextAlignment(.leading)
                            Spacer(minLength: 0)
                            Image(systemName: "chevron.right")
                        }.frame(minHeight: 44)
                    }.buttonStyle(.plain).accessibilityValue(item.done ? "Done" : "Not done")
                }
                Button("Hide for now") {
                    UserDefaults.standard.set(true, forKey: key)
                    hidden = true
                }.frame(minHeight: 44).font(UH.TextStyle.caption)
            }.padding(UH.Space.regular).uhCard()
        }
        }.task(id: plan.id) { hidden = UserDefaults.standard.bool(forKey: key) }
    }
}
