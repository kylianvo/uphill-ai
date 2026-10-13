import SwiftUI

/// "Get the most from your plan": the context that makes each new week fit the athlete
/// (watch, race history, thresholds, paces, injuries). Hidden once everything is done;
/// "Not now" hides it for two weeks.
struct SharpenChecklistCard: View {
    let user: User
    let corosConnected: Bool
    let raceHistoryLinked: Bool
    let onOpen: (TrainingDestination) -> Void
    var now: () -> Date = { .now }

    static let snoozeKey = "UPHILL_SHARPEN_SNOOZED_AT"
    static let snoozeDays = 14

    @State private var snoozed = false
    private var items: [SharpenItem] {
        SharpenChecklist.items(user: user, corosConnected: corosConnected, raceHistoryLinked: raceHistoryLinked)
    }

    var body: some View {
        let items = items
        let doneCount = items.filter(\.done).count
        Group {
            if !snoozed && doneCount < items.count {
                VStack(alignment: .leading, spacing: UH.Space.regular) {
                    HStack(alignment: .firstTextBaseline) {
                        Text("Get the most from your plan").font(UH.TextStyle.sectionTitle).foregroundStyle(UH.Palette.ink)
                        Spacer(minLength: 8)
                        Text(L("%lld of %lld", doneCount, items.count))
                            .font(UH.TextStyle.caption.weight(.semibold).monospacedDigit())
                            .foregroundStyle(UH.Palette.accentInk)
                    }
                    Text("Each one helps Coach Uphill fit your next weeks to you instead of an estimate.")
                        .font(UH.TextStyle.caption)
                        .foregroundStyle(UH.Palette.secondary)
                        .fixedSize(horizontal: false, vertical: true)

                    VStack(spacing: 0) {
                        ForEach(Array(items.enumerated()), id: \.element.id) { index, item in
                            if index > 0 { Divider() }
                            row(item)
                        }
                    }

                    Button("Not now") {
                        UserDefaults.standard.set(now().timeIntervalSince1970, forKey: Self.snoozeKey)
                        withAnimation(UH.Motion.standard) { snoozed = true }
                    }
                    .font(UH.TextStyle.caption)
                    .foregroundStyle(UH.Palette.secondary)
                    .frame(maxWidth: .infinity, minHeight: 44)
                }
                .trainingCard()
                .accessibilityIdentifier("plan.sharpen")
            }
        }
        .onAppear { snoozed = Self.isSnoozed(at: now()) }
    }

    static func isSnoozed(at date: Date, defaults: UserDefaults = .standard) -> Bool {
        let at = defaults.double(forKey: snoozeKey)
        guard at > 0 else { return false }
        return date.timeIntervalSince1970 - at < Double(snoozeDays) * 86_400
    }

    private func row(_ item: SharpenItem) -> some View {
        Button { onOpen(item.destination) } label: {
            HStack(spacing: UH.Space.small) {
                Image(systemName: icon(for: item.id))
                    .font(.subheadline.weight(.semibold))
                    .foregroundStyle(item.done ? UH.Palette.muted : UH.Palette.accentInk)
                    .frame(width: 36, height: 36)
                    .background(item.done ? UH.Palette.surface : UH.Palette.accent.opacity(0.12),
                                in: RoundedRectangle(cornerRadius: UH.Radius.control))
                VStack(alignment: .leading, spacing: 2) {
                    Text(item.title)
                        .font(UH.TextStyle.label)
                        .foregroundStyle(item.done ? UH.Palette.secondary : UH.Palette.ink)
                        .strikethrough(item.done, color: UH.Palette.muted)
                    if !item.done {
                        Text(benefit(for: item.id))
                            .font(UH.TextStyle.caption)
                            .foregroundStyle(UH.Palette.secondary)
                    }
                }
                .multilineTextAlignment(.leading)
                Spacer(minLength: 0)
                Image(systemName: item.done ? "checkmark.circle.fill" : "chevron.right")
                    .font(item.done ? .title3 : .footnote.weight(.semibold))
                    .foregroundStyle(item.done ? UH.Palette.accentInk : UH.Palette.muted)
            }
            .frame(minHeight: 56)
            .contentShape(Rectangle())
        }
        .buttonStyle(.plain)
        .accessibilityValue(item.done ? L("Done") : L("Not done"))
        .accessibilityIdentifier("plan.sharpen.\(item.id)")
    }

    private func icon(for id: String) -> String {
        switch id {
        case "watch": "applewatch.radiowaves.left.and.right"
        case "races": "medal"
        case "hr": "heart.fill"
        case "pace": "speedometer"
        default: "cross.case.fill"
        }
    }

    private func benefit(for id: String) -> String {
        switch id {
        case "watch": L("Real mileage and runs, not a guess")
        case "races": L("Your past finishes set a realistic goal")
        case "hr": L("Easy days stay easy, hard days hit the target")
        case "pace": L("Every workout gets a pace you can hold")
        default: L("Volume builds at a pace your body handles")
        }
    }
}
