import SwiftUI
import UniformTypeIdentifiers

struct PaceStrategySheet: View {
    @Environment(\.dismiss) private var dismiss
    let service: any PacingServicing
    var activePlan: Plan?
    var user: User?
    var initialTargetMins: Double?
    var onOpenNutrition: (() -> Void)?
    var onOpenGear: (() -> Void)?

    // Race course state
    @State private var raceName: String = ""
    @State private var distanceKm: Double = 50.0
    @State private var elevationGainM: Double = 2200.0
    @State private var splitIntervalKm: Double = 5.0

    // GPX Route State
    @State private var gpxResult: GpxCourseResult? = nil
    @State private var gpxData: Data? = nil
    @State private var showGpxImporter: Bool = false
    @State private var gpxErrorMessage: String? = nil

    // Pacing parameters
    @State private var targetTimeMins: Double = 330.0 // 5h 30m
    @State private var splitBias: Double = 0.0 // -0.05 to +0.05
    @State private var weightKg: Double = 68.0
    @State private var startClock: String = "05:00"

    // Splits and rest
    @State private var pacedCheckpoints: [PacedCheckpoint] = []
    @State private var restMins: [Int: Int] = [:]
    @State private var isLoading: Bool = false
    @State private var errorMessage: String? = nil
    var isPresentedInSheet: Bool = false

    private var isVietnamese: Bool {
        AppLanguage.current == .vi
    }

    init(
        service: any PacingServicing,
        activePlan: Plan? = nil,
        user: User? = nil,
        initialTargetMins: Double? = nil,
        initialGpxResult: GpxCourseResult? = nil,
        isPresentedInSheet: Bool = false,
        onOpenNutrition: (() -> Void)? = nil,
        onOpenGear: (() -> Void)? = nil
    ) {
        self.service = service
        self.activePlan = activePlan
        self.user = user
        self.initialTargetMins = initialTargetMins
        self.isPresentedInSheet = isPresentedInSheet
        self.onOpenNutrition = onOpenNutrition
        self.onOpenGear = onOpenGear
        _gpxResult = State(initialValue: initialGpxResult)
        if let gpx = initialGpxResult {
            _distanceKm = State(initialValue: gpx.totalDistanceKm)
            _elevationGainM = State(initialValue: gpx.totalElevationGainM)
        }
    }

    private var bounds: (min: Double, max: Double) {
        PacingCalculator.sliderBoundsMins(distanceKm: distanceKm, gainM: elevationGainM)
    }

    private var totalRestMinutes: Int {
        restMins.values.reduce(0, +)
    }

    private var movingTimeMinutes: Double {
        pacedCheckpoints.last?.cumulativeTimeMins ?? targetTimeMins
    }

    private var withRestTimeMinutes: Double {
        movingTimeMinutes + Double(totalRestMinutes)
    }

    private var hikeSectionsCount: Int {
        pacedCheckpoints.filter { $0.effort == "hike" }.count
    }

    private var totalEnergyKcal: Int {
        pacedCheckpoints.last?.energyKcal ?? 0
    }

    private var strategyLabel: String {
        if splitBias < -0.01 {
            return isVietnamese ? "Khởi đầu an toàn (Negative Split)" : "Conservative Start (Negative Split)"
        } else if splitBias > 0.01 {
            return isVietnamese ? "Khởi đầu nhanh (Positive Split)" : "Aggressive Start (Positive Split)"
        } else {
            return isVietnamese ? "Giữ đều sức (Tối ưu cơ năng)" : "Even Effort (Optimal Economy)"
        }
    }

