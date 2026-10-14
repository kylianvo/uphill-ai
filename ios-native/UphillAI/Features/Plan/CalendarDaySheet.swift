import SwiftUI

/// Peek at one day from the month grid without leaving it. Reads the day live from the model,
/// so ticking a session done updates the sheet in place.
struct CalendarDaySheet: View {
    let model: PlanViewModel
    let target: MoveTarget
    let onOpenWeek: (Int) -> Void
    let onSelect: (Workout) -> Void
    var onMoveOrSwap: ((PlanDay) -> Void)? = nil
    @Environment(\.dismiss) private var dismiss

    private var day: PlanDay? { model.days(for: target.week).first { $0.weekday == target.weekday } }

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: UH.Space.regular) {
                    if let day {
                        DayRow(day: day, onToggleDone: model.athleteId == nil ? { workout in
                            Task { await model.setDone(workout, !workout.isDone) }
                        } : nil, onMoveOrSwap: onMoveOrSwap, onSelect: onSelect)
                    }
                    Button { onOpenWeek(target.week) } label: {
                        Label(L("Open week %lld in list", target.week), systemImage: "list.bullet")
                            .font(UH.TextStyle.label)
                            .frame(maxWidth: .infinity, minHeight: 44)
                    }
                    .buttonStyle(.bordered)
                    .tint(UH.Palette.accentInk)
                    .accessibilityIdentifier("calendar.openWeek")
                }
                .padding(UH.Space.regular)
            }
            .background(UH.Palette.surface.ignoresSafeArea())
            .navigationTitle(target.date.formatted(.dateTime.weekday(.wide).day().month(.wide).locale(AppLanguage.current.locale)))
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .topBarTrailing) { Button("Done") { dismiss() } }
            }
        }
        .presentationDetents([.medium, .large])
    }
}
