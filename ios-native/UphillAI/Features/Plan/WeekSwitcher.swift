import SwiftUI

enum PlanViewMode: String, CaseIterable, Identifiable {
    case list = "List"
    case calendar = "Calendar"
    var id: String { rawValue }
}

struct WeekSwitcher: View {
    @Environment(\.accessibilityReduceMotion) private var reduceMotion
    let weeks: [Int]
    @Binding var selected: Int
    let currentWeek: Int
    var viewMode: Binding<PlanViewMode>? = nil

    var body: some View {
        HStack(alignment: .center) {
            if viewMode?.wrappedValue == .calendar {
                HStack(spacing: 6) {
                    Image(systemName: "calendar")
                        .font(.system(size: 14))
                        .foregroundStyle(UH.Palette.accentInk)
                    Text("Month Calendar")
                        .font(UH.TextStyle.sectionTitle)
                        .foregroundStyle(UH.Palette.ink)
                }
            } else {
                stepButton("chevron.left", label: L("Previous week"), to: selected - 1)
                Spacer()
                VStack(spacing: 2) {
                    Text("Week \(selected)")
                        .font(UH.TextStyle.sectionTitle)
                        .foregroundStyle(UH.Palette.ink)
                        .contentTransition(.numericText())
                    Text(selected == currentWeek ? L("This week") : " ")
                        .font(UH.TextStyle.eyebrow)
                        .foregroundStyle(UH.Palette.accentInk)
                }
                .accessibilityElement(children: .combine)
                Spacer()
                stepButton("chevron.right", label: L("Next week"), to: selected + 1)
            }

            if let viewMode {
                Spacer()
                Picker("View Mode", selection: viewMode) {
                    Image(systemName: "list.bullet")
                        .tag(PlanViewMode.list)
                    Image(systemName: "calendar")
                        .tag(PlanViewMode.calendar)
                }
                .pickerStyle(.segmented)
                .frame(width: 86)
                .accessibilityIdentifier("plan.viewMode")
            }
        }
        .sensoryFeedback(.selection, trigger: selected)
    }

    private func stepButton(_ icon: String, label: String, to week: Int) -> some View {
        Button {
            withAnimation(reduceMotion ? nil : UH.Motion.standard) { selected = week }
        } label: {
            Image(systemName: icon)
                .font(.body.weight(.semibold))
                .foregroundStyle(UH.Palette.ink)
                .frame(width: 44, height: 44)
        }
        .disabled(!weeks.contains(week))
        .accessibilityLabel(label)
    }
}
