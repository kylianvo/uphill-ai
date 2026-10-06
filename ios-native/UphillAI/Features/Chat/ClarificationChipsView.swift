import SwiftUI

struct ClarificationChipsView: View {
    let options: [String]
    let onSelect: (String) -> Void
    let onDismiss: () -> Void

    var body: some View {
        VStack(alignment: .leading, spacing: 6) {
            HStack {
                Text("Pick one to continue:")
                    .font(UH.TextStyle.caption)
                    .foregroundStyle(UH.Palette.secondary)

                Spacer()

                Button {
                    onDismiss()
                } label: {
                    Image(systemName: "xmark")
                        .font(.caption2)
                        .foregroundStyle(UH.Palette.muted)
                        .padding(4)
                }
                .accessibilityLabel("Dismiss suggestions")
            }
            .padding(.horizontal, UH.Space.regular)

            ScrollView(.horizontal, showsIndicators: false) {
                HStack(spacing: UH.Space.compact) {
                    ForEach(options, id: \.self) { option in
                        Button {
                            UIImpactFeedbackGenerator(style: .light).impactOccurred()
                            onSelect(option)
                        } label: {
                            Text(option)
                                .font(UH.TextStyle.label)
                                .foregroundStyle(UH.Palette.ink)
                                .padding(.horizontal, 14)
                                .padding(.vertical, 8)
                                .background(Color.white.opacity(0.9), in: Capsule())
                                .overlay(Capsule().stroke(UH.Palette.line, lineWidth: 1))
                        }
                    }
                }
                .padding(.horizontal, UH.Space.regular)
                .padding(.bottom, 4)
            }
        }
        .padding(.vertical, 4)
    }
}
