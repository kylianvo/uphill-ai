import SwiftUI

struct ManagePlanSheet: View {
    let model: PlanViewModel
    @Environment(\.dismiss) private var dismiss
    @State private var plans: [Plan]?

    var body: some View {
        NavigationStack {
            List {
                Section("Recent plans") {
                    if let plans {
                        if plans.isEmpty {
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
                                    VStack(alignment: .leading, spacing: 2) {
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
                    Text("Plan settings, new plans, watch sync and calendar export are on the web for now.")
                        .font(UH.TextStyle.caption)
                        .foregroundStyle(UH.Palette.muted)
                }
            }
            .navigationTitle("Manage plan")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar { Button("Done") { dismiss() } }
            .task { plans = await model.recentPlans() }
        }
        .presentationDetents([.medium, .large])
        .onDisappear { model.clearActionError() }
    }

    private func raceDate(_ plan: Plan) -> String {
        guard let day = PlanCalendar.day(from: plan.raceDate) else { return plan.raceDate }
        return "Race " + day.formatted(.dateTime.day().month(.abbreviated).year())
    }
}
