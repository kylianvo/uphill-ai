import Charts
import SwiftUI

extension TriageSection {
    var title: LocalizedStringKey {
        switch self {
        case .actNow: "Act now"
        case .reviewBuild: "Review & build"
        case .checkIn: "Check in"
        case .onTrack: "On track"
        }
    }

    var symbol: String {
        switch self {
        case .actNow: "exclamationmark.circle.fill"
        case .reviewBuild: "doc.text.magnifyingglass"
        case .checkIn: "bubble.left.fill"
        case .onTrack: "checkmark.circle.fill"
        }
    }

    var tint: Color {
        switch self {
        case .actNow: UH.Palette.danger
        case .reviewBuild: Color(light: "#1f6c9f", dark: "#7cc4f5")
        case .checkIn: UH.Palette.warningInk
        case .onTrack: UH.Palette.accentInk
        }
    }
}

extension CoachAction {
    var label: LocalizedStringKey {
        switch self {
        case .adaptWeek: "Adapt week"
        case .reviewPlan: "Review plan"
        case .buildPlan: "Build plan"
        case .openDraft: "Open draft"
        case .buildNextWeek: "Build next week"
        case .reviewChanges: "Review changes"
        case .note: "Note"
        }
    }
}

/// Review | Coached tag in the app's quiet pill style.
struct PlanTypeTag: View {
    let planType: String

    var body: some View {
        Text(planType == "coached" ? "Coached" : "Review")
            .font(.caption2.weight(.semibold))
            .padding(.horizontal, 7)
            .padding(.vertical, 2)
            .background(UH.Palette.tint, in: Capsule())
            .foregroundStyle(UH.Palette.secondary)
    }
}

/// One runner in an inbox section: name, the reason they're here, and the one action it calls for.
struct AthleteTriageRow: View {
    let athlete: CoachOverviewAthlete
    let onOpen: () -> Void
    let onAction: (CoachAction) -> Void
    let menu: AnyView

    private var reasons: [CoachSignal] { (athlete.signals ?? []).filter { $0.severity != .highlight } }

    var body: some View {
        VStack(alignment: .leading, spacing: 6) {
            HStack(alignment: .firstTextBaseline, spacing: 8) {
                Text(athlete.name)
                    .font(UH.TextStyle.label)
                    .foregroundStyle(UH.Palette.ink)
                    .lineLimit(1)
                PlanTypeTag(planType: athlete.effectivePlanType)
                Spacer(minLength: 4)
                menu
            }
            if let top = reasons.first {
                Text(CoachSignalText.sentence(top))
                    .font(.subheadline.weight(.medium))
                    .foregroundStyle(UH.Palette.ink)
                    .fixedSize(horizontal: false, vertical: true)
            }
            if reasons.count > 1 {
                Text(reasons.dropFirst().map { CoachSignalText.sentence($0) }.joined(separator: " · "))
                    .font(UH.TextStyle.caption)
                    .foregroundStyle(UH.Palette.secondary)
                    .lineLimit(2)
            }
            HStack(spacing: 8) {
                Text(AthleteMeta.line(athlete))
                    .font(UH.TextStyle.caption)
                    .foregroundStyle(UH.Palette.muted)
                    .lineLimit(1)
                Spacer(minLength: 4)
                if let action = athlete.primaryAction {
                    Button(action.label) { onAction(action) }
                        .font(.footnote.weight(.semibold))
                        .buttonStyle(.bordered)
                        .tint(athlete.section.tint)
                        .controlSize(.small)
                        .accessibilityIdentifier("athletes.action.\(athlete.athleteId)")
                }
            }
        }
        .padding(UH.Space.small)
        .background(UH.Palette.card, in: RoundedRectangle(cornerRadius: UH.Radius.panel))
        .overlay(RoundedRectangle(cornerRadius: UH.Radius.panel).stroke(UH.Palette.line, lineWidth: 1))
        .contentShape(RoundedRectangle(cornerRadius: UH.Radius.panel))
        .onTapGesture(perform: onOpen)
        .accessibilityElement(children: .combine)
        .accessibilityAction(named: Text("Open plan"), onOpen)
    }
}

enum AthleteMeta {
    /// "W6/12 · Build · 57 d · VMM 42K" — or "No plan".
    static func line(_ a: CoachOverviewAthlete) -> String {
        guard let plan = a.activePlan else { return L("No plan") }
        // Week, phase and days first: a long race name truncates last.
        var parts = ["W\(plan.currentWeek)/\(plan.totalWeeks)"]
        if let phase = a.phase { parts.append(phase.capitalized) }
        if let d = a.daysToRace, d >= 0 { parts.append(L("%lld d", d)) }
        parts.append(plan.raceName)
        return parts.joined(separator: " · ")
    }
}

/// A compact On-track line: name, week, 14-day done %, 4-week load sparkline.
struct OnTrackRow: View {
    let athlete: CoachOverviewAthlete
    let onOpen: () -> Void

    var body: some View {
        Button(action: onOpen) {
            HStack(spacing: 10) {
                VStack(alignment: .leading, spacing: 2) {
                    Text(athlete.name)
                        .font(.subheadline.weight(.semibold))
                        .foregroundStyle(UH.Palette.ink)
                        .lineLimit(1)
                    Text(AthleteMeta.line(athlete))
                        .font(.caption)
                        .foregroundStyle(UH.Palette.muted)
                        .lineLimit(1)
                }
                Spacer(minLength: 6)
                if let load = athlete.load4WMinutes, load.contains(where: { $0 > 0 }) {
                    Chart(Array(load.enumerated()), id: \.offset) { item in
                        BarMark(x: .value("Week", item.offset), y: .value("Minutes", item.element))
                            .foregroundStyle(item.offset == load.count - 1 ? UH.Palette.accent : UH.Palette.line)
                            .cornerRadius(2)
                    }
                    .chartXAxis(.hidden)
                    .chartYAxis(.hidden)
                    .frame(width: 44, height: 22)
                    .accessibilityHidden(true)
                }
                Text(athlete.adherence14D.map(CoachFormat.wholePercent) ?? "—")
                    .font(.footnote.weight(.semibold).monospacedDigit())
                    .foregroundStyle(UH.Palette.secondary)
                    .frame(minWidth: 40, alignment: .trailing)
            }
            .padding(.vertical, 8)
            .contentShape(Rectangle())
        }
        .buttonStyle(.plain)
    }
}
