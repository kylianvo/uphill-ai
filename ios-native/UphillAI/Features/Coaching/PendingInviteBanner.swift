import SwiftUI

struct PendingInviteBanner: View {
    let invites: [CoachingInvite]
    let onAccept: (Int) -> Void
    let onDecline: (Int) -> Void

    var body: some View {
        if !invites.isEmpty {
            VStack(spacing: 8) {
                ForEach(invites) { inv in
                    VStack(alignment: .leading, spacing: 10) {
                        HStack(alignment: .center, spacing: 8) {
                            Image(systemName: "envelope.badge.fill")
                                .font(.system(size: 16))
                                .foregroundStyle(Color.green)

                            VStack(alignment: .leading, spacing: 2) {
                                Text("Coaching Invitation")
                                    .font(.system(size: 11, weight: .bold, design: .monospaced))
                                    .foregroundStyle(Color.green)
                                Text("\(inv.displayCoachName) invited you to be coached")
                                    .font(UH.TextStyle.label)
                                    .foregroundStyle(UH.Palette.ink)
                            }

                            Spacer()
                        }

                        HStack(spacing: 10) {
                            Button {
                                onAccept(inv.id)
                            } label: {
                                Text("Accept")
                                    .font(UH.TextStyle.caption)
                                    .frame(maxWidth: .infinity)
                                    .padding(.vertical, 8)
                            }
                            .buttonStyle(.uhPrimary)

                            Button {
                                onDecline(inv.id)
                            } label: {
                                Text("Decline")
                                    .font(UH.TextStyle.caption)
                                    .foregroundStyle(UH.Palette.secondary)
                                    .frame(maxWidth: .infinity)
                                    .padding(.vertical, 8)
                                    .background(UH.Palette.hover)
                                    .clipShape(RoundedRectangle(cornerRadius: UH.Radius.control))
                                    .overlay(
                                        RoundedRectangle(cornerRadius: UH.Radius.control)
                                            .stroke(UH.Palette.line, lineWidth: 1)
                                    )
                            }
                            .buttonStyle(.plain)
                        }
                    }
                    .padding(14)
                    .background(
                        RoundedRectangle(cornerRadius: UH.Radius.panel)
                            .fill(Color.green.opacity(0.08))
                    )
                    .overlay(
                        RoundedRectangle(cornerRadius: UH.Radius.panel)
                            .stroke(Color.green.opacity(0.35), lineWidth: 1)
                    )
                }
            }
            .padding(.horizontal, UH.Space.regular)
            .padding(.bottom, UH.Space.small)
        }
    }
}
