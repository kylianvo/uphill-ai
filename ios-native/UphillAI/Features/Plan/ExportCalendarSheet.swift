import SwiftUI

struct ExportCalendarSheet: View {
    let model: PlanViewModel
    @Environment(\.dismiss) private var dismiss
    @Environment(\.openURL) private var openURL

    @State private var timePref = "all_day"
    @State private var copied = false

    private var plan: Plan? {
        model.snapshot?.plan
    }

    private var exportURLString: String {
        guard let plan else { return "" }
        let base = "https://app.uphill.ai"
        return "\(base)/api/coach/export-ics?plan_id=\(plan.id)&race_date=\(plan.raceDate)&time_pref=\(timePref)"
    }

    private var webcalURLString: String {
        exportURLString.replacingOccurrences(of: "https://", with: "webcal://")
    }

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: UH.Space.regular) {
                    // Hero card
                    heroCard

                    // Time preference selector
                    timePreferenceCard

                    // Action buttons
                    actionButtonsCard

                    // Instructions
                    instructionsCard
                }
                .padding(UH.Space.regular)
            }
            .background(UH.Palette.surface)
            .navigationTitle("Export Calendar")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Done") { dismiss() }
                }
            }
        }
        .presentationDetents([.medium, .large])
        .presentationBackground(UH.Palette.surface)
        .accessibilityIdentifier("export.calendar.sheet")
    }

    // MARK: - Hero Card

    private var heroCard: some View {
        VStack(alignment: .leading, spacing: UH.Space.small) {
            HStack(spacing: UH.Space.compact) {
                Image(systemName: "calendar.badge.clock")
                    .font(.title2)
                    .foregroundStyle(UH.Palette.accentInk)
                VStack(alignment: .leading, spacing: 2) {
                    Text(plan?.raceName ?? "Training Plan")
                        .font(UH.TextStyle.sectionTitle)
                        .foregroundStyle(UH.Palette.ink)
                    Text("\(model.weeks.count) weeks · \(model.snapshot?.workouts.filter { !$0.isRest }.count ?? 0) sessions")
                        .font(UH.TextStyle.caption)
                        .foregroundStyle(UH.Palette.secondary)
                }
            }

            Text("Add workouts directly to Apple Calendar, Google Calendar, or Outlook. Subscriptions stay updated as your plan adapts.")
                .font(UH.TextStyle.body)
                .foregroundStyle(UH.Palette.secondary)
        }
        .padding(UH.Space.regular)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(UH.Palette.card, in: RoundedRectangle(cornerRadius: UH.Radius.landing))
        .overlay(RoundedRectangle(cornerRadius: UH.Radius.landing).stroke(UH.Palette.line))
    }

    // MARK: - Time Preference Card

    private var timePreferenceCard: some View {
        VStack(alignment: .leading, spacing: UH.Space.compact) {
            Text("PREFERRED WORKOUT TIME")
                .font(.system(size: 10.5, weight: .bold, design: .monospaced))
                .tracking(0.5)
                .foregroundStyle(UH.Palette.muted)

            VStack(spacing: 6) {
                timeOption(id: "all_day", title: "All Day Event", subtitle: "Best for flexible daily scheduling", icon: "sun.max")
                timeOption(id: "morning", title: "Morning (06:00)", subtitle: "Early workout time slot", icon: "sunrise.fill")
                timeOption(id: "afternoon", title: "Afternoon (14:00)", subtitle: "Mid-day workout block", icon: "sun.haze.fill")
                timeOption(id: "evening", title: "Evening (18:00)", subtitle: "Post-work session", icon: "sunset.fill")
            }
        }
        .padding(UH.Space.regular)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(UH.Palette.card, in: RoundedRectangle(cornerRadius: UH.Radius.landing))
        .overlay(RoundedRectangle(cornerRadius: UH.Radius.landing).stroke(UH.Palette.line))
    }

    private func timeOption(id: String, title: String, subtitle: String, icon: String) -> some View {
        let isSelected = timePref == id
        return Button {
            timePref = id
        } label: {
            HStack(spacing: UH.Space.small) {
                Image(systemName: icon)
                    .font(.body)
                    .foregroundStyle(isSelected ? UH.Palette.accentInk : UH.Palette.secondary)
                    .frame(width: 24)

                VStack(alignment: .leading, spacing: 2) {
                    Text(title)
                        .font(UH.TextStyle.label)
                        .foregroundStyle(UH.Palette.ink)
                    Text(subtitle)
                        .font(UH.TextStyle.caption)
                        .foregroundStyle(UH.Palette.secondary)
                }

                Spacer()

                if isSelected {
                    Image(systemName: "checkmark.circle.fill")
                        .foregroundStyle(UH.Palette.accentInk)
                }
            }
            .padding(.horizontal, UH.Space.small)
            .padding(.vertical, 8)
            .background(isSelected ? UH.Palette.activeFill : UH.Palette.surface, in: RoundedRectangle(cornerRadius: UH.Radius.control))
            .overlay(RoundedRectangle(cornerRadius: UH.Radius.control).stroke(isSelected ? UH.Palette.accent : UH.Palette.line, lineWidth: 1))
        }
        .buttonStyle(.plain)
    }

    // MARK: - Action Buttons

    private var actionButtonsCard: some View {
        VStack(spacing: UH.Space.compact) {
            Button {
                if let url = URL(string: webcalURLString) {
                    openURL(url)
                }
            } label: {
                HStack(spacing: 8) {
                    Image(systemName: "calendar.badge.plus")
                    Text("Subscribe in Apple Calendar")
                }
                .frame(maxWidth: .infinity)
            }
            .buttonStyle(.uhPrimary)
            .accessibilityIdentifier("export.subscribe.apple")

            Button {
                UIPasteboard.general.string = exportURLString
                copied = true
                Task {
                    try? await Task.sleep(for: .seconds(2.5))
                    copied = false
                }
            } label: {
                HStack(spacing: 6) {
                    Image(systemName: copied ? "checkmark" : "doc.on.doc")
                        .foregroundStyle(copied ? UH.Palette.accentInk : UH.Palette.ink)
                    Text(copied ? "Link Copied!" : "Copy Calendar Subscription URL")
                        .foregroundStyle(copied ? UH.Palette.accentInk : UH.Palette.ink)
                }
                .font(UH.TextStyle.label)
                .frame(maxWidth: .infinity)
                .frame(height: 44)
                .background(UH.Palette.card, in: RoundedRectangle(cornerRadius: UH.Radius.control))
                .overlay(RoundedRectangle(cornerRadius: UH.Radius.control).stroke(UH.Palette.line, lineWidth: 1))
            }
            .buttonStyle(.plain)
            .sensoryFeedback(.success, trigger: copied)
            .accessibilityIdentifier("export.copy.url")
        }
    }

    // MARK: - Instructions

    private var instructionsCard: some View {
        VStack(alignment: .leading, spacing: 6) {
            Text("GOOGLE CALENDAR & OUTLOOK")
                .font(.system(size: 10, weight: .bold, design: .monospaced))
                .tracking(0.5)
                .foregroundStyle(UH.Palette.muted)

            Text("To subscribe in Google Calendar or Outlook on the web, copy the subscription link above and select \"Add Calendar from URL\".")
                .font(UH.TextStyle.caption)
                .foregroundStyle(UH.Palette.secondary)
        }
        .padding(UH.Space.small)
        .frame(maxWidth: .infinity, alignment: .leading)
    }
}
