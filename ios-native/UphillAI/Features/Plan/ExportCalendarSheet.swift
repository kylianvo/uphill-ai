import SwiftUI
import EventKit

struct ExportCalendarSheet: View {
    let model: PlanViewModel
    @Environment(\.dismiss) private var dismiss
    @Environment(\.openURL) private var openURL

    @State private var timePref: String = "all_day"
    @State private var copied: Bool = false
    @State private var isSyncingAppleCalendar: Bool = false
    @State private var appleCalendarSyncResult: CalendarSyncResult? = nil
    @State private var syncError: String? = nil
    @State private var icsFileURL: URL? = nil

    private var isVietnamese: Bool {
        AppLanguage.current == .vi
    }

    private var plan: Plan? {
        model.snapshot?.plan
    }

    private var workouts: [Workout] {
        model.snapshot?.workouts ?? []
    }

    private var activeWorkoutsCount: Int {
        workouts.filter { !$0.isRest }.count
    }

    private var exportURLString: String {
        guard let plan else { return "" }
        let base = "https://app.uphill.ai"
        return "\(base)/api/coach/export-ics?plan_id=\(plan.id)&race_date=\(plan.raceDate)&time_pref=\(timePref)"
    }

    private var webcalURLString: String {
        exportURLString.replacingOccurrences(of: "https://", with: "webcal://")
    }

