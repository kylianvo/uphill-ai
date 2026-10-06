import SwiftUI

struct DistanceBadgeGrid: View {
    let badges: [DistanceBadge]
    var onSelectBadge: ((DistanceBadge) -> Void)? = nil

    private let topGridColumns = [
        GridItem(.flexible(), spacing: 8),
        GridItem(.flexible(), spacing: 8),
        GridItem(.flexible(), spacing: 8)
    ]

    var body: some View {
        VStack(alignment: .leading, spacing: UH.Space.small) {
            HStack {
                Text("DISTANCE BADGES & PERSONAL BESTS")
                    .font(.system(size: 11, weight: .bold, design: .monospaced))
                    .tracking(0.6)
                    .foregroundStyle(UH.Palette.muted)
                Spacer()
                let unlockedCount = badges.filter { $0.unlocked }.count
                Text("\(unlockedCount)/\(badges.count) UNLOCKED")
                    .font(.system(size: 10, weight: .bold, design: .monospaced))
                    .foregroundStyle(unlockedCount > 0 ? UH.Palette.accentInk : UH.Palette.muted)
            }

            // Row 1: 5K, 10K, HM
            // Row 2: FM, 50K, 100K
            // Row 3: 100 Miles (full width prominent)
            let topSix = badges.filter { $0.category != .hundredMiles }
            let hundredMiles = badges.first { $0.category == .hundredMiles }

            LazyVGrid(columns: topGridColumns, spacing: 8) {
                ForEach(topSix) { badge in
                    badgeTile(badge)
                }
            }

            if let hundredMiles {
                hundredMilesTile(hundredMiles)
            }
        }
    }

    private func badgeTile(_ badge: DistanceBadge) -> some View {
        Button {
            UIImpactFeedbackGenerator(style: .light).impactOccurred()
            onSelectBadge?(badge)
        } label: {
            VStack(spacing: 4) {
                HStack {
                    Text(badge.category.shortLabel)
                        .font(.system(size: 11, weight: .bold, design: .monospaced))
                        .foregroundStyle(badge.unlocked ? UH.Palette.ink : UH.Palette.muted)
                    Spacer()
                    Image(systemName: badge.unlocked ? "medal.fill" : "lock.fill")
                        .font(.system(size: 11))
                        .foregroundStyle(badge.unlocked ? Color(hex: "#f59e0b") : UH.Palette.muted.opacity(0.5))
                }

                Text(badge.formattedPB)
                    .font(.system(size: 14, weight: .bold, design: .monospaced))
                    .foregroundStyle(badge.unlocked ? UH.Palette.ink : UH.Palette.muted.opacity(0.6))
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .padding(.top, 2)

                if let race = badge.bestRaceName, badge.unlocked {
                    Text(race)
                        .font(.system(size: 9.5))
                        .foregroundStyle(UH.Palette.secondary)
                        .lineLimit(1)
                        .frame(maxWidth: .infinity, alignment: .leading)
                } else {
                    Text(badge.unlocked ? "PB Recorded" : "Locked")
                        .font(.system(size: 9.5))
                        .foregroundStyle(UH.Palette.muted)
                        .frame(maxWidth: .infinity, alignment: .leading)
                }
            }
            .padding(10)
            .background(badge.unlocked ? UH.Palette.card : UH.Palette.surface, in: RoundedRectangle(cornerRadius: UH.Radius.control))
            .overlay(
                RoundedRectangle(cornerRadius: UH.Radius.control)
                    .stroke(badge.unlocked ? UH.Palette.accentInk.opacity(0.4) : UH.Palette.line, lineWidth: badge.unlocked ? 1.5 : 1)
            )
        }
        .buttonStyle(.plain)
    }

    private func hundredMilesTile(_ badge: DistanceBadge) -> some View {
        Button {
            UIImpactFeedbackGenerator(style: .light).impactOccurred()
            onSelectBadge?(badge)
        } label: {
            HStack(spacing: 12) {
                ZStack {
                    Circle()
                        .fill(badge.unlocked ? UH.Palette.activeFill : UH.Palette.surface)
                        .frame(width: 36, height: 36)
                    Image(systemName: badge.unlocked ? "crown.fill" : "lock.fill")
                        .font(.system(size: 16))
                        .foregroundStyle(badge.unlocked ? Color(hex: "#f59e0b") : UH.Palette.muted.opacity(0.5))
                }

                VStack(alignment: .leading, spacing: 2) {
                    HStack {
                        Text("100 MILES (161 KM)")
                            .font(.system(size: 11, weight: .bold, design: .monospaced))
                            .foregroundStyle(badge.unlocked ? UH.Palette.ink : UH.Palette.muted)
                        Spacer()
                        if badge.unlocked {
                            Text("ULTRA PINNACLE")
                                .font(.system(size: 9, weight: .heavy, design: .monospaced))
                                .padding(.horizontal, 6)
                                .padding(.vertical, 2)
                                .background(Color(hex: "#f59e0b").opacity(0.16), in: Capsule())
                                .foregroundStyle(Color(hex: "#b45309"))
                        }
                    }

                    if let race = badge.bestRaceName, badge.unlocked {
                        Text("\(race) · PB \(badge.formattedPB)")
                            .font(UH.TextStyle.caption.weight(.semibold))
                            .foregroundStyle(UH.Palette.accentInk)
                    } else {
                        Text(badge.unlocked ? "PB \(badge.formattedPB)" : "Complete a 100-mile race to unlock")
                            .font(UH.TextStyle.caption)
                            .foregroundStyle(UH.Palette.secondary)
                    }
                }
            }
            .padding(UH.Space.small)
            .background(badge.unlocked ? UH.Palette.card : UH.Palette.surface, in: RoundedRectangle(cornerRadius: UH.Radius.control))
            .overlay(
                RoundedRectangle(cornerRadius: UH.Radius.control)
                    .stroke(badge.unlocked ? Color(hex: "#f59e0b").opacity(0.5) : UH.Palette.line, lineWidth: badge.unlocked ? 1.5 : 1)
            )
        }
        .buttonStyle(.plain)
    }
}
