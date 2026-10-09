import SwiftUI

struct CoachWorkoutTypeOption: Identifiable, Equatable {
    var id: String { value }
    let value: String
    let labelEn: String
    let labelVi: String
    let color: Color

    static let all: [CoachWorkoutTypeOption] = [
        CoachWorkoutTypeOption(value: "Easy", labelEn: "Easy", labelVi: "Easy Run", color: Color.blue),
        CoachWorkoutTypeOption(value: "Recovery", labelEn: "Recovery", labelVi: "Recovery Run", color: Color.blue),
        CoachWorkoutTypeOption(value: "Long Run", labelEn: "Long Run", labelVi: "Long Run", color: Color.green),
        CoachWorkoutTypeOption(value: "Aerobic Capacity", labelEn: "Aerobic Capacity", labelVi: "Aerobic Capacity", color: Color.blue),
        CoachWorkoutTypeOption(value: "Tempo", labelEn: "Tempo", labelVi: "Tempo", color: Color.orange),
        CoachWorkoutTypeOption(value: "Threshold", labelEn: "Threshold", labelVi: "Threshold", color: Color.orange),
        CoachWorkoutTypeOption(value: "Interval", labelEn: "Interval", labelVi: "Interval", color: Color.red),
        CoachWorkoutTypeOption(value: "Muscular Endurance", labelEn: "Muscular Endurance", labelVi: "Muscular Endurance (ME)", color: Color.purple),
        CoachWorkoutTypeOption(value: "Strength", labelEn: "Strength", labelVi: "Strength", color: Color.purple),
        CoachWorkoutTypeOption(value: "Cross-Training", labelEn: "Cross-Training", labelVi: "Cross-Training", color: Color.teal),
    ]

    static func find(_ value: String) -> CoachWorkoutTypeOption? {
        all.first { $0.value.lowercased() == value.lowercased() }
    }
}

struct CoachWorkoutTypePicker: View {
    @Binding var selection: String

    var body: some View {
        Menu {
            ForEach(CoachWorkoutTypeOption.all) { opt in
                Button {
                    selection = opt.value
                } label: {
                    HStack {
                        Text(AppLanguage.current == .vi ? opt.labelVi : opt.labelEn)
                        if selection.lowercased() == opt.value.lowercased() {
                            Image(systemName: "checkmark")
                        }
                    }
                }
            }
        } label: {
            HStack(spacing: 8) {
                let current = CoachWorkoutTypeOption.find(selection) ?? CoachWorkoutTypeOption.all[0]
                Circle()
                    .fill(current.color)
                    .frame(width: 10, height: 10)
                Text(AppLanguage.current == .vi ? current.labelVi : current.labelEn)
                    .font(UH.TextStyle.body)
                    .foregroundStyle(UH.Palette.ink)
                Spacer()
                Image(systemName: "chevron.up.chevron.down")
                    .font(.system(size: 11))
                    .foregroundStyle(UH.Palette.secondary)
            }
            .padding(.horizontal, 12)
            .padding(.vertical, 10)
            .background(UH.Palette.hover)
            .clipShape(RoundedRectangle(cornerRadius: UH.Radius.control))
            .overlay(
                RoundedRectangle(cornerRadius: UH.Radius.control)
                    .stroke(UH.Palette.line, lineWidth: 1)
            )
        }
    }
}