    init(model: PlanViewModel) {
        self.model = model
    }

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: UH.Space.regular) {
                    // Hero card
                    heroCard

                    // Time preference selector
                    timePreferenceCard

                    // Direct Apple Calendar Sync (EventKit)
                    appleCalendarSyncCard

                    // Native .ics Share / Export
                    shareIcsCard

                    // Remote URL Subscription & Webcal
                    urlSubscriptionCard

                    // Instructions
                    instructionsCard
                }
                .padding(UH.Space.regular)
            }
            .background(UH.Palette.surface)
            .navigationTitle(isVietnamese ? "Xuất lịch tập" : "Export Calendar")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button(isVietnamese ? "Đóng" : "Done") { dismiss() }
                }
            }
        }
        .presentationDetents([.medium, .large])
        .presentationBackground(UH.Palette.surface)
        .accessibilityIdentifier("export.calendar.sheet")
        .task {
            prepareIcsFile()
        }
        .onChange(of: timePref) { _, _ in
            prepareIcsFile()
        }
    }

    // MARK: - Hero Card

    private var heroCard: some View {
        VStack(alignment: .leading, spacing: UH.Space.small) {
            HStack(spacing: UH.Space.compact) {
                Image(systemName: "calendar.badge.clock")
                    .font(.title2)
                    .foregroundStyle(UH.Palette.accentInk)
                VStack(alignment: .leading, spacing: 2) {
                    Text(plan?.raceName ?? (isVietnamese ? "Lịch tập" : "Training Plan"))
                        .font(UH.TextStyle.sectionTitle)
                        .foregroundStyle(UH.Palette.ink)
                    Text(isVietnamese
                        ? "\(model.weeks.count) tuần · \(activeWorkoutsCount) buổi tập"
                        : "\(model.weeks.count) weeks · \(activeWorkoutsCount) sessions")
                        .font(UH.TextStyle.caption)
                        .foregroundStyle(UH.Palette.secondary)
                }
            }

            Text(isVietnamese
                ? "Thêm các buổi tập trực tiếp vào Apple Calendar, Google Calendar, hoặc Outlook. Link đăng ký tự động cập nhật khi lịch tập thay đổi."
                : "Add workouts directly to Apple Calendar, Google Calendar, or Outlook. Subscriptions stay updated as your plan adapts.")
                .font(UH.TextStyle.body)
                .foregroundStyle(UH.Palette.secondary)
        }
        .padding(UH.Space.regular)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(UH.Palette.card, in: RoundedRectangle(cornerRadius: UH.Radius.landing))
        .overlay(RoundedRectangle(cornerRadius: UH.Radius.landing).stroke(UH.Palette.line))
    }

    // MARK: - Time Preference Card

    private var timePreferenceCard: some View {
        VStack(alignment: .leading, spacing: UH.Space.compact) {
            Text(isVietnamese ? "GIỜ TẬP ƯU TIÊN" : "PREFERRED WORKOUT TIME")
                .font(.system(size: 10.5, weight: .bold, design: .monospaced))
                .tracking(0.5)
                .foregroundStyle(UH.Palette.muted)

            VStack(spacing: 6) {
                timeOption(
                    id: "all_day",
                    title: isVietnamese ? "Cả ngày" : "All Day Event",
                    subtitle: isVietnamese ? "Phù hợp khi lịch chạy linh hoạt trong ngày" : "Best for flexible daily scheduling",
                    icon: "sun.max"
                )
                timeOption(
                    id: "morning",
                    title: isVietnamese ? "Buổi sáng (06:00)" : "Morning (06:00)",
                    subtitle: isVietnamese ? "Khung giờ chạy sáng sớm" : "Early workout time slot",
                    icon: "sunrise.fill"
                )
                timeOption(
                    id: "afternoon",
                    title: isVietnamese ? "Buổi chiều (14:00)" : "Afternoon (14:00)",
                    subtitle: isVietnamese ? "Khung giờ tập buổi chiều" : "Mid-day workout block",
                    icon: "sun.haze.fill"
                )
                timeOption(
                    id: "evening",
                    title: isVietnamese ? "Buổi tối (18:00)" : "Evening (18:00)",
                    subtitle: isVietnamese ? "Khung giờ chạy sau giờ làm" : "Post-work session",
                    icon: "sunset.fill"
                )
            }
        }
        .padding(UH.Space.regular)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(UH.Palette.card, in: RoundedRectangle(cornerRadius: UH.Radius.landing))
        .overlay(RoundedRectangle(cornerRadius: UH.Radius.landing).stroke(UH.Palette.line))
    }

    private func timeOption(id: String, title: String, subtitle: String, icon: String) -> some View {
        let isSelected = timePref == id
        return Button {
            timePref = id
            UIImpactFeedbackGenerator(style: .light).impactOccurred()
        } label: {
            HStack(spacing: UH.Space.small) {
                Image(systemName: icon)
                    .font(.body)
                    .foregroundStyle(isSelected ? UH.Palette.accentInk : UH.Palette.secondary)
                    .frame(width: 24)

                VStack(alignment: .leading, spacing: 2) {
                    Text(title)
                        .font(UH.TextStyle.label)
                        .foregroundStyle(UH.Palette.ink)
                    Text(subtitle)
                        .font(UH.TextStyle.caption)
                        .foregroundStyle(UH.Palette.secondary)
                }

                Spacer()

                if isSelected {
                    Image(systemName: "checkmark.circle.fill")
                        .foregroundStyle(UH.Palette.accentInk)
                }
            }
            .padding(.horizontal, UH.Space.small)
            .padding(.vertical, 8)
            .background(isSelected ? UH.Palette.activeFill : UH.Palette.surface, in: RoundedRectangle(cornerRadius: UH.Radius.control))
            .overlay(RoundedRectangle(cornerRadius: UH.Radius.control).stroke(isSelected ? UH.Palette.accent : UH.Palette.line, lineWidth: 1))
        }
        .buttonStyle(.plain)
    }

    // MARK: - Native Apple Calendar EventKit Card

    private var appleCalendarSyncCard: some View {
        VStack(alignment: .leading, spacing: UH.Space.compact) {
            HStack(spacing: 6) {
                Image(systemName: "apple.logo")
                    .font(.system(size: 13, weight: .bold))
                Text(isVietnamese ? "ĐỒNG BỘ TRỰC TIẾP APPLE CALENDAR" : "DIRECT APPLE CALENDAR SYNC")
                    .font(.system(size: 10.5, weight: .bold, design: .monospaced))
                    .tracking(0.5)
            }
            .foregroundStyle(UH.Palette.muted)

            Text(isVietnamese
                ? "Tự động tạo lịch riêng \"Uphill AI Training\" trên ứng dụng Calendar của máy mà không cần thao tác tải tệp."
                : "Automatically create a dedicated \"Uphill AI Training\" calendar in your native Calendar app without manual file imports.")
                .font(UH.TextStyle.caption)
                .foregroundStyle(UH.Palette.secondary)

            Button {
                Task {
                    await syncToEventKit()
                }
            } label: {
                HStack(spacing: 8) {
                    if isSyncingAppleCalendar {
                        ProgressView()
                            .tint(.white)
                        Text(isVietnamese ? "Đang đồng bộ..." : "Syncing to Calendar...")
                    } else {
                        Image(systemName: "calendar.badge.plus")
                        Text(isVietnamese ? "Thêm vào Apple Calendar" : "Add to Apple Calendar")
                    }
                }
                .font(UH.TextStyle.label)
                .frame(maxWidth: .infinity)
                .frame(height: 44)
            }
            .buttonStyle(.uhPrimary)
            .disabled(isSyncingAppleCalendar || plan == nil)
            .accessibilityIdentifier("export.sync.appleCalendar")

            if let result = appleCalendarSyncResult {
                HStack(spacing: 8) {
                    Image(systemName: "checkmark.circle.fill")
                        .foregroundStyle(UH.Palette.accentInk)
                    Text(isVietnamese
                        ? "Đã thêm \(result.addedCount) buổi tập vào lịch \(result.calendarTitle)"
                        : "Added \(result.addedCount) sessions to \(result.calendarTitle)")
                        .font(UH.TextStyle.caption.weight(.medium))
                        .foregroundStyle(UH.Palette.ink)
                }
                .padding(8)
                .frame(maxWidth: .infinity, alignment: .leading)
                .background(UH.Palette.activeFill, in: RoundedRectangle(cornerRadius: UH.Radius.control))
            }

            if let err = syncError {
                HStack(spacing: 8) {
                    Image(systemName: "exclamationmark.triangle.fill")
                        .foregroundStyle(Color.red)
                    Text(err)
                        .font(UH.TextStyle.caption)
                        .foregroundStyle(Color.red)
                }
                .padding(8)
                .frame(maxWidth: .infinity, alignment: .leading)
                .background(Color.red.opacity(0.1), in: RoundedRectangle(cornerRadius: UH.Radius.control))
            }
        }
        .padding(UH.Space.regular)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(UH.Palette.card, in: RoundedRectangle(cornerRadius: UH.Radius.landing))
        .overlay(RoundedRectangle(cornerRadius: UH.Radius.landing).stroke(UH.Palette.line))
    }

    // MARK: - Native .ics Share Card

    private var shareIcsCard: some View {
        VStack(alignment: .leading, spacing: UH.Space.compact) {
            Text(isVietnamese ? "XUẤT TỆP ĐỊNH DẠNG .ICS" : "EXPORT .ICS FILE")
                .font(.system(size: 10.5, weight: .bold, design: .monospaced))
                .tracking(0.5)
                .foregroundStyle(UH.Palette.muted)

            Text(isVietnamese
                ? "Xuất tệp iCalendar chuẩn để chia sẻ qua AirDrop, mở trên ứng dụng lịch khác, hoặc lưu vào Tệp."
                : "Export a standard iCalendar file to share via AirDrop, open in third-party calendar apps, or save to Files.")
                .font(UH.TextStyle.caption)
                .foregroundStyle(UH.Palette.secondary)

            if let fileURL = icsFileURL {
                ShareLink(item: fileURL) {
                    HStack(spacing: 8) {
                        Image(systemName: "square.and.arrow.up")
                        Text(isVietnamese ? "Chia sẻ / Lưu tệp .ics" : "Share / Export .ics File")
                    }
                    .font(UH.TextStyle.label)
                    .frame(maxWidth: .infinity)
                    .frame(height: 44)
                    .background(UH.Palette.surface, in: RoundedRectangle(cornerRadius: UH.Radius.control))
                    .overlay(RoundedRectangle(cornerRadius: UH.Radius.control).stroke(UH.Palette.line))
                }
                .buttonStyle(.plain)
                .accessibilityIdentifier("export.share.ics")
            } else {
                Button {
                    prepareIcsFile()
                } label: {
                    HStack(spacing: 8) {
                        Image(systemName: "arrow.triangle.2.circlepath")
                        Text(isVietnamese ? "Đang chuẩn bị tệp..." : "Preparing .ics File...")
                    }
                    .font(UH.TextStyle.caption)
                    .frame(maxWidth: .infinity)
                    .frame(height: 44)
                    .background(UH.Palette.surface, in: RoundedRectangle(cornerRadius: UH.Radius.control))
                    .overlay(RoundedRectangle(cornerRadius: UH.Radius.control).stroke(UH.Palette.line))
                }
                .disabled(true)
            }
        }
        .padding(UH.Space.regular)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(UH.Palette.card, in: RoundedRectangle(cornerRadius: UH.Radius.landing))
        .overlay(RoundedRectangle(cornerRadius: UH.Radius.landing).stroke(UH.Palette.line))
    }

    // MARK: - URL Subscription Card

    private var urlSubscriptionCard: some View {
        VStack(alignment: .leading, spacing: UH.Space.compact) {
            Text(isVietnamese ? "ĐĂNG KÝ QUA LINK TỰ ĐỘNG CẬP NHẬT" : "AUTO-UPDATING CALENDAR SUBSCRIPTION")
                .font(.system(size: 10.5, weight: .bold, design: .monospaced))
                .tracking(0.5)
                .foregroundStyle(UH.Palette.muted)

            VStack(spacing: UH.Space.compact) {
                Button {
                    if let url = URL(string: webcalURLString) {
                        openURL(url)
                    }
                } label: {
                    HStack(spacing: 8) {
                        Image(systemName: "link.badge.plus")
                        Text(isVietnamese ? "Đăng ký trên Apple Calendar (webcal)" : "Subscribe in Apple Calendar (webcal)")
                    }
                    .font(UH.TextStyle.label)
                    .frame(maxWidth: .infinity)
                    .frame(height: 44)
                    .background(UH.Palette.surface, in: RoundedRectangle(cornerRadius: UH.Radius.control))
                    .overlay(RoundedRectangle(cornerRadius: UH.Radius.control).stroke(UH.Palette.line))
                }
                .buttonStyle(.plain)
                .accessibilityIdentifier("export.subscribe.apple")

                Button {
                    UIPasteboard.general.string = exportURLString
                    copied = true
                    UIImpactFeedbackGenerator(style: .medium).impactOccurred()
                    Task {
                        try? await Task.sleep(for: .seconds(2.5))
                        copied = false
                    }
                } label: {
                    HStack(spacing: 6) {
                        Image(systemName: copied ? "checkmark" : "doc.on.doc")
                            .foregroundStyle(copied ? UH.Palette.accentInk : UH.Palette.ink)
                        Text(copied
                            ? (isVietnamese ? "Đã sao chép link!" : "Link Copied!")
                            : (isVietnamese ? "Sao chép link đăng ký lịch" : "Copy Calendar Subscription URL"))
                            .foregroundStyle(copied ? UH.Palette.accentInk : UH.Palette.ink)
                    }
                    .font(UH.TextStyle.label)
                    .frame(maxWidth: .infinity)
                    .frame(height: 44)
                    .background(UH.Palette.surface, in: RoundedRectangle(cornerRadius: UH.Radius.control))
                    .overlay(RoundedRectangle(cornerRadius: UH.Radius.control).stroke(UH.Palette.line, lineWidth: 1))
                }
                .buttonStyle(.plain)
                .sensoryFeedback(.success, trigger: copied)
                .accessibilityIdentifier("export.copy.url")
            }
        }
        .padding(UH.Space.regular)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(UH.Palette.card, in: RoundedRectangle(cornerRadius: UH.Radius.landing))
        .overlay(RoundedRectangle(cornerRadius: UH.Radius.landing).stroke(UH.Palette.line))
    }

    // MARK: - Instructions

    private var instructionsCard: some View {
        VStack(alignment: .leading, spacing: 6) {
            Text("GOOGLE CALENDAR & OUTLOOK")
                .font(.system(size: 10, weight: .bold, design: .monospaced))
                .tracking(0.5)
                .foregroundStyle(UH.Palette.muted)

            Text(isVietnamese
                ? "Để đăng ký trên Google Calendar hoặc Outlook web, sao chép link đăng ký ở trên và chọn \"Thêm lịch từ URL\" (Add Calendar from URL)."
                : "To subscribe in Google Calendar or Outlook on the web, copy the subscription link above and select \"Add Calendar from URL\".")
                .font(UH.TextStyle.caption)
                .foregroundStyle(UH.Palette.secondary)
        }
        .padding(UH.Space.small)
        .frame(maxWidth: .infinity, alignment: .leading)
    }

    // MARK: - Actions

    private func prepareIcsFile() {
        guard let plan else { return }
        do {
            let url = try CalendarExportManager.shared.exportToTemporaryIcsFile(
                plan: plan,
                workouts: workouts,
                timePref: timePref
            )
            self.icsFileURL = url
        } catch {
            self.syncError = error.localizedDescription
        }
    }

    private func syncToEventKit() async {
        guard let plan else { return }
        isSyncingAppleCalendar = true
        syncError = nil
        appleCalendarSyncResult = nil

        do {
            let result = try await CalendarExportManager.shared.syncToAppleCalendar(
                plan: plan,
                workouts: workouts,
                timePref: timePref
            )
            UINotificationFeedbackGenerator().notificationOccurred(.success)
            withAnimation(UH.Motion.standard) {
                self.appleCalendarSyncResult = result
            }
        } catch {
            UINotificationFeedbackGenerator().notificationOccurred(.error)
            withAnimation(UH.Motion.standard) {
                self.syncError = error.localizedDescription
            }
        }

        isSyncingAppleCalendar = false
    }
}
