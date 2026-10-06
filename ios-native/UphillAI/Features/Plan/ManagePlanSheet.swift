import SwiftUI

struct ManagePlanSheet: View {
    let model: PlanViewModel
    var deviceService: (any DeviceConnectionServicing)? = nil
    let onStartNew: () -> Void
    var onSchedule: () -> Void = {}
    var onTool: ((TrainingDestination) -> Void)? = nil
    @Environment(\.dismiss) private var dismiss
    @State private var plans: [Plan]?
    @State private var loadError: String?
    @State private var confirmNew = false
    @State private var confirmDelete = false
    @State private var isDeleting = false
    @State private var showExportCalendar = false
    @State private var connectionStatus: DeviceConnectionStatus? = nil

    init(model: PlanViewModel, deviceService: (any DeviceConnectionServicing)? = nil, onStartNew: @escaping () -> Void, onSchedule: @escaping () -> Void = {}, onTool: ((TrainingDestination) -> Void)? = nil, initialPlans: [Plan]? = nil, initialConfirmDelete: Bool = false) {
        self.model = model
        self.deviceService = deviceService
        self.onStartNew = onStartNew
        self.onSchedule = onSchedule
        self.onTool = onTool
        _plans = State(initialValue: initialPlans)
        _confirmDelete = State(initialValue: initialConfirmDelete)
    }

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

