import SwiftUI

struct ManagePlanSheet: View {
    let model: PlanViewModel
    let onStartNew: () -> Void
    var onSchedule: () -> Void = {}
    @Environment(\.dismiss) private var dismiss
    @State private var plans: [Plan]?
    @State private var loadError: String?
    @State private var confirmNew = false
    @State private var confirmDelete = false
    @State private var isDeleting = false

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: UH.Space.regular) {
                    if let loadError {
                        HStack(spacing: UH.Space.compact) {
                            Image(systemName: "exclamationmark.triangle.fill")
                                .foregroundStyle(UH.Palette.danger)
                            Text(loadError)
                                .font(UH.TextStyle.caption)
                                .foregroundStyle(UH.Palette.danger)
                        }
                        .padding(UH.Space.small)
                        .frame(maxWidth: .infinity, alignment: .leading)
                        .background(UH.Palette.danger.opacity(0.1), in: RoundedRectangle(cornerRadius: UH.Radius.control))
                    }

                    if let actionError = model.actionError {
                        HStack(spacing: UH.Space.compact) {
                            Image(systemName: "exclamationmark.triangle.fill")
                                .foregroundStyle(UH.Palette.danger)
                            Text(actionError)
                                .font(UH.TextStyle.caption)
                                .foregroundStyle(UH.Palette.danger)
                        }
                        .padding(UH.Space.small)
                        .frame(maxWidth: .infinity, alignment: .leading)
                        .background(UH.Palette.danger.opacity(0.1), in: RoundedRectangle(cornerRadius: UH.Radius.control))
                    }

                    // 1. Recent Plans Section
                    recentPlansSection

                    // 2. Plan Actions (New Plan, Plan Settings)
                    planActionsSection

                    // 3. Delete Plan Section
                    if model.snapshot != nil {
                        deletePlanSection
                    }

                    // 4. Integrations / Coming Soon
                    integrationsSection
                }
                .padding(UH.Space.regular)
            }
            .background(UH.Palette.surface)
            .navigationTitle("Manage Plan")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .confirmationAction) {
                    Button("Done") { dismiss() }
                }
            }
            .confirmationDialog("Start a new plan?", isPresented: $confirmNew, titleVisibility: .visible) {
                Button("Start new plan") { onStartNew(); dismiss() }
                Button("Cancel", role: .cancel) {}
            } message: {
                Text("Your current plan stays in Recent plans. The new plan becomes your active plan.")
            }
            .confirmationDialog("Delete Training Plan?", isPresented: $confirmDelete, titleVisibility: .visible) {
                Button("Delete Plan", role: .destructive) {
                    Task {
                        guard let id = model.snapshot?.plan.id else { return }
                        isDeleting = true
                        let ok = await model.deletePlan(id: id)
                        isDeleting = false
                        if ok { dismiss() }
                    }
                }
                Button("Keep Plan", role: .cancel) {}
            } message: {
                Text("This will permanently delete your training plan and all scheduled workouts. This action cannot be undone.")
            }
            .disabled(isDeleting)
            .overlay {
                if isDeleting {
                    ProgressView("Deleting plan…")
                        .padding()
                        .background(UH.Palette.card.opacity(0.9), in: RoundedRectangle(cornerRadius: UH.Radius.landing))
                }
            }
            .task {
                do {
                    plans = try await model.recentPlans()
                } catch let error as APIError {
                    if case .transport = error { loadError = PlanViewModel.offlineMessage } else { loadError = error.userMessage }
                } catch {
                    loadError = error.localizedDescription
                }
            }
        }
        .presentationDetents([.medium, .large])
        .presentationBackground(UH.Palette.surface)
        .onDisappear { model.clearActionError() }
        .accessibilityIdentifier("manage.sheet")
    }

    // MARK: - Recent Plans

    private var recentPlansSection: some View {
        VStack(alignment: .leading, spacing: UH.Space.compact) {
            Text("RECENT PLANS")
                .font(.system(size: 10.5, weight: .bold, design: .monospaced))
                .tracking(0.5)
                .foregroundStyle(UH.Palette.muted)

            if let plans {
                if plans.isEmpty {
                    Text("No plans found.")
                        .font(UH.TextStyle.caption)
                        .foregroundStyle(UH.Palette.secondary)
                        .padding(UH.Space.small)
                } else {
                    VStack(spacing: 8) {
                        ForEach(plans) { plan in
                            let isActive = plan.id == model.snapshot?.plan.id
                            Button {
                                if !isActive {
                                    Task {
                                        await model.select(plan)
                                        if model.actionError == nil { dismiss() }
                                    }
                                }
                            } label: {
                                HStack {
                                    VStack(alignment: .leading, spacing: 3) {
                                        HStack(spacing: 6) {
                                            Text(plan.raceName)
                                                .font(UH.TextStyle.label)
                                                .foregroundStyle(UH.Palette.ink)
                                            if isActive {
                                                Text("ACTIVE")
                                                    .font(.system(size: 9, weight: .bold))
                                                    .tracking(0.5)
                                                    .foregroundStyle(UH.Palette.accentInk)
                                                    .padding(.horizontal, 5)
                                                    .padding(.vertical, 1.5)
                                                    .background(UH.Palette.activeFill, in: Capsule())
                                            }
                                        }
                                        Text("\(raceDate(plan)) · \(plan.totalWeeks) weeks")
                                            .font(UH.TextStyle.caption)
                                            .foregroundStyle(UH.Palette.secondary)
                                    }

                                    Spacer()

                                    if isActive {
                                        Image(systemName: "checkmark.circle.fill")
                                            .foregroundStyle(UH.Palette.accentInk)
                                            .font(.system(size: 18))
                                    } else {
                                        Image(systemName: "chevron.right")
                                            .font(.system(size: 13, weight: .semibold))
                                            .foregroundStyle(UH.Palette.muted)
                                    }
                                }
                                .padding(UH.Space.small)
                                .background(UH.Palette.card, in: RoundedRectangle(cornerRadius: UH.Radius.landing))
                                .overlay(
                                    RoundedRectangle(cornerRadius: UH.Radius.landing)
                                        .stroke(isActive ? UH.Palette.accentInk.opacity(0.8) : UH.Palette.line, lineWidth: isActive ? 1.5 : 1)
                                )
                            }
                            .buttonStyle(.plain)
                            .disabled(isActive)
                            .accessibilityIdentifier("manage.plan.\(plan.id)")
                            .accessibilityAddTraits(isActive ? .isSelected : [])
                        }
                    }
                }
            } else {
                HStack {
                    ProgressView()
                    Text("Loading plans…")
                        .font(UH.TextStyle.caption)
                        .foregroundStyle(UH.Palette.secondary)
                }
                .padding(UH.Space.small)
            }
        }
    }

    // MARK: - Plan Actions

    private var planActionsSection: some View {
        VStack(alignment: .leading, spacing: UH.Space.compact) {
            Text("PLAN ACTIONS")
                .font(.system(size: 10.5, weight: .bold, design: .monospaced))
                .tracking(0.5)
                .foregroundStyle(UH.Palette.muted)

            VStack(spacing: 0) {
                Button {
                    confirmNew = true
                } label: {
                    HStack {
                        Label("New Plan", systemImage: "plus.circle")
                            .font(UH.TextStyle.label)
                            .foregroundStyle(UH.Palette.ink)
                        Spacer()
                        Image(systemName: "chevron.right")
                            .font(.system(size: 13, weight: .semibold))
                            .foregroundStyle(UH.Palette.muted)
                    }
                    .padding(UH.Space.regular)
                    .contentShape(Rectangle())
                }
                .buttonStyle(.plain)
                .accessibilityIdentifier("manage.startNew")

                Divider().overlay(UH.Palette.line.opacity(0.6))

                Button {
                    onSchedule()
                    dismiss()
                } label: {
                    HStack {
                        Label("Plan Settings", systemImage: "gearshape")
                            .font(UH.TextStyle.label)
                            .foregroundStyle(UH.Palette.ink)
                        Spacer()
                        Image(systemName: "chevron.right")
                            .font(.system(size: 13, weight: .semibold))
                            .foregroundStyle(UH.Palette.muted)
                    }
                    .padding(UH.Space.regular)
                    .contentShape(Rectangle())
                }
                .buttonStyle(.plain)
                .accessibilityIdentifier("manage.settings")
            }
            .background(UH.Palette.card, in: RoundedRectangle(cornerRadius: UH.Radius.landing))
            .overlay(RoundedRectangle(cornerRadius: UH.Radius.landing).stroke(UH.Palette.line))
        }
    }

    // MARK: - Delete Plan

    private var deletePlanSection: some View {
        VStack(alignment: .leading, spacing: UH.Space.compact) {
            Text("DANGER ZONE")
                .font(.system(size: 10.5, weight: .bold, design: .monospaced))
                .tracking(0.5)
                .foregroundStyle(UH.Palette.danger)

            Button {
                confirmDelete = true
            } label: {
                HStack {
                    Label("Delete Training Plan", systemImage: "trash")
                        .font(UH.TextStyle.label)
                        .foregroundStyle(UH.Palette.danger)
                    Spacer()
                }
                .padding(UH.Space.regular)
                .frame(maxWidth: .infinity, alignment: .leading)
                .background(UH.Palette.card, in: RoundedRectangle(cornerRadius: UH.Radius.landing))
                .overlay(RoundedRectangle(cornerRadius: UH.Radius.landing).stroke(UH.Palette.danger.opacity(0.3)))
            }
            .buttonStyle(.plain)
            .accessibilityIdentifier("manage.deletePlan")
        }
    }

    // MARK: - Integrations (Coming Soon)

    private var integrationsSection: some View {
        VStack(alignment: .leading, spacing: UH.Space.compact) {
            Text("INTEGRATIONS")
                .font(.system(size: 10.5, weight: .bold, design: .monospaced))
                .tracking(0.5)
                .foregroundStyle(UH.Palette.muted)

            VStack(spacing: 0) {
                comingSoonRow(title: "Sync Watch", icon: "applewatch")
                Divider().overlay(UH.Palette.line.opacity(0.6))
                comingSoonRow(title: "Add to Calendar (.ics)", icon: "calendar.badge.plus")
            }
            .background(UH.Palette.card, in: RoundedRectangle(cornerRadius: UH.Radius.landing))
            .overlay(RoundedRectangle(cornerRadius: UH.Radius.landing).stroke(UH.Palette.line))
        }
    }

    private func comingSoonRow(title: String, icon: String) -> some View {
        HStack {
            Label(title, systemImage: icon)
                .font(UH.TextStyle.label)
                .foregroundStyle(UH.Palette.ink.opacity(0.5))
            Spacer()
            Text("Coming soon")
                .font(.system(size: 10, weight: .bold, design: .monospaced))
                .foregroundStyle(UH.Palette.muted)
                .padding(.horizontal, 6)
                .padding(.vertical, 2)
                .background(UH.Palette.hover, in: Capsule())
        }
        .padding(UH.Space.regular)
        .opacity(0.6)
        .accessibilityElement(children: .combine)
        .accessibilityLabel("\(title) Coming soon")
    }

    private func raceDate(_ plan: Plan) -> String {
        guard let day = PlanCalendar.day(from: plan.raceDate) else { return plan.raceDate }
        return "Race " + day.formatted(.dateTime.day().month(.abbreviated).year())
    }
}
