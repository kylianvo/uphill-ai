import SwiftUI

/// Redesigned Goal Sheet with 2-column small stat tiles for goal context and anchor list.
struct GoalSheet: View {
    let model: PlanViewModel
    @Environment(\.dismiss) private var dismiss
    @State private var busy = false
    @State private var error: String?
    @State private var confirming = false
    @State private var isContextExpanded = true

    private var targetText: String {
        guard let hours = model.goal?.targetTimeHours else { return L("No target set") }
        return L("Your target: ") + PlanViewModel.formatMinutes(hours * 60)
    }

    private var contextGroups: [GoalContext.Group] {
        if let groups = model.goal?.assessment?.context?.groups, !groups.isEmpty {
            return groups
        }
        var rows: [GoalContext.Row] = []
        if let km = model.snapshot?.plan.courseDistanceKm {
            rows.append(GoalContext.Row(label: L("Distance"), value: "\(Int(km.rounded())) km"))
        }
        if let dPlus = model.snapshot?.plan.courseElevationGainM {
            rows.append(GoalContext.Row(label: "D+", value: "\(Int(dPlus.rounded())) m"))
        }
        rows.append(GoalContext.Row(label: L("Course profile"), value: L("Estimated")))
        if let hours = model.goal?.targetTimeHours ?? model.snapshot?.plan.targetTimeHours {
            rows.append(GoalContext.Row(label: L("Time Target"), value: PlanViewModel.formatMinutes(hours * 60)))
        }
        if !rows.isEmpty {
            return [GoalContext.Group(title: L("Race"), rows: rows)]
        }
        return []
    }

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: UH.Space.section) {
                    // Header with race name and target
                    VStack(alignment: .leading, spacing: 4) {
                        Text(model.snapshot?.plan.raceName ?? L("Race Goal"))
                            .font(UH.TextStyle.screenTitle)
                            .foregroundStyle(UH.Palette.ink)
                        Text(targetText)
                            .font(UH.TextStyle.label)
                            .foregroundStyle(UH.Palette.secondary)
                    }

                    // Tiers card
                    if let tiers = model.goal?.assessment?.goals {
                        VStack(spacing: 0) {
                            tier(L("Stretch"), tiers.a, emphasised: false)
                            tier(L("Realistic"), tiers.b, emphasised: true)
                            tier(L("Safe"), tiers.c, emphasised: false)
                        }
                        .padding(.horizontal, UH.Space.regular)
                        .trainingCard(padding: 0)
                    } else {
                        Text("We can't estimate a finish time yet.")
                            .foregroundStyle(UH.Palette.secondary)
                            .trainingCard()
                    }

                    // Goal Context & Reasoning
                    if let assessment = model.goal?.assessment {
                        if !assessment.reasoning.isEmpty {
                            VStack(alignment: .leading, spacing: UH.Space.compact) {
                                ForEach(assessment.reasoning, id: \.self) { line in
                                    Label(line, systemImage: "circle.fill")
                                        .font(UH.TextStyle.body)
                                        .foregroundStyle(UH.Palette.ink)
                                }
                            }
                        }

                        let groups = contextGroups
                        if !groups.isEmpty || !assessment.anchors.isEmpty {
                            DisclosureGroup("What this is based on", isExpanded: $isContextExpanded) {
                                VStack(alignment: .leading, spacing: UH.Space.regular) {
                                    // 2-column stat tiles grid for context groups
                                    ForEach(groups) { group in
                                        VStack(alignment: .leading, spacing: UH.Space.compact) {
                                            Text(group.title)
                                                .font(UH.TextStyle.sectionTitle)
                                                .foregroundStyle(UH.Palette.ink)

                                            LazyVGrid(columns: [GridItem(.flexible()), GridItem(.flexible())], spacing: UH.Space.small) {
                                                ForEach(group.rows) { row in
                                                    VStack(alignment: .leading, spacing: 4) {
                                                        Text(row.label.uppercased())
                                                            .font(.system(size: 10, weight: .bold))
                                                            .foregroundStyle(UH.Palette.secondary)
                                                        Text(row.value)
                                                            .font(.system(.subheadline, design: .monospaced).weight(.bold))
                                                            .foregroundStyle(UH.Palette.ink)
                                                    }
                                                    .padding(UH.Space.small)
                                                    .frame(maxWidth: .infinity, alignment: .leading)
                                                    .background(UH.Palette.surface, in: RoundedRectangle(cornerRadius: UH.Radius.control))
                                                    .overlay(RoundedRectangle(cornerRadius: UH.Radius.control).stroke(UH.Palette.line, lineWidth: 1))
                                                }
                                            }
                                        }
                                    }

                                    // Calculation anchors list
                                    if !assessment.anchors.isEmpty {
                                        VStack(alignment: .leading, spacing: UH.Space.compact) {
                                            Text("Calculation Anchors")
                                                .font(UH.TextStyle.sectionTitle)
                                                .foregroundStyle(UH.Palette.ink)

                                            VStack(spacing: UH.Space.small) {
                                                ForEach(assessment.anchors) { anchor in
                                                    HStack {
                                                        Text(anchor.methodLabel)
                                                            .font(UH.TextStyle.body)
                                                            .foregroundStyle(UH.Palette.ink)
                                                        Spacer()
                                                        Text(PlanViewModel.formatMinutes(anchor.minutes))
                                                            .font(.system(.body, design: .monospaced).weight(.bold))
                                                            .foregroundStyle(UH.Palette.accentInk)
                                                    }
                                                    .padding(UH.Space.small)
                                                    .background(UH.Palette.surface, in: RoundedRectangle(cornerRadius: UH.Radius.control))
                                                    .overlay(RoundedRectangle(cornerRadius: UH.Radius.control).stroke(UH.Palette.line, lineWidth: 1))
                                                }
                                            }
                                        }
                                    }
                                }
                                .padding(.top, UH.Space.regular)
                            }
                            .tint(UH.Palette.accentInk)
                            .trainingCard()
                        }

                        if !assessment.missing.isEmpty {
                            Text("We'd know more with: " + assessment.missing.map { $0.replacingOccurrences(of: "_", with: " ") }.joined(separator: ", "))
                                .font(UH.TextStyle.caption)
                                .foregroundStyle(UH.Palette.secondary)
                                .padding(.horizontal, 4)
                        }
                    }

                    if let error {
                        Text(error).font(UH.TextStyle.caption).foregroundStyle(UH.Palette.danger)
                    }

                    if let suggestion = model.suggestedMinutes {
                        Button("Set \(PlanViewModel.formatMinutes(suggestion)) as my target") { confirming = true }
                            .buttonStyle(.uhPrimary).disabled(busy)
                    }

                    Button {
                        Task { await check() }
                    } label: {
                        if busy { ProgressView() } else { Text("Check again") }
                    }
                    .buttonStyle(.uhSecondary).disabled(busy)

                    if let assessment = model.goal?.assessment {
                        Text(footer(assessment)).font(UH.TextStyle.caption).foregroundStyle(UH.Palette.muted)
                            .frame(maxWidth: .infinity, alignment: .center)
                    }
                }
                .padding(UH.Space.section)
            }
            .background(UH.Palette.surface)
            .navigationTitle("Goal Assessment")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar { Button("Done") { dismiss() } }
            .confirmationDialog("Change your target time to \(model.suggestedMinutes.map(PlanViewModel.formatMinutes) ?? "")?",
                                isPresented: $confirming, titleVisibility: .visible) {
                Button("Change target") { Task { await apply() } }
                Button("Keep \(model.goal?.targetTimeHours.map { PlanViewModel.formatMinutes($0 * 60) } ?? "current")", role: .cancel) {}
            } message: { Text("Your training paces won't change until your next week is built.") }
        }
        .presentationDetents([.large])
        .presentationBackground(UH.Palette.surface)
    }

    private func tier(_ title: String, _ minutes: Double, emphasised: Bool) -> some View {
        HStack {
            Text(title).font(emphasised ? UH.TextStyle.sectionTitle : UH.TextStyle.body)
            Spacer()
            Text(PlanViewModel.formatMinutes(minutes)).font(UH.TextStyle.metric)
        }
        .frame(minHeight: 52)
        .overlay(alignment: .bottom) { if title != L("Safe") { Divider() } }
        .accessibilityElement(children: .combine)
    }

    private func footer(_ assessment: GoalAssessment) -> String {
        let source = assessment.engine == "none" || assessment.engine == nil ? L("Estimated from your training so far") : L("Estimated from your race history")
        guard let created = assessment.createdAt, let date = (try? Date(created, strategy: Date.ISO8601FormatStyle(includingFractionalSeconds: true))) ?? (try? Date(created, strategy: .iso8601)) else { return source }
        return source + " · " + date.formatted(Date.FormatStyle(locale: AppLanguage.current.locale).day().month(.abbreviated))
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
