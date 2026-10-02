import SwiftUI

struct ScheduleNoticeBanner: View {
    let notice: ScheduleNotice
    let onDismiss: () -> Void
    var body: some View {
        Button(action: onDismiss) {
            Label(notice.text, systemImage: notice.style == .error ? "exclamationmark.circle" : "exclamationmark.triangle")
                .font(UH.TextStyle.caption).multilineTextAlignment(.leading)
                .foregroundStyle(notice.style == .error ? UH.Palette.danger : UH.Palette.warningInk)
                .padding(UH.Space.small).frame(maxWidth: .infinity, minHeight: 44, alignment: .leading)
                .background(notice.style == .error ? UH.Palette.danger.opacity(0.1) : UH.Palette.warningFill,
                            in: RoundedRectangle(cornerRadius: UH.Radius.panel))
        }.buttonStyle(.plain)
            .accessibilityHint("Tap to dismiss")
            .task(id: notice.id) {
                do { try await Task.sleep(for: .seconds(7)); onDismiss() } catch { }
            }
    }
}