    var body: some View {
        ScrollView {
                VStack(alignment: .leading, spacing: UH.Space.section) {
                    // Header Card
                    VStack(alignment: .leading, spacing: 4) {
                        Text("PACE STRATEGY")
                            .font(.system(size: 11, weight: .bold, design: .monospaced))
                            .tracking(0.8)
                            .foregroundStyle(UH.Palette.accentInk)
                        Text(raceName.isEmpty ? (isVietnamese ? "Chiến thuật Pace & Điểm chia Split" : "Race Pacing & Split Plan") : raceName)
                            .font(UH.TextStyle.sectionTitle)
                            .foregroundStyle(UH.Palette.ink)
                        Text(isVietnamese
                            ? "Tính toán theo đường cong tiêu hao năng lượng Minetti, bù độ cao, độ mệt mỏi tích lũy và chiến thuật phân bổ split."
                            : "Calibrated using the Minetti metabolic cost curve with altitude penalty, cumulative fatigue decay, and split strategy adjustment.")
                            .font(UH.TextStyle.caption)
                            .foregroundStyle(UH.Palette.secondary)
                    }

                    if let activePlan, activePlan.raceName != raceName, gpxResult == nil {
                        Button {
                            raceName = activePlan.raceName
                            if let d = activePlan.courseDistanceKm, d > 0 { distanceKm = d }
                            if let g = activePlan.courseElevationGainM, g > 0 { elevationGainM = g }
                            Task { await recalculatePacing() }
                        } label: {
                            HStack(spacing: 6) {
                                Image(systemName: "flag.checkered")
                                Text(isVietnamese ? "Dùng giải đua của plan: \(activePlan.raceName)" : "Use plan race: \(activePlan.raceName)")
                            }
                            .font(UH.TextStyle.caption.weight(.medium))
                            .foregroundStyle(UH.Palette.accentInk)
                            .padding(.vertical, 6)
                            .padding(.horizontal, 10)
                            .background(UH.Palette.activeFill, in: RoundedRectangle(cornerRadius: UH.Radius.control))
                        }
                    }

                    // Configuration Controls (Includes GPX Importer)
                    courseSetupCard

                    // Target Time & Strategy Controls
                    pacingControlsCard

                    // Headline Metrics Strip
                    if !pacedCheckpoints.isEmpty {
                        metricsSummaryStrip
                    }

                    // Course Profile Chart
                    PaceProfileChart(paced: pacedCheckpoints)

                    // Pacing Splits Table
                    if !pacedCheckpoints.isEmpty {
                        PacingSplitsTableView(
                            checkpoints: pacedCheckpoints,
                            restMins: $restMins,
                            startClock: startClock
                        )
                    }

                    // Handoff CTAs (Prod Parity)
                    HStack(spacing: 12) {
                        Button {
                            if isPresentedInSheet { dismiss() }
                            onOpenNutrition?()
                        } label: {
                            HStack(spacing: 6) {
                                Image(systemName: "fork.knife")
                                Text(isVietnamese ? "Kế hoạch Fueling" : "Plan Fueling")
                            }
                            .font(UH.TextStyle.label)
                            .foregroundStyle(Color.white)
                            .frame(maxWidth: .infinity)
                            .padding(.vertical, 12)
                            .background(UH.Palette.ink, in: RoundedRectangle(cornerRadius: UH.Radius.control))
                        }

                        Button {
                            if isPresentedInSheet { dismiss() }
                            onOpenGear?()
                        } label: {
                            HStack(spacing: 6) {
                                Image(systemName: "shoe.fill")
                                Text(isVietnamese ? "Chọn giày thi đấu" : "Select Shoes")
                            }
                            .font(UH.TextStyle.label)
                            .foregroundStyle(UH.Palette.ink)
                            .frame(maxWidth: .infinity)
                            .padding(.vertical, 12)
                            .background(UH.Palette.surface, in: RoundedRectangle(cornerRadius: UH.Radius.control))
                            .overlay(RoundedRectangle(cornerRadius: UH.Radius.control).stroke(UH.Palette.line))
                        }
                    }
                    .padding(.bottom, UH.Space.reading)
                }
                .padding(UH.Space.regular)
            }
            .background(UH.Palette.surface.ignoresSafeArea())
            .navigationTitle("Pace Strategy")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                if isPresentedInSheet {
                    ToolbarItem(placement: .topBarTrailing) {
                        Button {
                            dismiss()
                        } label: {
                            Image(systemName: "xmark.circle.fill")
                                .foregroundStyle(UH.Palette.muted)
                                .font(.system(size: 22))
                        }
                        .accessibilityIdentifier("paceStrategy.dismiss")
                    }
                }
            }
            .fileImporter(
                isPresented: $showGpxImporter,
                allowedContentTypes: [.xml, UTType(filenameExtension: "gpx") ?? .data, .data],
                allowsMultipleSelection: false
            ) { result in
                handleGpxSelection(result)
            }
            .task {
                if let p = activePlan {
                    raceName = p.raceName
                    if let d = p.courseDistanceKm, d > 0 { distanceKm = d }
                    if let g = p.courseElevationGainM, g > 0 { elevationGainM = g }
                }
                if let u = user, let w = u.weightKg, w > 30 {
                    weightKg = w
                }
                if let initial = initialTargetMins {
                    targetTimeMins = initial
                } else if let activePlan, let targetHours = activePlan.targetTimeHours, targetHours > 0 {
                    targetTimeMins = targetHours * 60.0
                } else {
                    targetTimeMins = max(bounds.min, min(bounds.max, (distanceKm + elevationGainM / 100.0) * 6.5))
                }
                await recalculatePacing()
            }
    }

    // MARK: - Setup Card

    private var courseSetupCard: some View {
        VStack(alignment: .leading, spacing: 10) {
            Text(isVietnamese ? "CẤU HÌNH CUNG ĐƯỜNG" : "COURSE CONFIGURATION")
                .font(.system(size: 11, weight: .bold, design: .monospaced))
                .foregroundStyle(UH.Palette.muted)

            // GPX File Importer Section
            gpxImportSection

            TextField(isVietnamese ? "Tên giải chạy" : "Race name", text: $raceName)
                .font(UH.TextStyle.body)
                .padding(10)
                .background(UH.Palette.surface, in: RoundedRectangle(cornerRadius: UH.Radius.control))
                .overlay(RoundedRectangle(cornerRadius: UH.Radius.control).stroke(UH.Palette.line))

            HStack(spacing: 12) {
                VStack(alignment: .leading, spacing: 4) {
                    Text(isVietnamese ? "Cự ly (km)" : "Distance (km)")
                        .font(UH.TextStyle.disclosure)
                        .foregroundStyle(UH.Palette.secondary)
                    TextField("50", value: $distanceKm, format: .number)
                        .keyboardType(.decimalPad)
                        .font(UH.TextStyle.metric)
                        .padding(10)
                        .background(UH.Palette.surface, in: RoundedRectangle(cornerRadius: UH.Radius.control))
                        .overlay(RoundedRectangle(cornerRadius: UH.Radius.control).stroke(UH.Palette.line))
                        .disabled(gpxResult != nil)
                }

                VStack(alignment: .leading, spacing: 4) {
                    Text(isVietnamese ? "Độ cao (m D+)" : "Gain (m D+)")
                        .font(UH.TextStyle.disclosure)
                        .foregroundStyle(UH.Palette.secondary)
                    TextField("2200", value: $elevationGainM, format: .number)
                        .keyboardType(.numberPad)
                        .font(UH.TextStyle.metric)
                        .padding(10)
                        .background(UH.Palette.surface, in: RoundedRectangle(cornerRadius: UH.Radius.control))
                        .overlay(RoundedRectangle(cornerRadius: UH.Radius.control).stroke(UH.Palette.line))
                        .disabled(gpxResult != nil)
                }
            }

            // Split Interval Picker
            VStack(alignment: .leading, spacing: 6) {
                Text(isVietnamese ? "Khoảng cách Split" : "Split Interval")
                    .font(UH.TextStyle.disclosure)
                    .foregroundStyle(UH.Palette.secondary)

                HStack(spacing: 8) {
                    ForEach([1.0, 5.0, 10.0], id: \.self) { interval in
                        Button {
                            splitIntervalKm = interval
                            UIImpactFeedbackGenerator(style: .light).impactOccurred()
                            if let data = gpxData, let res = gpxResult {
                                if let newRes = try? GpxCourseParser.parse(data: data, fileName: res.fileName, intervalKm: interval) {
                                    self.gpxResult = newRes
                                }
                            }
                            Task { await recalculatePacing() }
                        } label: {
                            Text("\(Int(interval)) km")
                                .font(UH.TextStyle.caption.weight(splitIntervalKm == interval ? .bold : .medium))
                                .foregroundStyle(splitIntervalKm == interval ? Color.white : UH.Palette.ink)
                                .frame(maxWidth: .infinity)
                                .padding(.vertical, 8)
                                .background(splitIntervalKm == interval ? UH.Palette.ink : UH.Palette.surface, in: RoundedRectangle(cornerRadius: UH.Radius.control))
                                .overlay(RoundedRectangle(cornerRadius: UH.Radius.control).stroke(UH.Palette.line))
                        }
                    }
                }
            }
        }
        .trainingCard()
    }

    // MARK: - GPX Import Section

    private var gpxImportSection: some View {
        VStack(alignment: .leading, spacing: 6) {
            if let gpx = gpxResult {
                // Loaded GPX Chip Card
                HStack(spacing: 10) {
                    Image(systemName: "map.fill")
                        .font(.system(size: 14))
                        .foregroundStyle(UH.Palette.accentInk)

                    VStack(alignment: .leading, spacing: 2) {
                        HStack(spacing: 6) {
                            Text(gpx.fileName)
                                .font(UH.TextStyle.label.weight(.semibold))
                                .foregroundStyle(UH.Palette.ink)
                                .lineLimit(1)
                            Text("GPX")
                                .font(.system(size: 9, weight: .bold, design: .monospaced))
                                .foregroundStyle(UH.Palette.accentInk)
                                .padding(.horizontal, 5)
                                .padding(.vertical, 1.5)
                                .background(UH.Palette.activeFill, in: Capsule())
                        }

                        Text(String(format: "%.1f km · +%d m D+ · %d CPs", gpx.totalDistanceKm, Int(gpx.totalElevationGainM), gpx.checkpoints.count))
                            .font(.system(size: 11, design: .monospaced))
                            .foregroundStyle(UH.Palette.secondary)
                    }

                    Spacer()

                    Button {
                        withAnimation(UH.Motion.standard) {
                            self.gpxResult = nil
                            self.gpxData = nil
                            self.gpxErrorMessage = nil
                        }
                        UIImpactFeedbackGenerator(style: .light).impactOccurred()
                        Task { await recalculatePacing() }
                    } label: {
                        Image(systemName: "xmark.circle.fill")
                            .font(.system(size: 18))
                            .foregroundStyle(UH.Palette.muted)
                    }
                    .buttonStyle(.plain)
                    .accessibilityLabel("Remove GPX file")
                }
                .padding(10)
                .background(UH.Palette.activeFill, in: RoundedRectangle(cornerRadius: UH.Radius.control))
                .overlay(RoundedRectangle(cornerRadius: UH.Radius.control).stroke(UH.Palette.accent.opacity(0.4), lineWidth: 1))
            } else {
                // Import GPX Button
                Button {
                    showGpxImporter = true
                } label: {
                    HStack(spacing: 8) {
                        Image(systemName: "arrow.triangle.turn.up.right.diamond.fill")
                            .font(.system(size: 14))
                            .foregroundStyle(UH.Palette.accentInk)
                        VStack(alignment: .leading, spacing: 2) {
                            Text(isVietnamese ? "Tải tệp GPX cung đường" : "Import GPX Course File")
                                .font(UH.TextStyle.label)
                                .foregroundStyle(UH.Palette.ink)
                            Text(isVietnamese
                                ? "Nạp biểu đồ độ cao thực tế và các điểm checkpoint từ tệp .gpx"
                                : "Load exact elevation profile & waypoints from .gpx")
                                .font(UH.TextStyle.caption)
                                .foregroundStyle(UH.Palette.secondary)
                        }
                        Spacer()
                        Image(systemName: "square.and.arrow.down")
                            .font(.system(size: 13, weight: .semibold))
                            .foregroundStyle(UH.Palette.secondary)
                    }
                    .padding(UH.Space.small)
                    .background(UH.Palette.surface, in: RoundedRectangle(cornerRadius: UH.Radius.control))
                    .overlay(RoundedRectangle(cornerRadius: UH.Radius.control).stroke(UH.Palette.line))
                }
                .buttonStyle(.plain)
                .accessibilityIdentifier("pace.importGpx")
            }

            if let err = gpxErrorMessage {
                HStack(spacing: 6) {
                    Image(systemName: "exclamationmark.circle.fill")
                        .foregroundStyle(UH.Palette.danger)
                        .font(.system(size: 11))
                    Text(err)
                        .font(UH.TextStyle.caption)
                        .foregroundStyle(UH.Palette.danger)
                }
                .padding(.top, 2)
            }
        }
    }

    // MARK: - Pacing Controls Card

    private var pacingControlsCard: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text(isVietnamese ? "MỤC TIÊU THỜI GIAN & CHIẾN THUẬT" : "TARGET TIME & STRATEGY")
                .font(.system(size: 11, weight: .bold, design: .monospaced))
                .foregroundStyle(UH.Palette.muted)

            // Target Finish Time Slider
            VStack(alignment: .leading, spacing: 6) {
                HStack {
                    Text(isVietnamese ? "Mục tiêu thời gian hoàn thành" : "Target Finish Time")
                        .font(UH.TextStyle.body.weight(.medium))
                        .foregroundStyle(UH.Palette.ink)
                    Spacer()
                    Text(GoalEstimate.formatMinutes(targetTimeMins))
                        .font(UH.TextStyle.metric)
                        .foregroundStyle(UH.Palette.accentInk)
                }

                Slider(
                    value: $targetTimeMins,
                    in: bounds.min...bounds.max,
                    step: 5.0
                ) {
                    Text("Target Time")
                }
                .tint(UH.Palette.accentInk)
                .onChange(of: targetTimeMins) { _, _ in
                    Task { await recalculatePacing() }
                }

                HStack {
                    Text(GoalEstimate.formatMinutes(bounds.min))
                    Spacer()
                    Text(GoalEstimate.formatMinutes(bounds.max))
                }
                .font(.system(size: 10, design: .monospaced))
                .foregroundStyle(UH.Palette.muted)
            }

            Divider().padding(.vertical, 2)

            // Split Bias Slider (-5% to +5%)
            VStack(alignment: .leading, spacing: 6) {
                HStack {
                    Text(isVietnamese ? "Chiến thuật phân bổ Split" : "Split Execution Strategy")
                        .font(UH.TextStyle.body.weight(.medium))
                        .foregroundStyle(UH.Palette.ink)
                    Spacer()
                    Text(strategyLabel)
                        .font(UH.TextStyle.disclosure.weight(.bold))
                        .foregroundStyle(UH.Palette.ink)
                }

                Slider(value: $splitBias, in: -0.05...0.05, step: 0.01)
                    .tint(UH.Palette.accentInk)
                    .onChange(of: splitBias) { _, _ in
                        Task { await recalculatePacing() }
                    }

                HStack {
                    Text(isVietnamese ? "Thận trọng" : "Conservative")
                    Spacer()
                    Text(isVietnamese ? "Đều" : "Even")
                    Spacer()
                    Text(isVietnamese ? "Tấn công" : "Aggressive")
                }
                .font(.system(size: 10, weight: .medium, design: .monospaced))
                .foregroundStyle(UH.Palette.muted)
            }

            Divider().padding(.vertical, 2)

            // Runner Weight & Race Start Time
            HStack(spacing: 12) {
                VStack(alignment: .leading, spacing: 4) {
                    Text(isVietnamese ? "Cân nặng runner (kg)" : "Runner Weight (kg)")
                        .font(UH.TextStyle.disclosure)
                        .foregroundStyle(UH.Palette.secondary)
                    TextField("68", value: $weightKg, format: .number)
                        .keyboardType(.decimalPad)
                        .font(UH.TextStyle.caption)
                        .padding(8)
                        .background(UH.Palette.surface, in: RoundedRectangle(cornerRadius: UH.Radius.control))
                        .overlay(RoundedRectangle(cornerRadius: UH.Radius.control).stroke(UH.Palette.line))
                }

                VStack(alignment: .leading, spacing: 4) {
                    Text(isVietnamese ? "Giờ xuất phát" : "Start Time (Clock)")
                        .font(UH.TextStyle.disclosure)
                        .foregroundStyle(UH.Palette.secondary)
                    TextField("05:00", text: $startClock)
                        .font(UH.TextStyle.caption)
                        .padding(8)
                        .background(UH.Palette.surface, in: RoundedRectangle(cornerRadius: UH.Radius.control))
                        .overlay(RoundedRectangle(cornerRadius: UH.Radius.control).stroke(UH.Palette.line))
                }
            }
        }
        .trainingCard()
    }

    // MARK: - Metrics Strip

    private var metricsSummaryStrip: some View {
        HStack(spacing: 8) {
            metricChip(icon: "clock", label: isVietnamese ? "Di chuyển" : "Moving", value: GoalEstimate.formatMinutes(movingTimeMinutes))
            metricChip(icon: "cup.and.saucer.fill", label: isVietnamese ? "Kèm nghỉ" : "With Rest", value: GoalEstimate.formatMinutes(withRestTimeMinutes))
            metricChip(icon: "figure.hiking", label: isVietnamese ? "Đoạn đi bộ" : "Hike Secs", value: "\(hikeSectionsCount)")
            if totalEnergyKcal > 0 {
                metricChip(icon: "flame.fill", label: isVietnamese ? "Tiêu hao" : "Energy", value: "~\(totalEnergyKcal) kcal")
            }
        }
    }

    private func metricChip(icon: String, label: String, value: String) -> some View {
        VStack(alignment: .leading, spacing: 2) {
            HStack(spacing: 3) {
                Image(systemName: icon)
                    .font(.system(size: 9))
                Text(label.uppercased())
                    .font(.system(size: 8, weight: .bold, design: .monospaced))
            }
            .foregroundStyle(UH.Palette.muted)

            Text(value)
                .font(.system(size: 13, weight: .bold, design: .monospaced))
                .foregroundStyle(UH.Palette.ink)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(8)
        .background(UH.Palette.surface, in: RoundedRectangle(cornerRadius: UH.Radius.control))
        .overlay(RoundedRectangle(cornerRadius: UH.Radius.control).stroke(UH.Palette.line))
    }

    // MARK: - Handle GPX Selection

    private func handleGpxSelection(_ result: Result<[URL], any Error>) {
        switch result {
        case .success(let urls):
            guard let url = urls.first else { return }
            let accessing = url.startAccessingSecurityScopedResource()
            defer {
                if accessing { url.stopAccessingSecurityScopedResource() }
            }

            do {
                let data = try Data(contentsOf: url)
                let parseResult = try GpxCourseParser.parse(
                    data: data,
                    fileName: url.lastPathComponent,
                    intervalKm: splitIntervalKm
                )

                self.gpxData = data
                self.gpxResult = parseResult
                self.gpxErrorMessage = nil
                self.distanceKm = parseResult.totalDistanceKm
                self.elevationGainM = parseResult.totalElevationGainM

                if raceName.isEmpty {
                    var cleaned = parseResult.fileName.replacingOccurrences(of: ".gpx", with: "", options: .caseInsensitive)
                    cleaned = cleaned.replacingOccurrences(of: "_", with: " ").replacingOccurrences(of: "-", with: " ")
                    self.raceName = cleaned
                }

                // Adjust target time slider bounds
                let b = PacingCalculator.sliderBoundsMins(distanceKm: parseResult.totalDistanceKm, gainM: parseResult.totalElevationGainM)
                targetTimeMins = max(b.min, min(b.max, (parseResult.totalDistanceKm + parseResult.totalElevationGainM / 100.0) * 6.5))

                UINotificationFeedbackGenerator().notificationOccurred(.success)
                Task { await recalculatePacing() }
            } catch {
                UINotificationFeedbackGenerator().notificationOccurred(.error)
                self.gpxErrorMessage = error.localizedDescription
            }

        case .failure(let err):
            self.gpxErrorMessage = err.localizedDescription
        }
    }

    // MARK: - Recalculate

    private func recalculatePacing() async {
        isLoading = true
        let checkpoints: [CourseCheckpoint]

        if let gpx = gpxResult {
            checkpoints = gpx.checkpoints
        } else {
            checkpoints = PacingCalculator.synthesizeCourse(
                distanceKm: distanceKm,
                gainM: elevationGainM,
                intervalKm: splitIntervalKm
            )
        }

        let req = PacingRequest(
            checkpoints: checkpoints,
            targetTimeMins: targetTimeMins,
            splitBias: splitBias,
            runnerWeightKg: weightKg,
            raceStartIso: nil
        )

        do {
            let res = try await service.calculatePacing(request: req)
            withAnimation(UH.Motion.standard) {
                self.pacedCheckpoints = res
            }
        } catch {
            errorMessage = error.localizedDescription
        }
        isLoading = false
    }
}
