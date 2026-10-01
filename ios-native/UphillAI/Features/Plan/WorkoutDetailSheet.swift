import SwiftUI

struct WorkoutDetailSheet: View {
    let model: PlanViewModel
    let workoutID: Int
    @Environment(\.dismiss) private var dismiss
    @State private var rpe: Int?
    @State private var notes = ""
    @State private var didLoadLog = false
    @State private var showSaved = false
    @State private var isBusy = false

    private var workout: Workout? { model.snapshot?.workouts.first { $0.id == workoutID } }

    var body: some View {
        NavigationStack {
            if let workout {
                ScrollView {
                    VStack(alignment: .leading, spacing: UH.Space.section) {
                        header(workout)
                        facts(workout)
                        if let text = workout.description, !text.isEmpty { prose("About", text) }
                        if let tip = workout.fuelingTip, !tip.isEmpty { prose("Fueling", tip) }
                        if let error = model.actionError {
                            Text(error).font(UH.TextStyle.caption).foregroundStyle(UH.Palette.danger)
                        }
                        if workout.approvedAt == nil {
                            Label("Waiting for your coach's approval", systemImage: "hourglass")
                                .font(UH.TextStyle.caption)
                                .foregroundStyle(UH.Palette.secondary)
                        } else {
                            actions(workout)
                            if !workout.isRest { logSection(workout) }
                        }
                    }
                    .padding(UH.Space.medium)
                }
                .background(UH.Palette.surface.ignoresSafeArea())
                .toolbar { Button("Done") { dismiss() } }
                .onAppear { loadLog(workout) }
            }
        }
        .presentationDetents([.medium, .large])
        .presentationDragIndicator(.visible)
        .sensoryFeedback(.success, trigger: model.lastCompletedID)
        .sensoryFeedback(.error, trigger: model.actionError) { _, new in new != nil }
        .onDisappear { model.clearActionError() }
    }

    private func header(_ w: Workout) -> some View {
        VStack(alignment: .leading, spacing: 4) {
            if w.isPriority {
                Text("PRIORITY").font(UH.TextStyle.eyebrow).tracking(0.6).foregroundStyle(UH.Palette.accentInk)
            }
            Text(w.title).font(UH.TextStyle.sectionTitle).foregroundStyle(UH.Palette.ink)
            Text(subtitle(w)).font(UH.TextStyle.caption).foregroundStyle(UH.Palette.secondary)
        }
    }

    private func subtitle(_ w: Workout) -> String {
        guard let plan = model.snapshot?.plan,
              let date = PlanCalendar.date(week: w.weekNumber, weekday: w.weekday, plan: plan,
                                           workouts: model.snapshot?.workouts ?? []) else { return w.phase }
        return date.formatted(.dateTime.weekday(.abbreviated).day().month(.abbreviated)) + " · " + w.phase
    }

    private struct Fact: Identifiable {
        let label: String
        let value: String
        var id: String { label }
    }

    private func facts(_ w: Workout) -> some View {
        let candidates: [(String, String?)] = [
            ("Duration", "\(Int(w.durationMinutes)) min"),
            ("Distance", w.distanceKm.flatMap { $0 > 0 ? $0.formatted(.number.precision(.fractionLength(0...1))) + " km" : nil }),
            ("Elevation gain", w.elevationGainM.flatMap { $0 > 0 ? "\(Int($0)) m" : nil }),
            ("Zone", w.targetZone == "Rest" ? nil : w.targetZone),
            ("Heart rate", w.targetHrRange),
            ("Pace", w.targetPace),
            ("Intervals", intervals(w)),
            ("Treadmill", treadmill(w)),
        ]
        let facts = candidates.compactMap { label, value in value.map { Fact(label: label, value: $0) } }
        return LazyVGrid(columns: [GridItem(.flexible(), alignment: .leading), GridItem(.flexible(), alignment: .leading)],
                         alignment: .leading, spacing: UH.Space.small) {
            ForEach(facts) { fact in
                VStack(alignment: .leading, spacing: 2) {
                    Text(fact.label.uppercased()).font(UH.TextStyle.eyebrow).foregroundStyle(UH.Palette.muted)
                    Text(fact.value).font(UH.TextStyle.label).foregroundStyle(UH.Palette.ink)
                }
                .accessibilityElement(children: .combine)
            }
        }
        .uhCard()
    }

