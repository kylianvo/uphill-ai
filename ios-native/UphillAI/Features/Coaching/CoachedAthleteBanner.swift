import SwiftUI

struct CoachedAthleteBanner: View {
    let athlete: CoachedAthleteRow
    let onExit: () -> Void

    var body: some View {
        HStack(spacing: 12) {
            ZStack {
                Circle()
                    .fill(Color.orange.opacity(0.18))
                    .frame(width: 32, height: 32)
                Image(systemName: "person.badge.shield.checkmark.fill")
                    .font(.system(size: 15))
                    .foregroundStyle(Color.orange)
            }

            VStack(alignment: .leading, spacing: 1) {
                HStack(spacing: 6) {
                    Text("COACHING MODE")
                        .font(.system(size: 9.5, weight: .black, design: .monospaced))
                        .foregroundStyle(Color.orange)
                        .padding(.horizontal, 5)
                        .padding(.vertical, 1.5)
                        .background(Color.orange.opacity(0.15))
                        .clipShape(Capsule())
                    Text(athlete.displayName)
                        .font(UH.TextStyle.label)
                        .foregroundStyle(UH.Palette.ink)
                        .lineLimit(1)
                }
                Text("Viewing & managing plan as coach")
                    .font(UH.TextStyle.caption)
                    .foregroundStyle(UH.Palette.secondary)
            }

            Spacer()

            Button(action: onExit) {
                HStack(spacing: 4) {
                    Text("Exit")
                        .font(.system(size: 12, weight: .bold))
                    Image(systemName: "xmark.circle.fill")
                        .font(.system(size: 12))
                }
                .padding(.horizontal, 10)
                .padding(.vertical, 6)
                .background(UH.Palette.hover)
                .foregroundStyle(UH.Palette.ink)
                .clipShape(Capsule())
                .overlay(
                    Capsule()
                        .stroke(UH.Palette.line, lineWidth: 1)
                )
            }
            .buttonStyle(.plain)
        }
        .padding(.horizontal, 14)
        .padding(.vertical, 10)
        .background(
            RoundedRectangle(cornerRadius: UH.Radius.panel)
                .fill(UH.Palette.surface.opacity(0.95))
                .shadow(color: Color.black.opacity(0.08), radius: 6, y: 3)
        )
        .overlay(
            RoundedRectangle(cornerRadius: UH.Radius.panel)
                .stroke(Color.orange.opacity(0.4), lineWidth: 1.5)
        )
        .padding(.horizontal, UH.Space.small)
        .padding(.top, 4)
    }
}
