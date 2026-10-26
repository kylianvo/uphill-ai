import SwiftUI

/// Redesigned Goal Sheet with 2-column small stat tiles for goal context and anchor list.
struct GoalSheet: View {
    let model: PlanViewModel
    @Environment(\.dismiss) private var dismiss
    @State private var busy = false
    @State private var error: String?
    /// A goal the athlete tapped to make their target; A goes through its own check first.
    @State private var choosing: GoalChoice?
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

                    // One goal with two backups: B is what the plan is built for
                    if let tiers = model.goal?.assessment?.goals {
                        VStack(spacing: 0) {
                            tier(.a, tiers.a)
                            Divider()
                            tier(.b, tiers.b)
                            Divider()
                            tier(.c, tiers.c)
                        }
                        .padding(.horizontal, UH.Space.regular)
                        .trainingCard(padding: 0)
                        .accessibilityIdentifier("goal.ladder")
                    } else {
                        Text("We can't estimate a finish time yet.")
                            .foregroundStyle(UH.Palette.secondary)
                            .trainingCard()
                    }

                    GoalPathRow(path: model.goal?.path)

                    GoalPlanCheckCard(feasibility: model.goal?.feasibility, assessment: model.goal?.assessment)

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
            .sheet(item: $choosing.filtered { $0.tier == .a }) { choice in
                ChooseAGoalSheet(minutes: choice.minutes, feasibility: model.goal?.aFeasibility) {
                    choosing = nil
                    Task { await apply(choice.minutes) }
                }
            }
            .confirmationDialog(L("Change your target time to %@?", choosing.map { PlanViewModel.formatMinutes($0.minutes) } ?? ""),
                                isPresented: Binding(get: { choosing != nil && choosing?.tier != .a }, set: { if !$0 { choosing = nil } }),
                                titleVisibility: .visible) {
                Button("Change target") { if let choice = choosing { Task { await apply(choice.minutes) } } }
                Button("Keep \(model.goal?.targetTimeHours.map { PlanViewModel.formatMinutes($0 * 60) } ?? "current")", role: .cancel) {}
            } message: { Text("Your training paces won't change until your next week is built.") }
        }
        .presentationDetents([.large])
        .presentationBackground(UH.Palette.surface)
    }

    private func tier(_ tier: GoalChoice.Tier, _ minutes: Double) -> some View {
        let target = model.goal?.targetTimeHours.map { abs($0 * 60 - minutes) / minutes <= 0.03 } ?? false
        return Button {
            if !target { choosing = GoalChoice(tier: tier, minutes: minutes) }
        } label: {
            HStack(spacing: UH.Space.small) {
                VStack(alignment: .leading, spacing: 2) {
                    Text(verbatim: tier.title)
                        .font(tier == .b ? UH.TextStyle.sectionTitle : UH.TextStyle.body)
                        .foregroundStyle(UH.Palette.ink)
                    Text(verbatim: target ? L("Your target") : tier.line)
                        .font(UH.TextStyle.caption)
                        .foregroundStyle(target ? UH.Palette.accentInk : UH.Palette.secondary)
                }
                Spacer()
                Text(PlanViewModel.formatMinutes(minutes))
                    .font(tier == .b ? UH.TextStyle.metric : UH.TextStyle.body.monospacedDigit())
                    .foregroundStyle(UH.Palette.ink)
                Image(systemName: target ? "checkmark.circle.fill" : "chevron.right")
                    .font(.footnote.weight(.semibold))
                    .foregroundStyle(target ? UH.Palette.accentInk : UH.Palette.muted)
                    .accessibilityHidden(true)
            }
            .frame(minHeight: 56)
            .contentShape(Rectangle())
        }
        .buttonStyle(.plain)
        .disabled(busy)
        .accessibilityElement(children: .combine)
        .accessibilityIdentifier("goal.tier.\(tier.rawValue)")
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

    private func apply(_ minutes: Double) async {
        busy = true; error = nil
        error = await model.applyGoal(minutes: minutes)
        choosing = nil
        busy = false
    }
}

