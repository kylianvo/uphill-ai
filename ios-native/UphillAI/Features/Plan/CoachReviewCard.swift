import SwiftUI

struct CoachReviewCard: View {
    let model: PlanViewModel
    let onOpenReview: () -> Void
    @State private var isExpanded: Bool = false

    init(model: PlanViewModel, onOpenReview: @escaping () -> Void, initialExpanded: Bool = false) {
        self.model = model
        self.onOpenReview = onOpenReview
        _isExpanded = State(initialValue: initialExpanded)
    }
    @Environment(\.accessibilityReduceMotion) private var reduceMotion

    private var priorityWorkout: Workout? {
        model.snapshot?.workouts.first { $0.weekNumber == model.selectedWeek && $0.isPriority }
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            // Header / Collapsed view
            Button {
                withAnimation(reduceMotion ? nil : UH.Motion.standard) {
                    isExpanded.toggle()
                }
            } label: {
                HStack(alignment: .center, spacing: 10) {
                    Image(systemName: "quote.bubble.fill")
                        .font(.system(size: 14))
                        .foregroundStyle(UH.Palette.accentInk)
                        .padding(6)
                        .background(UH.Palette.activeFill, in: Circle())

                    VStack(alignment: .leading, spacing: 2) {
                        HStack(spacing: 6) {
                            Text("COACH'S REVIEW")
                                .font(.system(size: 10, weight: .bold, design: .monospaced))
                                .foregroundStyle(UH.Palette.accentInk)
                            if !isExpanded, let prio = priorityWorkout {
                                Text("· Pick: \(prio.title)")
                                    .font(UH.TextStyle.caption)
                                    .foregroundStyle(UH.Palette.secondary)
                                    .lineLimit(1)
                            }
                        }

                        if !isExpanded {
                            if let thisWeek = whyThisWeek {
                                Text(verbatim: thisWeek)
                                    .font(UH.TextStyle.caption)
                                    .foregroundStyle(UH.Palette.secondary)
                                    .lineLimit(1)
                            } else {
                                Text("Tap to read coach takeaways and weekly focus")
                                    .font(UH.TextStyle.caption)
                                    .foregroundStyle(UH.Palette.muted)
                                    .lineLimit(1)
                            }
                        }
                    }

                    Spacer()

                    Image(systemName: isExpanded ? "chevron.up" : "chevron.down")
                        .font(.system(size: 12, weight: .semibold))
                        .foregroundStyle(UH.Palette.muted)
                        .frame(width: 44, height: 44)
                        .contentShape(Rectangle())
                }
                .contentShape(Rectangle())
            }
            .buttonStyle(.plain)
            .accessibilityIdentifier("plan.coachCard.toggle")

            // Expanded content
            if isExpanded {
                VStack(alignment: .leading, spacing: UH.Space.small) {
                    Divider().overlay(UH.Palette.line.opacity(0.6)).padding(.vertical, 4)

                    // Key Coach Takeaways
                    takeawaysSection

                    // Coach's pick this week
                    if let priority = priorityWorkout {
                        coachPickSection(priority)
                    }

                    // Weekly review action
                    Button(action: onOpenReview) {
                        HStack {
                            Image(systemName: "chart.bar.doc.horizontal")
                                .font(.system(size: 12))
                            Text("Read complete weekly review")
                                .font(.system(size: 12.5, weight: .semibold))
                            Spacer()
                            Image(systemName: "chevron.right")
                                .font(.system(size: 11, weight: .bold))
                        }
                        .foregroundStyle(UH.Palette.accentInk)
                        .padding(.vertical, 8)
                        .padding(.horizontal, 10)
                        .background(UH.Palette.hover, in: RoundedRectangle(cornerRadius: UH.Radius.control))
                    }
                    .buttonStyle(.plain)
                    .accessibilityIdentifier("plan.coachCard.reviewLink")
                }
                .transition(.opacity.combined(with: .move(edge: .top)))
            }
        }
        .padding(UH.Space.small)
        .background(UH.Palette.card, in: RoundedRectangle(cornerRadius: UH.Radius.landing))
        .overlay(RoundedRectangle(cornerRadius: UH.Radius.landing).stroke(UH.Palette.line))
    }

    /// The week brief's reason, else the block narrative's focus for the week.
    private var whyThisWeek: String? {
        let why = model.weekBrief?.why ?? model.selectedWeekNarrative?.aiThisWeekDescription
        return why?.isEmpty == false ? why : nil
    }

    private func section<Content: View>(_ title: String, tint: Color = UH.Palette.secondary, @ViewBuilder _ content: () -> Content) -> some View {
        VStack(alignment: .leading, spacing: 2) {
            Text(verbatim: title)
                .font(.system(size: 9.5, weight: .bold, design: .monospaced))
                .foregroundStyle(tint)
            content()
                .font(.system(size: 12.5))
                .foregroundStyle(UH.Palette.ink)
                .lineSpacing(1.5)
                .fixedSize(horizontal: false, vertical: true)
        }
    }

    // Key Coach Takeaways: the coach message, why this week, what the key sessions build, what to watch, last week
    private var takeawaysSection: some View {
        let brief = model.weekBrief
        let nudge = model.selectedWeek == model.currentWeek ? model.coachNudge : nil
        let lastWeek = model.selectedWeekNarrative?.aiLastWeekReview

        return VStack(alignment: .leading, spacing: UH.Space.small) {
            if let nudge {
                Text(verbatim: nudge.text)
                    .font(.system(size: 13.5, weight: .semibold))
                    .foregroundStyle(nudge.kind == .headsUp ? UH.Palette.warningInk : UH.Palette.ink)
                    .fixedSize(horizontal: false, vertical: true)
            }
            if let why = whyThisWeek {
                section(L("WHY THIS WEEK"), tint: UH.Palette.accentInk) { Text(verbatim: why) }
            }
            if let benefits = brief?.benefits, !benefits.isEmpty {
                section(L("WHAT IT BUILDS")) {
                    VStack(alignment: .leading, spacing: 2) {
                        ForEach(benefits, id: \.self) { Text(verbatim: "• " + $0) }
                    }
                }
            }
            if let watch = brief?.watch, !watch.isEmpty {
                section(L("WATCH OUT"), tint: UH.Palette.warningInk) { Text(verbatim: watch) }
            }
            if let lastWeek, !lastWeek.isEmpty {
                section(L("LAST WEEK REVIEW")) { Text(verbatim: lastWeek) }
            }
        }
        .padding(UH.Space.small)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(UH.Palette.surface, in: RoundedRectangle(cornerRadius: UH.Radius.control))
    }

    // Coach's pick this week
    private func coachPickSection(_ workout: Workout) -> some View {
        VStack(alignment: .leading, spacing: 3) {
            HStack(spacing: 5) {
                Image(systemName: "star.fill")
                    .font(.system(size: 10))
                    .foregroundStyle(UH.Palette.accentInk)
                Text("COACH'S PICK THIS WEEK")
                    .font(.system(size: 10, weight: .bold, design: .monospaced))
                    .foregroundStyle(UH.Palette.accentInk)
                Spacer()
                Text("PRIORITY")
                    .font(.system(size: 9, weight: .bold))
                    .foregroundStyle(UH.Palette.accentInk)
                    .padding(.horizontal, 5)
                    .padding(.vertical, 2)
                    .background(UH.Palette.activeFill, in: Capsule())
            }

            Text("\(workout.title) (\(Int(workout.durationMinutes)) min)")
                .font(.system(size: 13, weight: .semibold))
                .foregroundStyle(UH.Palette.ink)

            Text("This session drives your primary training stimulus this week. Stay disciplined on the target zone.")
                .font(.system(size: 12))
                .foregroundStyle(UH.Palette.secondary)
        }
        .padding(UH.Space.small)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(UH.Palette.activeFill.opacity(0.4), in: RoundedRectangle(cornerRadius: UH.Radius.control))
        .overlay(RoundedRectangle(cornerRadius: UH.Radius.control).stroke(UH.Palette.accentInk.opacity(0.3), lineWidth: 1))
    }
}
