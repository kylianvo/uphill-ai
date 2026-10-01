import SwiftUI

struct GoalSheet: View {
    let model: PlanViewModel
    @Environment(\.dismiss) private var dismiss
    @State private var busy = false
    @State private var error: String?
    @State private var confirming = false

    private var targetText: String {
        guard let hours = model.goal?.targetTimeHours else { return "No target set" }
        return "Your target: " + PlanViewModel.formatMinutes(hours * 60)
    }

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: UH.Space.section) {
                    Text(targetText).font(UH.TextStyle.label).foregroundStyle(UH.Palette.secondary)
                    if let tiers = model.goal?.assessment?.goals {
                        VStack(spacing: 0) {
                            tier("Stretch", tiers.a, emphasised: false)
                            tier("Realistic", tiers.b, emphasised: true)
                            tier("Safe", tiers.c, emphasised: false)
                        }
                        .padding(.horizontal, UH.Space.regular).uhCard(padding: 0)
                    } else {
                        Text("We can't estimate a finish time yet.").foregroundStyle(UH.Palette.secondary)
                    }
                    if let assessment = model.goal?.assessment {
                        if !assessment.reasoning.isEmpty {
                            VStack(alignment: .leading, spacing: UH.Space.compact) {
                                ForEach(assessment.reasoning, id: \.self) { Label($0, systemImage: "circle.fill").labelStyle(.titleAndIcon) }
                            }.font(UH.TextStyle.body)
                        }
                        if !assessment.missing.isEmpty {
                            Text("We'd know more with: " + assessment.missing.map { $0.replacingOccurrences(of: "_", with: " ") }.joined(separator: ", "))
                                .font(UH.TextStyle.caption).foregroundStyle(UH.Palette.secondary)
                        }
                    }
                    if let error { Text(error).font(UH.TextStyle.caption).foregroundStyle(UH.Palette.danger) }
                    if let suggestion = model.suggestedMinutes {
                        Button("Set \(PlanViewModel.formatMinutes(suggestion)) as my target") { confirming = true }
                            .buttonStyle(.uhPrimary).disabled(busy)
                    }
                    Button { Task { await check() } } label: {
                        if busy { ProgressView() } else { Text("Check again") }
                    }
                    .buttonStyle(.uhSecondary).disabled(busy)
                    if let assessment = model.goal?.assessment {
                        Text(footer(assessment)).font(UH.TextStyle.caption).foregroundStyle(UH.Palette.muted)
                    }
                }
                .padding(UH.Space.section)
            }
            .background(UH.Palette.surface)
            .navigationTitle("Your goal for \(model.snapshot?.plan.raceName ?? "this race")")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar { Button("Done") { dismiss() } }
            .confirmationDialog("Change your target time to \(model.suggestedMinutes.map(PlanViewModel.formatMinutes) ?? "")?",
                                isPresented: $confirming, titleVisibility: .visible) {
                Button("Change target") { Task { await apply() } }
                Button("Keep \(model.goal?.targetTimeHours.map { PlanViewModel.formatMinutes($0 * 60) } ?? "current")", role: .cancel) {}
            } message: { Text("Your training paces won't change until your next week is built.") }
        }
        .presentationDetents([.medium, .large])
        .presentationBackground(UH.Palette.surface)
    }

    private func tier(_ title: String, _ minutes: Double, emphasised: Bool) -> some View {
        HStack {
            Text(title).font(emphasised ? UH.TextStyle.sectionTitle : UH.TextStyle.body)
            Spacer()
            Text(PlanViewModel.formatMinutes(minutes)).font(UH.TextStyle.metric)
        }
        .frame(minHeight: 52)
        .overlay(alignment: .bottom) { if title != "Safe" { Divider() } }
        .accessibilityElement(children: .combine)
    }

    private func footer(_ assessment: GoalAssessment) -> String {
        let source = assessment.engine == "none" || assessment.engine == nil ? "Estimated from your training so far" : "Estimated from your race history"
        guard let created = assessment.createdAt, let date = (try? Date(created, strategy: Date.ISO8601FormatStyle(includingFractionalSeconds: true))) ?? (try? Date(created, strategy: .iso8601)) else { return source }
        return source + " \u{00B7} " + date.formatted(.dateTime.day().month(.abbreviated))
    }

    private func check() async {
        busy = true; error = nil
        error = await model.reassessGoal()
        busy = false
    }

    private func apply() async {
        busy = true; error = nil
        error = await model.applySuggestedGoal()
        busy = false
    }
}