struct GoalChoice: Identifiable, Equatable {
    enum Tier: String { case a, b, c
        var title: String {
            switch self {
            case .a: L("If everything clicks")
            case .b: L("Your goal")
            case .c: L("Safety net")
            }
        }
        var line: String {
            switch self {
            case .a: L("Your best day")
            case .b: L("What your plan is built for")
            case .c: L("Still a good race on a rough day")
            }
        }
    }
    let tier: Tier
    let minutes: Double
    var id: String { tier.rawValue }
}

private extension Binding where Value == GoalChoice? {
    /// The same choice, seen only when it passes `include`; clearing it clears the source.
    func filtered(_ include: @escaping (GoalChoice) -> Bool) -> Binding<GoalChoice?> {
        Binding(get: { wrappedValue.flatMap { include($0) ? $0 : nil } }, set: { if $0 == nil { wrappedValue = nil } })
    }
}

/// Choosing A: what A asks of the week first, so the athlete commits knowing it. B stays the fallback.
struct ChooseAGoalSheet: View {
    let minutes: Double
    let feasibility: GoalFeasibility?
    let onConfirm: () -> Void
    @Environment(\.dismiss) private var dismiss

    private var unsupported: Bool { feasibility?.verdict == "unsupported" }

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: UH.Space.section) {
                    VStack(alignment: .leading, spacing: 4) {
                        Text(PlanViewModel.formatMinutes(minutes)).font(UH.TextStyle.metric).foregroundStyle(UH.Palette.ink)
                        Text("If everything clicks").font(UH.TextStyle.label).foregroundStyle(UH.Palette.secondary)
                    }
                    if let check = feasibility?.check {
                        VStack(alignment: .leading, spacing: UH.Space.compact) {
                            Label(check.title, systemImage: check.tone == .short ? "exclamationmark.triangle.fill" : "exclamationmark.circle")
                                .font(UH.TextStyle.label).foregroundStyle(UH.Palette.warningInk)
                            Text(check.line).font(UH.TextStyle.body).foregroundStyle(UH.Palette.ink)
                            ForEach(check.levers, id: \.self) { Text($0).font(UH.TextStyle.caption).foregroundStyle(UH.Palette.secondary) }
                        }
                        .padding(UH.Space.regular)
                        .frame(maxWidth: .infinity, alignment: .leading)
                        .background(UH.Palette.warningFill, in: RoundedRectangle(cornerRadius: UH.Radius.panel))
                    } else if feasibility != nil {
                        Label("Your week can carry this.", systemImage: "checkmark.circle.fill")
                            .font(UH.TextStyle.label).foregroundStyle(UH.Palette.accentInk)
                    }
                    Text("Coach Uphill adds the harder A sessions only in weeks when your progress and recovery say you're ready. Your goal stays as the fallback.")
                        .font(UH.TextStyle.body).foregroundStyle(UH.Palette.secondary)
                        .fixedSize(horizontal: false, vertical: true)
                    Text("Your training paces won't change until your next week is built.")
                        .font(UH.TextStyle.caption).foregroundStyle(UH.Palette.muted)
                    VStack(spacing: UH.Space.small) {
                        if unsupported {
                            Button("Keep my current target") { dismiss() }.buttonStyle(.uhPrimary)
                            Button("Train for A anyway", action: onConfirm).buttonStyle(.uhSecondary)
                        } else {
                            Button("Train for A", action: onConfirm).buttonStyle(.uhPrimary)
                            Button("Keep my current target") { dismiss() }.buttonStyle(.uhSecondary)
                        }
                    }
                    .accessibilityIdentifier("goal.chooseA.actions")
                }
                .padding(UH.Space.section)
            }
            .background(UH.Palette.surface)
            .navigationTitle(L("Chase A?"))
            .navigationBarTitleDisplayMode(.inline)
        }
        .presentationDetents([.medium, .large])
        .presentationBackground(UH.Palette.surface)
    }
}
