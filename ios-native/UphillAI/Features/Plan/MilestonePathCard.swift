import SwiftUI

/// A beginner's path to First 5K / First 10K: the next milestone, one tap to confirm it, and the full list.
struct MilestonePathCard: View {
    let model: PlanViewModel
    @State private var confirming = false
    @State private var showAll = false

    var body: some View {
        if let milestones = model.beginnerMilestones {
            VStack(alignment: .leading, spacing: 6) {
                Text(L("Your path").uppercased())
                    .font(UH.TextStyle.eyebrow).tracking(0.5).foregroundStyle(UH.Palette.secondary)
                Text(verbatim: model.beginnerHeaderText ?? milestones.targetTitle)
                    .font(UH.TextStyle.sectionTitle).foregroundStyle(UH.Palette.ink).lineLimit(2).minimumScaleFactor(0.8)
                if let next = milestones.next {
                    Text(verbatim: "→ " + next.title).font(UH.TextStyle.label).foregroundStyle(UH.Palette.ink)
                    Text(verbatim: next.typicalWeeksText).font(UH.TextStyle.caption).foregroundStyle(UH.Palette.secondary)
                }
                Spacer(minLength: 0)
                HStack(spacing: UH.Space.regular) {
                    if let next = milestones.next {
                        Button("I did it") { confirming = true }
                            .font(UH.TextStyle.label).foregroundStyle(UH.Palette.accentInk)
                            .accessibilityIdentifier("milestone.didit")
                            .confirmationDialog(next.title, isPresented: $confirming, titleVisibility: .visible) {
                                Button("Yes, mark it") { Task { await model.markMilestone(next.key) } }
                                Button("Not yet", role: .cancel) {}
                            }
                    }
                    if milestones.canUpgrade {
                        Button("Next: First 10K") { Task { await model.upgradeMilestoneTarget(clearEvent: milestones.hasEvent) } }
                            .font(UH.TextStyle.label).foregroundStyle(UH.Palette.accentInk)
                            .accessibilityIdentifier("milestone.upgrade")
                    }
                    Spacer()
                    Button("All milestones") { showAll = true }
                        .font(UH.TextStyle.caption).foregroundStyle(UH.Palette.secondary)
                        .accessibilityIdentifier("milestone.all")
                }
            }
            .padding(14)
            .frame(width: 315, height: 184, alignment: .topLeading)
            .background(UH.Palette.card, in: RoundedRectangle(cornerRadius: UH.Radius.landing))
            .sheet(isPresented: $showAll) { MilestoneListSheet(model: model) }
            .accessibilityIdentifier("plan.milestones")
        }
    }
}

/// Every milestone on the ladder, with undo for the ones reached.
struct MilestoneListSheet: View {
    let model: PlanViewModel
    @Environment(\.dismiss) private var dismiss

    var body: some View {
        NavigationStack {
            List {
                if let milestones = model.beginnerMilestones {
                    Section {
                        ForEach(milestones.items) { item in
                            HStack(spacing: UH.Space.small) {
                                Image(systemName: item.isReached ? "checkmark.circle.fill" : (item.key == milestones.nextKey ? "arrow.right.circle" : "circle"))
                                    .foregroundStyle(item.isReached ? UH.Palette.accentInk : UH.Palette.muted)
                                VStack(alignment: .leading, spacing: 2) {
                                    Text(verbatim: item.title).font(UH.TextStyle.label)
                                    if !item.isReached { Text(verbatim: item.typicalWeeksText).font(UH.TextStyle.caption).foregroundStyle(UH.Palette.secondary) }
                                }
                                Spacer()
                                if item.isReached {
                                    Button("Undo") { Task { await model.undoMilestone(item.key) } }
                                        .font(UH.TextStyle.caption).buttonStyle(.borderless)
                                        .accessibilityLabel(L("Undo %@", item.title))
                                }
                            }
                        }
                    } footer: {
                        Text("Repeating a week is normal. You move on when you're ready.")
                    }
                }
            }
            .navigationTitle(L("Your path"))
            .navigationBarTitleDisplayMode(.inline)
            .toolbar { ToolbarItem(placement: .confirmationAction) { Button("Done") { dismiss() } } }
        }
    }
}
