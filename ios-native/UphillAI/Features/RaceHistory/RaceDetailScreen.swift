import SwiftUI

struct RaceDetailScreen: View {
    let result: RaceResult
    let service: any RaceHistoryServicing
    var athleteId: Int? = nil
    var onChanged: (() -> Void)? = nil
    @Environment(\.dismiss) private var dismiss
    @State private var model: RaceDetailViewModel
    @State private var courseId: Int?
    @State private var editing = false
    @State private var deleting = false
    @State private var isSaving = false
    @State private var writeError: String?

    init(result: RaceResult, service: any RaceHistoryServicing, athleteId: Int? = nil, onChanged: (() -> Void)? = nil) {
        self.result = result; self.service = service; self.athleteId = athleteId; self.onChanged = onChanged
        _model = State(initialValue: RaceDetailViewModel(service: service))
    }
    private var recorded: RaceResult { model.detail?.result ?? result }
    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: UH.Space.section) {
                VStack(alignment: .leading, spacing: UH.Space.small) {
                    Text(recorded.raceName).font(UH.TextStyle.sectionTitle).accessibilityAddTraits(.isHeader)
                    Text("\(recorded.raceDate) · \(RaceDisplay.discipline(recorded.discipline)) · \(RaceDisplay.source(recorded.source))").foregroundStyle(UH.Palette.secondary)
                    if !recorded.selected { Text("Awaiting confirmation").foregroundStyle(UH.Palette.accentInk) }
                    Text(recorded.formattedDuration).font(UH.TextStyle.metric.monospacedDigit())
                    Text("Recorded distance: \(recorded.formattedDistance)")
                    if let elevation = recorded.elevationGainM { Text("Recorded elevation gain: \(RaceDisplay.number(elevation)) m") }
                    if let location = recorded.location { Label(location, systemImage: "mappin.and.ellipse") }
                    if let bib = recorded.bib { Text("Bib: \(bib)") }
                    rank("Overall", rank: recorded.rankOverall, total: recorded.totalOverall, pct: model.detail?.performance.overallTopPct)
                    rank("Gender", rank: recorded.rankGender, total: recorded.totalGender, pct: model.detail?.performance.genderTopPct)
                    rank("Age group", rank: recorded.rankAgeGroup, total: recorded.totalAgeGroup, pct: model.detail?.performance.ageGroupTopPct)
                    if let key = model.detail?.performance.roadPbKey { Label("\(key.uppercased()) personal best", systemImage: "medal") }
                    if let pace = model.detail?.performance.averagePaceSecKm { Text("Average pace: \(RaceDisplay.pace(pace)) /km") }
                    if let link = recorded.resultUrl, let url = safeRaceResultURL(link) { Link("Open result source", destination: url) }
                }.trainingCard()
                if let note = recorded.userNote, !note.isEmpty {
                    VStack(alignment: .leading, spacing: UH.Space.small) {
                        Text("Your notes").font(UH.TextStyle.sectionTitle).accessibilityAddTraits(.isHeader)
                        Text(note)
                    }
                }
                if athleteId == nil {
                    HStack {
                        if recorded.source == "manual" {
                            Button("Edit result") { editing = true }
                            Spacer()
                            Button("Delete result", role: .destructive) { deleting = true }
                        } else if recorded.source == "vbm" {
                            Button(recorded.selected ? "Not my result" : "This is my result") {
                                Task { await mutate { _ = try await service.updateResult(id: recorded.id, changes: ["selected": .bool(!recorded.selected)]); courseId = nil } }
                            }
                        }
                    }.disabled(isSaving)
                }
                if let error = writeError { Text(error).foregroundStyle(UH.Palette.danger) }
                VStack(alignment: .leading, spacing: UH.Space.small) {
                    Text("Race Review").font(UH.TextStyle.sectionTitle).accessibilityAddTraits(.isHeader)
                    if model.isLoading { ProgressView("Loading review…") }
                    if let error = model.errorMessage {
                        Text(error).foregroundStyle(UH.Palette.danger)
                        Button("Retry") { Task { await reload() } }
                    }
                    if let detail = model.detail {
                        if let prior = detail.previousFinish {
                            Text("\(raceTimeDifference(prior.deltaSec)) than your finish on \(prior.raceDate).")
                            Text("Courses and conditions can vary between editions.").font(UH.TextStyle.caption).foregroundStyle(UH.Palette.secondary)
                        }
                        RaceCourseContextView(context: detail.courseContext, resultYear: String(recorded.raceDate.prefix(4)), onChoose: { courseId = $0 }, onRetry: { Task { await reload() } })
                        if !recorded.isDnf, let field = detail.historicalField {
                            historicalField(field)
                        }
                    }
                }
            }.font(UH.TextStyle.body).padding(UH.Space.regular)
        }.background(UH.Palette.surface.ignoresSafeArea())
            .navigationTitle("Race detail").navigationBarTitleDisplayMode(.inline)
            .task(id: courseId) { await reload() }
            .sheet(isPresented: $editing) {
                AddRaceSheet(service: service, editingResult: recorded) { _ in
                    courseId = nil; onChanged?(); Task { await reload() }
                }
            }
            .confirmationDialog("Delete this manual result?", isPresented: $deleting, titleVisibility: .visible) {
                Button("Delete result", role: .destructive) {
                    Task { await mutate(deleting: true) { try await service.deleteResult(id: recorded.id) } }
                }
            }
    }
    private func reload() async { await model.load(id: result.id, courseId: courseId, athleteId: athleteId) }
    private func mutate(deleting: Bool = false, action: () async throws -> Void) async {
        isSaving = true; writeError = nil
        do { try await action(); onChanged?(); if deleting { dismiss() } else { await reload() } }
        catch { writeError = error.raceHistoryMessage }
        isSaving = false
    }
    @ViewBuilder private func rank(_ label: String, rank: Int?, total: Int?, pct: Double?) -> some View {
        if let rank {
            Text("\(label) rank: #\(rank)\(total.map { $0 >= rank && rank > 0 ? " of \($0)" : "" } ?? "")")
            if !recorded.isDnf, let pct { Text("Top \(pct.formatted())% of the \(label.lowercased()) field").font(UH.TextStyle.caption).foregroundStyle(UH.Palette.secondary) }
        }
    }
    @ViewBuilder private func historicalField(_ field: [String: JSONValue]) -> some View {
        if let year = field["year"]?.intValue, let label = field["distance_label"]?.stringValue {
            Text("Historical field · \(String(year)) · \(label)").font(UH.TextStyle.label)
            if let total = field["finishers"]?.intValue { Text("\(total) finishers") }
            if let winner = field["winner_time"]?.stringValue { Text("Winner: \(winner)") }
            if let median = field["percentiles"]?["overall"]?["p50"]?.stringValue { Text("Median finish: \(median)") }
        }
    }
}
