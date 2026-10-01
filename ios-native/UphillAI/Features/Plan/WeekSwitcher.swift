import SwiftUI

struct WeekSwitcher: View {
    @Environment(\.accessibilityReduceMotion) private var reduceMotion
    let weeks: [Int]
    @Binding var selected: Int
    let currentWeek: Int

    var body: some View {
        HStack {
            stepButton("chevron.left", label: "Previous week", to: selected - 1)
            Spacer()
            VStack(spacing: UH.Space.compact) {
                Text("Week \(selected)")
                    .font(UH.TextStyle.sectionTitle)
                    .foregroundStyle(UH.Palette.ink)
                    .contentTransition(.numericText())
                Text(selected == currentWeek ? "This week" : " ")
                    .font(UH.TextStyle.eyebrow)
                    .foregroundStyle(UH.Palette.accentInk)
            }
            .accessibilityElement(children: .combine)
            Spacer()
            stepButton("chevron.right", label: "Next week", to: selected + 1)
        }
        .sensoryFeedback(.selection, trigger: selected)
    }

    private func stepButton(_ icon: String, label: String, to week: Int) -> some View {
        Button {
            withAnimation(reduceMotion ? nil : UH.Motion.standard) { selected = week }
        } label: {
            Image(systemName: icon)
                .font(.body.weight(.semibold))
                .frame(width: 44, height: 44)
        }
        .disabled(!weeks.contains(week))
        .accessibilityLabel(label)
    }
}