                    // Tools & Labs
                    toolsSection

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
            .sheet(isPresented: $showExportCalendar) {
                ExportCalendarSheet(model: model)
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
                if let deviceService {
                    connectionStatus = try? await deviceService.fetchStatus()
                }
            }
        }
        .presentationDetents([.medium, .large])
        .presentationBackground(UH.Palette.surface)
        .onDisappear {
            model.clearActionError()
            model.clearWatchSyncNotice()
        }
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

    // MARK: - Integrations (Watch & COROS Sync)

    private var integrationsSection: some View {
        let isConnected = connectionStatus?.isCorosConnected == true
        let deviceModel = connectionStatus?.coros?.deviceModel ?? "COROS APEX 2 Pro"

        return VStack(alignment: .leading, spacing: UH.Space.compact) {
            Text("INTEGRATIONS & WATCH SYNC")
                .font(.system(size: 10.5, weight: .bold, design: .monospaced))
                .tracking(0.5)
                .foregroundStyle(UH.Palette.muted)

            VStack(spacing: 0) {
                // Connection status row
                HStack(spacing: 8) {
                    Image(systemName: "applewatch")
                        .font(.system(size: 16))
                        .foregroundStyle(isConnected ? UH.Palette.accentInk : UH.Palette.muted)

                    VStack(alignment: .leading, spacing: 2) {
                        Text(isConnected ? deviceModel : "No watch connected")
                            .font(UH.TextStyle.label)
                            .foregroundStyle(UH.Palette.ink)
                        Text(isConnected ? "Connected in Profile" : "Connect in Profile")
                            .font(UH.TextStyle.caption)
                            .foregroundStyle(UH.Palette.secondary)
                    }

                    Spacer()

                    if isConnected {
                        HStack(spacing: 4) {
                            Circle().fill(UH.Palette.accentInk).frame(width: 6, height: 6)
                            Text("Connected")
                                .font(.system(size: 10, weight: .bold, design: .monospaced))
                                .foregroundStyle(UH.Palette.accentInk)
                        }
                        .padding(.horizontal, 7)
                        .padding(.vertical, 3)
                        .background(UH.Palette.activeFill, in: Capsule())
                    } else {
                        Text("Not connected")
                            .font(.system(size: 10, weight: .medium, design: .monospaced))
                            .foregroundStyle(UH.Palette.muted)
                            .padding(.horizontal, 6)
                            .padding(.vertical, 3)
                            .background(UH.Palette.hover, in: Capsule())
                    }
                }
                .padding(UH.Space.regular)

                Divider().overlay(UH.Palette.line.opacity(0.6))

                // Live Sync Watch row
                Button {
                    Task {
                        _ = await model.syncWatch()
                    }
                } label: {
                    HStack {
                        Label("Sync Watch Activities", systemImage: "arrow.triangle.2.circlepath")
                            .font(UH.TextStyle.label)
                            .foregroundStyle(UH.Palette.ink)
                        Spacer()
                        if model.isSyncingWatch {
                            ProgressView().controlSize(.small)
                        } else {
                            Text("Sync now")
                                .font(.system(size: 11, weight: .bold))
                                .foregroundStyle(UH.Palette.accentInk)
                                .padding(.horizontal, 8)
                                .padding(.vertical, 4)
                                .background(UH.Palette.activeFill, in: Capsule())
                        }
                    }
                    .padding(UH.Space.regular)
                }
                .buttonStyle(.plain)
                .disabled(model.isSyncingWatch)
                .accessibilityIdentifier("manage.syncWatch")

                if let notice = model.watchSyncNotice {
                    let isSuccess = notice.lowercased().contains("synced") || notice.lowercased().contains("up to date")
                    HStack(spacing: 6) {
                        Image(systemName: isSuccess ? "checkmark.circle.fill" : (isConnected ? "exclamationmark.circle.fill" : "info.circle"))
                            .foregroundStyle(isSuccess ? UH.Palette.accentInk : (isConnected ? UH.Palette.danger : UH.Palette.muted))
                            .font(.system(size: 12))
                        Text(notice)
                            .font(UH.TextStyle.caption)
                            .foregroundStyle(isSuccess ? UH.Palette.secondary : UH.Palette.danger)
                    }
                    .padding(.horizontal, UH.Space.regular)
                    .padding(.bottom, 8)
                }

                Divider().overlay(UH.Palette.line.opacity(0.6))

                // COROS Push Row ("Send this week")
                if let deviceService {
                    VStack(alignment: .leading, spacing: 6) {
                        HStack {
                            Text("SEND THIS WEEK")
                                .font(.system(size: 10, weight: .bold, design: .monospaced))
                                .foregroundStyle(UH.Palette.muted)
                            Spacer()
                        }
                        CorosPushButton(service: deviceService)
                        if isConnected {
                            CorosAttribution(deviceModel: deviceModel)
                        }
                    }
                    .padding(UH.Space.regular)

                    Divider().overlay(UH.Palette.line.opacity(0.6))
                }

                // Add to Calendar (.ics) row
                Button {
                    showExportCalendar = true
                } label: {
                    HStack {
                        Label("Add to Calendar (.ics)", systemImage: "calendar.badge.plus")
                            .font(UH.TextStyle.label)
                            .foregroundStyle(UH.Palette.ink)
                        Spacer()
                        Image(systemName: "chevron.right")
                            .font(.system(size: 11, weight: .semibold))
                            .foregroundStyle(UH.Palette.muted)
                    }
                    .padding(UH.Space.regular)
                }
                .buttonStyle(.plain)
                .accessibilityIdentifier("manage.exportCalendar")
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

    // MARK: - Tools & Labs

    private var toolsSection: some View {
        VStack(alignment: .leading, spacing: UH.Space.compact) {
            Text("TOOLS & LABS")
                .font(.system(size: 10.5, weight: .bold, design: .monospaced))
                .tracking(0.5)
                .foregroundStyle(UH.Palette.muted)

            VStack(spacing: 0) {
                Button {
                    onTool?(.goalDeterminer)
                    dismiss()
                } label: {
                    toolRow(title: "Goal Determiner", icon: "speedometer", desc: "Percentile finish estimation")
                }
                .buttonStyle(.plain)
                .accessibilityIdentifier("manage.tool.goalDeterminer")

                Divider().overlay(UH.Palette.line.opacity(0.6))

                Button {
                    onTool?(.gearVault)
                    dismiss()
                } label: {
                    toolRow(title: "Gear Vault", icon: "shoe.fill", desc: "Shoe rotation & recommendations")
                }
                .buttonStyle(.plain)
                .accessibilityIdentifier("manage.tool.gearVault")

                Divider().overlay(UH.Palette.line.opacity(0.6))

                Button {
                    onTool?(.nutritionLab)
                    dismiss()
                } label: {
                    toolRow(title: "Nutrition Lab", icon: "drop.fill", desc: "Precision fueling timeline")
                }
                .buttonStyle(.plain)
                .accessibilityIdentifier("manage.tool.nutritionLab")

                Divider().overlay(UH.Palette.line.opacity(0.6))

                Button {
                    onTool?(.gearVault)
                    dismiss()
                } label: {
                    toolRow(title: "Shoe Rotation", icon: "shoe", desc: "Active shoe rotation & wear")
                }
                .buttonStyle(.plain)
                .accessibilityIdentifier("manage.tool.shoeRotation")
            }
            .background(UH.Palette.card, in: RoundedRectangle(cornerRadius: UH.Radius.landing))
            .overlay(RoundedRectangle(cornerRadius: UH.Radius.landing).stroke(UH.Palette.line))
        }
    }

    private func toolRow(title: String, icon: String, desc: String) -> some View {
        HStack {
            Image(systemName: icon)
                .font(.system(size: 16))
                .foregroundStyle(UH.Palette.accentInk)
                .frame(width: 28)
            VStack(alignment: .leading, spacing: 2) {
                Text(title)
                    .font(UH.TextStyle.label)
                    .foregroundStyle(UH.Palette.ink)
                Text(desc)
                    .font(UH.TextStyle.caption)
                    .foregroundStyle(UH.Palette.secondary)
            }
            Spacer()
            Image(systemName: "chevron.right")
                .font(.system(size: 13, weight: .semibold))
                .foregroundStyle(UH.Palette.muted)
        }
        .padding(UH.Space.regular)
        .contentShape(Rectangle())
    }

}
