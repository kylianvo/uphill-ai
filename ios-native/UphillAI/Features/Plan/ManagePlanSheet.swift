import SwiftUI

struct ManagePlanSheet: View {
    let model: PlanViewModel
    let onStartNew: () -> Void
    var onSchedule: () -> Void = {}
    @Environment(\.dismiss) private var dismiss
    @State private var plans: [Plan]?
    @State private var loadError: String?
    @State private var confirmNew = false

    var body: some View {
        NavigationStack {
            List {
                Section("Recent plans") {
                    if let loadError {
                        Text(loadError).font(UH.TextStyle.caption).foregroundStyle(UH.Palette.danger)
                    } else if let plans {
                        if plans.allSatisfy({ $0.id == model.snapshot?.plan.id }) {
                            Text("No other plans yet.").foregroundStyle(UH.Palette.secondary)
                        }
                        ForEach(plans) { plan in
                            let isActive = plan.id == model.snapshot?.plan.id
                            Button {
                                Task {
                                    await model.select(plan)
                                    if model.actionError == nil { dismiss() }
                                }
                            } label: {
                                HStack {
                                    VStack(alignment: .leading, spacing: UH.Space.compact) {
                                        Text(plan.raceName).font(UH.TextStyle.label).foregroundStyle(UH.Palette.ink)
                                        Text(raceDate(plan)).font(UH.TextStyle.caption).foregroundStyle(UH.Palette.secondary)
                                    }
                                    Spacer()
                                    if isActive {
                                        Image(systemName: "checkmark").foregroundStyle(UH.Palette.accentInk)
                                    }
                                }
                                .frame(minHeight: 44)
                            }
                            .disabled(isActive)
                            .accessibilityAddTraits(isActive ? .isSelected : [])
                        }
                    } else {
                        ProgressView()
                    }
                }
                if let error = model.actionError {
                    Text(error).font(UH.TextStyle.caption).foregroundStyle(UH.Palette.danger)
                }
                Section {
                    Button("Schedule") { onSchedule(); dismiss() }.frame(minHeight: 44)
                }.listRowBackground(UH.Palette.card)
                Section("New plan") {
                    Button("Start new plan") { confirmNew = true }
                        .frame(minHeight: 44).accessibilityIdentifier("manage.startNew")
                }
                .listRowBackground(UH.Palette.card)
                Section {
                    Text("Plan settings, watch sync and calendar export are on the web for now.")
                        .font(UH.TextStyle.caption)
                        .foregroundStyle(UH.Palette.muted)
                }
            }
            .listRowBackground(UH.Palette.card)
            .listSectionSpacing(UH.Space.section)
            .tint(UH.Palette.accentInk)
            .scrollContentBackground(.hidden)
            .background(UH.Palette.surface)
            .confirmationDialog("Start a new plan?", isPresented: $confirmNew, titleVisibility: .visible) {
                Button("Start new plan") { onStartNew(); dismiss() }
                Button("Cancel", role: .cancel) {}
            } message: {
                Text("Your current plan stays in Recent plans. The new plan becomes your active plan.")
            }
            .navigationTitle("Manage plan")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar { Button("Done") { dismiss() } }
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
    }

    private func raceDate(_ plan: Plan) -> String {
        guard let day = PlanCalendar.day(from: plan.raceDate) else { return plan.raceDate }
        return "Race " + day.formatted(.dateTime.day().month(.abbreviated).year())
    }
}
