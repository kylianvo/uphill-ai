import SwiftUI

/// Picks the watch run that belongs to a workout, for when matching linked the wrong one or none.
/// A manual link is never re-scored by later automatic matching.
struct WatchMatchSheet: View {
    let model: PlanViewModel
    let workout: Workout
    @Environment(\.dismiss) private var dismiss

    private enum Phase: Equatable { case loading, loaded([WatchActivity]), failed(String) }
    @State private var phase: Phase = .loading
    @State private var linkingID: Int?
    @State private var error: String?

    var body: some View {
        NavigationStack {
            Group {
                switch phase {
                case .loading:
                    ProgressView().frame(maxWidth: .infinity, maxHeight: .infinity)
                case .failed(let message):
                    emptyState(icon: "exclamationmark.triangle", title: L("Couldn't load your watch runs"), body: message,
                               retry: true)
                case .loaded(let activities) where activities.isEmpty:
                    emptyState(icon: "applewatch.slash", title: L("No watch runs in this plan yet"),
                               body: L("Sync your watch from Manage, then come back to link a run."), retry: false)
                case .loaded(let activities):
                    list(activities)
                }
            }
            .background(UH.Palette.surface.ignoresSafeArea())
            .navigationTitle("Link a watch run")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) { Button("Cancel") { dismiss() } }
            }
        }
        .task { await reload() }
        .presentationDetents([.medium, .large])
        .accessibilityIdentifier("watchMatch.sheet")
    }

    private func list(_ activities: [WatchActivity]) -> some View {
        List {
            Section {
                ForEach(activities) { activity in
                    row(activity)
                }
            } header: {
                Text("Pick the run you did for \(workout.title).")
                    .font(UH.TextStyle.caption)
                    .foregroundStyle(UH.Palette.secondary)
                    .textCase(nil)
            } footer: {
                if let error {
                    Text(error).font(UH.TextStyle.caption).foregroundStyle(UH.Palette.danger)
                }
            }
        }
        .scrollContentBackground(.hidden)
    }

    private func row(_ activity: WatchActivity) -> some View {
        let isCurrent = activity.workoutId == workout.id && activity.isSettledMatch
        return Button {
            guard !isCurrent else { return }
            Task { await link(activity) }
        } label: {
            HStack(spacing: UH.Space.small) {
                VStack(alignment: .leading, spacing: 3) {
                    Text(Self.title(activity))
                        .font(UH.TextStyle.label)
                        .foregroundStyle(UH.Palette.ink)
                    Text(Self.measurements(activity))
                        .font(UH.TextStyle.caption)
                        .monospacedDigit()
                        .foregroundStyle(UH.Palette.secondary)
                    Text(linkText(activity))
                        .font(UH.TextStyle.caption)
                        .foregroundStyle(isCurrent ? UH.Palette.accentInk : UH.Palette.muted)
                }
                Spacer(minLength: 0)
                if linkingID == activity.activityId {
                    ProgressView()
                } else if isCurrent {
                    Image(systemName: "checkmark.circle.fill").foregroundStyle(UH.Palette.accentInk)
                }
            }
            .frame(minHeight: 44)
            .contentShape(Rectangle())
        }
        .buttonStyle(.plain)
        .disabled(linkingID != nil)
        .listRowBackground(UH.Palette.card)
        .accessibilityIdentifier("watchMatch.row.\(activity.activityId)")
    }

    private func linkText(_ activity: WatchActivity) -> String {
        if activity.workoutId == workout.id { return L("Linked to this workout") }
        if let title = activity.workoutTitle, activity.workoutId != nil { return L("Now linked to %@", title) }
        return L("Not linked")
    }

    private func emptyState(icon: String, title: String, body: String, retry: Bool) -> some View {
        VStack(spacing: UH.Space.compact) {
            Image(systemName: icon).font(.system(size: 32)).foregroundStyle(UH.Palette.secondary)
                .accessibilityHidden(true)
            Text(title).font(UH.TextStyle.sectionTitle).foregroundStyle(UH.Palette.ink)
            Text(body).font(UH.TextStyle.body).foregroundStyle(UH.Palette.secondary)
                .multilineTextAlignment(.center).fixedSize(horizontal: false, vertical: true)
            if retry {
                Button("Try again") { Task { await reload() } }.buttonStyle(.uhSecondary).frame(maxWidth: 200)
            }
        }
        .padding(UH.Space.section)
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }

    private func reload() async {
        phase = .loading
        do {
            phase = .loaded(try await model.watchActivities())
        } catch let error as APIError {
            phase = .failed(error.userMessage)
        } catch {
            phase = .failed(error.localizedDescription)
        }
    }

    private func link(_ activity: WatchActivity) async {
        linkingID = activity.activityId
        error = nil
        defer { linkingID = nil }
        if let message = await model.setMatch(activityID: activity.activityId, to: workout) {
            error = message
        } else {
            dismiss()
        }
    }

    static func title(_ activity: WatchActivity) -> String {
        guard let date = activity.startDate else { return L("Watch run") }
        return date.formatted(Date.FormatStyle(locale: AppLanguage.current.locale)
            .weekday(.abbreviated).month(.abbreviated).day().hour().minute())
    }

    static func measurements(_ activity: WatchActivity) -> String {
        var parts: [String] = []
        if let km = activity.distanceKm {
            parts.append("\(km.formatted(.number.precision(.fractionLength(1)))) km")
        }
        if let seconds = activity.durationSeconds {
            parts.append(Duration.seconds(seconds).formatted(.time(pattern: seconds >= 3600 ? .hourMinuteSecond : .minuteSecond)))
        }
        if let hr = activity.avgHr {
            parts.append(L("avg HR %lld", Int(hr.rounded())))
        }
        return parts.joined(separator: " · ")
    }
}
