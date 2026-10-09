import SwiftUI

struct WeekReviewSheet: View {
    let model: PlanViewModel
    let week: Int
    @Environment(\.dismiss) private var dismiss
    @State private var phase = Phase.loading

    private enum Phase { case loading, loaded(WeekReview), failed(String) }

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: UH.Space.regular) {
                    switch phase {
                    case .loading:
                        placeholder.redacted(reason: .placeholder)
                    case .loaded(let review):
                        reviewContent(review)
                    case .failed(let message):
                        VStack(spacing: UH.Space.regular) {
                            Text(message)
                                .foregroundStyle(UH.Palette.secondary)
                                .multilineTextAlignment(.center)
                            Button("Try again") {
                                Task { await load() }
                            }
                            .buttonStyle(.uhPrimary)
                            .frame(maxWidth: 220)
                        }
                        .frame(maxWidth: .infinity)
                    }
                }
                .padding(UH.Space.regular)
            }
            .background(UH.Palette.surface)
            .navigationTitle("Week \(week) Review")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .topBarTrailing) {
                    Button("Done") { dismiss() }
                        .font(UH.TextStyle.label)
                        .foregroundStyle(UH.Palette.ink)
                }
            }
            .task { await load() }
        }
        .presentationDetents([.large])
        .presentationBackground(UH.Palette.surface)
    }

    private var placeholder: some View {
        VStack(alignment: .leading, spacing: UH.Space.regular) {
            Circle().frame(width: 96, height: 96)
            Text("Loading week summary and performance metrics from Coach Uphill…")
            ForEach(0..<4, id: \.self) { _ in
                RoundedRectangle(cornerRadius: 12).frame(height: 52)
            }
        }
    }

    private func reviewContent(_ review: WeekReview) -> some View {
        VStack(alignment: .leading, spacing: UH.Space.regular) {
            // 1. Hero Completion Card
            completionHeroCard(review)

            // 2. Volume Comparison Card
            volumeComparisonCard(review)

            // 3. Coach Narrative
            if let narrative = review.narrative {
                narrativeCard(narrative)
            }

            // 4. Per-Workout Execution
            workoutListCard(review.perWorkout)
        }
    }

    // MARK: - Completion Hero

    private func completionHeroCard(_ review: WeekReview) -> some View {
        let pct = review.checkboxCompletionPct ?? review.completionPct
        let doneCount = review.perWorkout.filter { $0.actual.state == "matched" || $0.actual.state == "checkbox_only" }.count
        let totalCount = review.perWorkout.count

        return HStack(spacing: UH.Space.regular) {
            Gauge(value: min(max(pct, 0), 100), in: 0...100) {
                Text("Completion")
            } currentValueLabel: {
                Text("\(Int(pct))%")
                    .font(.system(size: 15, weight: .bold, design: .monospaced))
                    .foregroundStyle(UH.Palette.ink)
            }
            .gaugeStyle(.accessoryCircularCapacity)
            .tint(pct >= 80 ? UH.Palette.accentInk : (pct >= 50 ? UH.Palette.secondary : UH.Palette.danger))
            .scaleEffect(1.2)
            .frame(width: 68, height: 68)

            VStack(alignment: .leading, spacing: 3) {
                Text(pct >= 80 ? L("Great week of training") : (pct >= 50 ? L("Solid consistency") : L("Recovery & catch-up")))
                    .font(UH.TextStyle.sectionTitle)
                    .foregroundStyle(UH.Palette.ink)

                Text("\(doneCount) of \(totalCount) workouts completed")
                    .font(UH.TextStyle.caption)
                    .foregroundStyle(UH.Palette.secondary)
            }

            Spacer()
        }
        .trainingCard()
    }

    // MARK: - Volume Comparison

    private func volumeComparisonCard(_ review: WeekReview) -> some View {
        let plannedDist = review.planned?.distanceKm ?? 0
        let actualDist = review.actual?.totalActualKm ?? review.perWorkout.compactMap { $0.actual.distanceKm }.reduce(0, +)

        let plannedMins = review.planned?.durationMinutes ?? 0
        let actualMins = review.actual?.totalActualMinutes ?? review.perWorkout.compactMap { $0.actual.durationMinutes }.reduce(0, +)

        let plannedVert = review.planned?.elevationGainM ?? 0
        let actualVert = review.actual?.totalActualVertM ?? 0

        return VStack(alignment: .leading, spacing: UH.Space.small) {
            Text("VOLUME COMPARISON")
                .font(.system(size: 10, weight: .bold, design: .monospaced))
                .tracking(0.5)
                .foregroundStyle(UH.Palette.muted)

            LazyVGrid(columns: [GridItem(.flexible()), GridItem(.flexible()), GridItem(.flexible())], spacing: UH.Space.compact) {
                metricCell(
                    title: L("DISTANCE"),
                    actual: String(format: "%.1f km", actualDist),
                    planned: plannedDist > 0 ? String(format: "%.0f km", plannedDist) : nil
                )

                metricCell(
                    title: L("TIME"),
                    actual: formatHoursMins(actualMins),
                    planned: plannedMins > 0 ? formatHoursMins(plannedMins) : nil
                )

                metricCell(
                    title: L("VERT"),
                    actual: "\(Int(actualVert)) m",
                    planned: plannedVert > 0 ? "\(Int(plannedVert)) m" : nil
                )
            }

            if let unplanned = review.actual?.unplannedCount, unplanned > 0 {
                HStack(spacing: 5) {
                    Image(systemName: "plus.circle.fill")
                        .foregroundStyle(UH.Palette.accentInk)
                        .font(.system(size: 11))
                    let extraKm = review.actual?.unplannedKm ?? 0
                    let plural = unplanned > 1 ? "s" : ""
                    let kmStr = String(format: "%.1f", extraKm)
                    Text("Includes \(unplanned) extra session\(plural) (+\(kmStr) km)")
                        .font(UH.TextStyle.caption)
                        .foregroundStyle(UH.Palette.secondary)
                }
                .padding(.top, 2)
            }
        }
        .trainingCard()
    }

    private func metricCell(title: String, actual: String, planned: String?) -> some View {
        VStack(alignment: .leading, spacing: 2) {
            Text(title)
                .font(.system(size: 9.5, weight: .bold, design: .monospaced))
                .foregroundStyle(UH.Palette.muted)
            Text(actual)
                .font(.system(size: 13.5, weight: .bold, design: .monospaced))
                .foregroundStyle(UH.Palette.ink)
            if let planned {
                Text("Goal: \(planned)")
                    .font(.system(size: 10, design: .monospaced))
                    .foregroundStyle(UH.Palette.secondary)
            }
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(8)
        .background(UH.Palette.surface, in: RoundedRectangle(cornerRadius: 8))
        .overlay(RoundedRectangle(cornerRadius: 8).stroke(UH.Palette.line, lineWidth: 1))
    }

    private func formatHoursMins(_ totalMins: Double) -> String {
        let hrs = Int(totalMins) / 60
        let mins = Int(totalMins) % 60
        return hrs > 0 ? "\(hrs)h \(mins)m" : "\(mins)m"
    }

    // MARK: - Coach Narrative

    private func narrativeCard(_ narrative: WeekNarrative) -> some View {
        VStack(alignment: .leading, spacing: UH.Space.small) {
            HStack(spacing: 6) {
                Image(systemName: "sparkles")
                    .foregroundStyle(UH.Palette.accentInk)
                Text("COACH UPHILL TAKEAWAY")
                    .font(.system(size: 10, weight: .bold, design: .monospaced))
                    .tracking(0.5)
                    .foregroundStyle(UH.Palette.muted)
            }

            if let summary = narrative.summary, !summary.isEmpty {
                Text(summary)
                    .font(UH.TextStyle.body)
                    .foregroundStyle(UH.Palette.ink)
                    .fixedSize(horizontal: false, vertical: true)
            }

            if !narrative.highlights.isEmpty {
                VStack(alignment: .leading, spacing: 6) {
                    Text("Went well")
                        .font(UH.TextStyle.sectionTitle)
                        .foregroundStyle(UH.Palette.ink)

                    ForEach(narrative.highlights, id: \.self) { item in
                        HStack(alignment: .firstTextBaseline, spacing: 8) {
                            Image(systemName: "checkmark.circle.fill")
                                .font(.system(size: 12))
                                .foregroundStyle(Color(red: 0.05, green: 0.65, blue: 0.45))
                            Text(item)
                                .font(UH.TextStyle.caption)
                                .foregroundStyle(UH.Palette.ink)
                                .fixedSize(horizontal: false, vertical: true)
                        }
                    }
                }
                .padding(.top, 4)
            }

            if !narrative.watch.isEmpty {
                VStack(alignment: .leading, spacing: 6) {
                    Text("Keep an eye on")
                        .font(UH.TextStyle.sectionTitle)
                        .foregroundStyle(UH.Palette.ink)

                    ForEach(narrative.watch, id: \.self) { item in
                        HStack(alignment: .firstTextBaseline, spacing: 8) {
                            Image(systemName: "exclamationmark.triangle.fill")
                                .font(.system(size: 12))
                                .foregroundStyle(Color(red: 0.9, green: 0.6, blue: 0.1))
                            Text(item)
                                .font(UH.TextStyle.caption)
                                .foregroundStyle(UH.Palette.ink)
                                .fixedSize(horizontal: false, vertical: true)
                        }
                    }
                }
                .padding(.top, 4)
            }
        }
        .trainingCard()
    }

    // MARK: - Per-Workout List

    private func workoutListCard(_ entries: [WeekReviewEntry]) -> some View {
        VStack(alignment: .leading, spacing: UH.Space.small) {
            Text("SESSION BREAKDOWN")
                .font(.system(size: 10, weight: .bold, design: .monospaced))
                .tracking(0.5)
                .foregroundStyle(UH.Palette.muted)

            VStack(spacing: 0) {
                ForEach(Array(entries.enumerated()), id: \.element.id) { index, entry in
                    workoutRow(entry)
                    if index < entries.count - 1 {
                        Divider()
                            .padding(.vertical, 6)
                    }
                }
            }
        }
        .trainingCard()
    }

    private func workoutRow(_ entry: WeekReviewEntry) -> some View {
        HStack(alignment: .center) {
            VStack(alignment: .leading, spacing: 3) {
                HStack(spacing: 6) {
                    if let day = entry.dayOfWeek {
                        Text(day.prefix(3).uppercased())
                            .font(.system(size: 10, weight: .bold, design: .monospaced))
                            .foregroundStyle(UH.Palette.secondary)
                    }
                    Text(entry.title ?? entry.type ?? L("Workout"))
                        .font(UH.TextStyle.label)
                        .foregroundStyle(UH.Palette.ink)
                }

                HStack(spacing: 6) {
                    if let km = entry.actual.distanceKm, km > 0 {
                        Text(String(format: "%.1f km", km))
                            .font(.system(size: 11, design: .monospaced))
                            .foregroundStyle(UH.Palette.secondary)
                    }
                    if let mins = entry.actual.durationMinutes, mins > 0 {
                        Text("· \(Int(mins))m")
                            .font(.system(size: 11, design: .monospaced))
                            .foregroundStyle(UH.Palette.secondary)
                    }
                }
            }

            Spacer()

            statusBadge(for: entry.actual.state)
        }
        .padding(.vertical, 4)
    }

    @ViewBuilder
    private func statusBadge(for state: String) -> some View {
        let (label, color, bg) = badgeConfig(for: state)
        Text(label)
            .font(.system(size: 10.5, weight: .bold))
            .foregroundStyle(color)
            .padding(.horizontal, 8)
            .padding(.vertical, 3)
            .background(bg, in: Capsule())
    }

    private func badgeConfig(for state: String) -> (String, Color, Color) {
        switch state {
        case "matched":
            return (L("Synced"), UH.Palette.accentInk, UH.Palette.activeFill)
        case "checkbox_only":
            return (L("Done"), Color(red: 0.05, green: 0.65, blue: 0.45), Color(red: 0.05, green: 0.65, blue: 0.45).opacity(0.12))
        case "missed":
            return (L("Missed"), UH.Palette.danger, UH.Palette.danger.opacity(0.12))
        default:
            return (L("Pending"), UH.Palette.secondary, UH.Palette.surface)
        }
    }

    private func load() async {
        phase = .loading
        switch await model.weekReview(week) {
        case .success(let review): phase = .loaded(review)
        case .failure(let error): phase = .failed(error.userMessage)
        }
    }
}
