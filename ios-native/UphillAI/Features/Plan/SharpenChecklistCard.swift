import SwiftUI

/// Redesigned training card with a progress ring, icons, benefit copy, and checks.
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
                let doneCount = items.filter(\.done).count
                let totalCount = items.count

                VStack(alignment: .leading, spacing: UH.Space.regular) {
                    // Header with progress ring
                    HStack(alignment: .center, spacing: UH.Space.regular) {
                        VStack(alignment: .leading, spacing: 2) {
                            Text("Sharpen your plan").font(UH.TextStyle.sectionTitle).foregroundStyle(UH.Palette.ink)
                            Text("Each detail makes your next week's workouts more tailored.")
                                .font(UH.TextStyle.caption)
                                .foregroundStyle(UH.Palette.secondary)
                                .fixedSize(horizontal: false, vertical: true)
                        }

                        Spacer(minLength: 8)

                        // Circular progress ring
                        ZStack {
                            Circle()
                                .stroke(UH.Palette.line, lineWidth: 4.5)
                            Circle()
                                .trim(from: 0, to: CGFloat(doneCount) / CGFloat(max(1, totalCount)))
                                .stroke(UH.Palette.accent, style: StrokeStyle(lineWidth: 4.5, lineCap: .round))
                                .rotationEffect(.degrees(-90))
                            Text("\(doneCount) of \(totalCount)")
                                .font(.system(size: 11, weight: .bold, design: .monospaced))
                                .foregroundStyle(UH.Palette.ink)
                                .multilineTextAlignment(.center)
                        }
                        .frame(width: 52, height: 52)
                        .accessibilityElement(children: .ignore)
                        .accessibilityLabel("\(doneCount) of \(totalCount) completed")
                    }

                    Divider()

                    // Item rows with icons, benefits, and checks
                    VStack(spacing: UH.Space.small) {
                        ForEach(Array(items.enumerated()), id: \.element.id) { index, item in
                            Button {
                                onOpen(item.destination)
                            } label: {
                                HStack(spacing: UH.Space.small) {
                                    // Icon badge
                                    ZStack {
                                        RoundedRectangle(cornerRadius: UH.Radius.control)
                                            .fill(item.done ? UH.Palette.activeFill : UH.Palette.surface)
                                            .frame(width: 36, height: 36)
                                            .overlay(RoundedRectangle(cornerRadius: UH.Radius.control).stroke(item.done ? UH.Palette.accent : UH.Palette.line, lineWidth: 1))
                                        Image(systemName: icon(for: item.id))
                                            .font(.subheadline.weight(.semibold))
                                            .foregroundStyle(item.done ? UH.Palette.buttonInk : UH.Palette.accentInk)
                                    }

                                    VStack(alignment: .leading, spacing: 2) {
                                        Text(item.title)
                                            .font(UH.TextStyle.label)
                                            .foregroundStyle(UH.Palette.ink)
                                            .multilineTextAlignment(.leading)
                                        Text(benefit(for: item.id))
                                            .font(UH.TextStyle.caption)
                                            .foregroundStyle(UH.Palette.secondary)
                                            .multilineTextAlignment(.leading)
                                    }

                                    Spacer(minLength: 0)

                                    if item.done {
                                        Image(systemName: "checkmark.circle.fill")
                                            .font(.title3)
                                            .foregroundStyle(UH.Palette.accentInk)
                                    } else {
                                        Image(systemName: "chevron.right")
                                            .font(.footnote.weight(.semibold))
                                            .foregroundStyle(UH.Palette.muted)
                                    }
                                }
                                .frame(minHeight: 48)
                                .contentShape(Rectangle())
                            }
                            .buttonStyle(.plain)
                            .accessibilityValue(item.done ? "Done" : "Not done")

                            if index < items.count - 1 {
                                Divider()
                            }
                        }
                    }

                    // Hide button
                    Button {
                        UserDefaults.standard.set(true, forKey: key)
                        hidden = true
                    } label: {
                        Text("Hide for now")
                            .font(UH.TextStyle.caption)
                            .foregroundStyle(UH.Palette.muted)
                            .frame(maxWidth: .infinity, minHeight: 44, alignment: .center)
                    }
                    .buttonStyle(.plain)
                }
                .trainingCard()
            }
        }
        .task(id: plan.id) {
            hidden = UserDefaults.standard.bool(forKey: key)
        }
    }

    private func icon(for id: String) -> String {
        switch id {
        case "hr": "heart.fill"
        case "pace": "speedometer"
        case "notes": "cross.case.fill"
        case "schedule": "calendar"
        case "profile": "person.text.rectangle"
        default: "sparkles"
        }
    }

    private func benefit(for id: String) -> String {
        switch id {
        case "hr": "Locks in your aerobic endurance thresholds"
        case "pace": "Calibrates Zone 2 recovery & aerobic runs"
        case "notes": "Alerts Coach Uphill to adapt volume & loading"
        case "schedule": "Anchors your primary weekend endurance session"
        case "profile": "Refines energy expenditure & recovery rates"
        default: "Makes workouts more accurate"
        }
    }
}