    private func intervals(_ w: Workout) -> String? {
        guard let reps = w.intervalReps, let value = w.intervalRepValue, let unit = w.intervalRepUnit else { return nil }
        var text = "\(reps) × \(value.formatted(.number.precision(.fractionLength(0...1)))) \(unit)"
        if let walk = w.walkIntervalValue, walk > 0 {
            text += ", walk \(walk.formatted(.number.precision(.fractionLength(0...1)))) \(unit)"
        }
        return text
    }

    private func treadmill(_ w: Workout) -> String? {
        guard let speed = w.treadmillSpeed, speed != "0", !speed.isEmpty else { return nil }
        let incline = w.treadmillIncline.flatMap { $0 == "0" || $0.isEmpty ? nil : $0 }
        let speedText = speed.replacingOccurrences(of: "-", with: "–") + " km/h"
        guard let incline else { return speedText }
        return speedText + " · " + incline.replacingOccurrences(of: "-", with: "–") + " %"
    }

    private func prose(_ title: String, _ text: String) -> some View {
        VStack(alignment: .leading, spacing: UH.Space.compact) {
            Text(title.uppercased()).font(UH.TextStyle.eyebrow).foregroundStyle(UH.Palette.muted)
            Text(text).font(UH.TextStyle.body).foregroundStyle(UH.Palette.ink)
        }
    }

    @ViewBuilder
    private func actions(_ w: Workout) -> some View {
        VStack(spacing: UH.Space.small) {
            if w.isDone {
                Button("Undo done") { run { await model.setDone(w, false) } }.buttonStyle(.uhSecondary).accessibilityIdentifier("detail.undoDone")
            } else if !w.isRest {
                Button("Mark as done") { run { await model.setDone(w, true) } }.buttonStyle(.uhPrimary).accessibilityIdentifier("detail.markDone")
                if !w.isMissedFlag {
                    Button("Mark as missed") { run { await model.setMissed(w) } }.buttonStyle(.uhSecondary)
                } else {
                    Text("Marked as missed").font(UH.TextStyle.caption).foregroundStyle(UH.Palette.danger)
                }
            }
            if !w.isRest {
                let targets = model.moveTargets(for: w)
                if !targets.isEmpty {
                    Menu {
                        ForEach(targets) { target in
                            Button(moveLabel(target)) { run { if await model.move(w, to: target) { dismiss() } } }
                        }
                    } label: {
                        Label("Move to…", systemImage: "calendar")
                            .frame(maxWidth: .infinity, minHeight: 44)
                    }
                    .font(UH.TextStyle.label)
                    .foregroundStyle(UH.Palette.accentInk)
                }
            }
        }
        .disabled(isBusy)
    }

    private func moveLabel(_ target: MoveTarget) -> String {
        let day = target.date.formatted(.dateTime.weekday(.abbreviated).day().month(.abbreviated))
        return target.week > model.currentWeek ? "Next week · \(day)" : day
    }

    private func logSection(_ w: Workout) -> some View {
        VStack(alignment: .leading, spacing: UH.Space.small) {
            Text("YOUR LOG").font(UH.TextStyle.eyebrow).foregroundStyle(UH.Palette.muted)
            Stepper(value: Binding(get: { rpe ?? 5 }, set: { rpe = $0 }), in: 1...10) {
                LabeledContent("Effort (RPE)", value: rpe.map(String.init) ?? "Not set")
            }
            TextField("Notes", text: $notes, axis: .vertical)
                .lineLimit(3...6)
                .padding(UH.Space.small)
                .background(UH.Palette.card, in: RoundedRectangle(cornerRadius: UH.Radius.control))
                .overlay(RoundedRectangle(cornerRadius: UH.Radius.control).stroke(UH.Palette.line))
            Button(showSaved ? "Saved" : "Save") {
                run {
                    if await model.saveLog(w, rpe: rpe, notes: notes) {
                        showSaved = true
                        try? await Task.sleep(for: .seconds(2))
                        showSaved = false
                    }
                }
            }
            .buttonStyle(.uhSecondary)
            .disabled(rpe == w.rpe && notes == (w.notes ?? ""))
        }
        .uhCard()
    }

    private func loadLog(_ w: Workout) {
        guard !didLoadLog else { return }
        rpe = w.rpe
        notes = w.notes ?? ""
        didLoadLog = true
    }

    private func run(_ action: @escaping @MainActor () async -> Void) {
        Task {
            isBusy = true
            await action()
            isBusy = false
        }
    }
}
