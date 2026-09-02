import type { LegalContent } from "@/components/LegalShell";

/**
 * Support page content.
 *
 * Required by the COROS API application terms, which oblige partners to publish
 * a login portal and a support page so users can reach the integration and
 * request technical help.
 */

const CONTACT = "vvviet123@gmail.com";

export const supportEn: LegalContent = {
  title: "Support",
  updated: "Last updated: 2 September 2026",
  intro: [
    `Need help with Uphill AI? Email ${CONTACT} and we will get back to you within 5 business days. Telling us your account email, what you expected to happen, and what happened instead will usually get you a faster answer.`,
  ],
  sections: [
    {
      heading: "Your account",
      body: [
        "Sign in or create an account at uphill-ai.io.vn. You can sign in with email and password, or with Google or Facebook.",
        "To change your training profile — heart-rate zones, weekly volume, training days — open Profile settings inside the app.",
      ],
    },
    {
      heading: "Connecting a device account",
      body: [
        "Uphill AI can connect to your device account so your completed activities are matched against your plan automatically, and so your planned workouts can be sent to your watch.",
      ],
      bullets: [
        "To connect: open Profile settings, choose Connected accounts, pick your provider, and authorise the connection in the window that opens. You choose which categories of data to share.",
        "To disconnect: return to Connected accounts and select Disconnect. Data stops flowing immediately, and we delete the associated device data within 24 hours.",
        "You can also revoke access from your device provider's own account settings, which has the same effect.",
      ],
    },
    {
      heading: "Activities are not syncing",
      bullets: [
        "Confirm your watch has synced with its own app first — we receive activities only after they reach your provider's servers.",
        "Check that the connection still shows as active in Connected accounts; a provider may end a connection if a password changed.",
        "Allow a few minutes. Activities usually arrive within minutes of your watch syncing, but a provider backlog can delay them.",
        "If an activity still has not appeared after a few hours, email us the activity date, time and provider and we will investigate.",
      ],
    },
    {
      heading: "An activity matched the wrong session",
      body: [
        "Uphill AI matches completed activities to planned sessions automatically, and it will not always be right — a warm-up jog recorded separately from the main session is a common cause.",
        "You can correct any match yourself: open the session in your plan and choose Change matched activity. Manual matches always take precedence over automatic ones.",
      ],
    },
    {
      heading: "Sending workouts to your watch",
      bullets: [
        "Your planned structured workouts are published to your connected account's calendar; sync your watch with its own app to pull them onto the device.",
        "Only structured sessions with defined targets are sent. Notes-only sessions stay in Uphill AI.",
        "If a workout does not reach the watch, confirm the device supports structured workouts and that the account is still connected.",
      ],
    },
    {
      heading: "Privacy, data export and deletion",
      body: [
        `To request a copy of your data, correct it, or delete your account and everything associated with it, email ${CONTACT}. We respond within 30 days.`,
        "Our Privacy Notice at /privacy explains what we collect, how we use artificial intelligence, how long we keep data, and how to revoke access.",
      ],
    },
    {
      heading: "Reporting a security issue",
      body: [
        `If you believe you have found a security vulnerability, email ${CONTACT} with the details. Please do not disclose it publicly until we have had a chance to respond.`,
      ],
    },
  ],
  footer:
    "Uphill AI provides fitness and performance guidance only. It is not a medical device and does not provide medical advice. Consult a qualified medical professional before starting or changing a training programme.",
};

export const supportVi: LegalContent = {
  title: "Hỗ trợ",
  updated: "Cập nhật lần cuối: ngày 2 tháng 9 năm 2026",
  intro: [
    `Bạn cần hỗ trợ với Uphill AI? Hãy gửi email tới ${CONTACT}, chúng tôi sẽ phản hồi trong vòng 5 ngày làm việc. Nếu bạn cho biết email tài khoản, điều bạn mong đợi và điều thực tế đã xảy ra, chúng tôi thường có thể trả lời nhanh hơn.`,
  ],
  sections: [
    {
      heading: "Tài khoản của bạn",
      body: [
        "Đăng nhập hoặc tạo tài khoản tại uphill-ai.io.vn. Bạn có thể đăng nhập bằng email và mật khẩu, hoặc bằng Google hay Facebook.",
        "Để thay đổi hồ sơ tập luyện — vùng nhịp tim, khối lượng hàng tuần, ngày tập — hãy mở phần Cài đặt hồ sơ trong ứng dụng.",
      ],
    },
    {
      heading: "Liên kết tài khoản thiết bị",
      body: [
        "Uphill AI có thể liên kết với tài khoản thiết bị của bạn để tự động đối chiếu hoạt động đã hoàn thành với kế hoạch, và để gửi buổi tập đã lên kế hoạch sang đồng hồ của bạn.",
      ],
      bullets: [
        "Để liên kết: mở Cài đặt hồ sơ, chọn Tài khoản đã liên kết, chọn nhà cung cấp và cho phép kết nối trong cửa sổ hiện ra. Bạn chọn nhóm dữ liệu muốn chia sẻ.",
        "Để hủy liên kết: quay lại Tài khoản đã liên kết và chọn Hủy liên kết. Dữ liệu ngừng gửi ngay lập tức và chúng tôi xóa dữ liệu thiết bị liên quan trong vòng 24 giờ.",
        "Bạn cũng có thể thu hồi quyền truy cập trong phần cài đặt tài khoản của nhà cung cấp thiết bị, với hiệu lực tương đương.",
      ],
    },
    {
      heading: "Hoạt động không đồng bộ",
      bullets: [
        "Hãy chắc chắn đồng hồ đã đồng bộ với ứng dụng của hãng trước — chúng tôi chỉ nhận hoạt động sau khi dữ liệu tới máy chủ của nhà cung cấp.",
        "Kiểm tra liên kết còn hiển thị là đang hoạt động trong Tài khoản đã liên kết; nhà cung cấp có thể ngắt kết nối nếu mật khẩu thay đổi.",
        "Hãy đợi vài phút. Hoạt động thường xuất hiện trong vòng vài phút sau khi đồng hồ đồng bộ, nhưng có thể chậm hơn nếu nhà cung cấp đang quá tải.",
        "Nếu sau vài giờ hoạt động vẫn chưa xuất hiện, hãy gửi email cho chúng tôi kèm ngày, giờ và nhà cung cấp để chúng tôi kiểm tra.",
      ],
    },
    {
      heading: "Hoạt động bị ghép sai buổi tập",
      body: [
        "Uphill AI tự động ghép hoạt động đã hoàn thành với buổi tập đã lên kế hoạch, và đôi khi sẽ không chính xác — một buổi khởi động được ghi riêng với buổi tập chính là nguyên nhân thường gặp.",
        "Bạn có thể tự sửa: mở buổi tập trong kế hoạch và chọn Đổi hoạt động đã ghép. Lựa chọn thủ công luôn được ưu tiên hơn kết quả tự động.",
      ],
    },
    {
      heading: "Gửi buổi tập sang đồng hồ",
      bullets: [
        "Buổi tập có cấu trúc sẽ được gửi vào lịch của tài khoản đã liên kết; hãy đồng bộ đồng hồ với ứng dụng của hãng để tải về thiết bị.",
        "Chỉ những buổi tập có mục tiêu cụ thể mới được gửi. Các buổi chỉ có ghi chú sẽ ở lại trong Uphill AI.",
        "Nếu buổi tập không tới được đồng hồ, hãy kiểm tra thiết bị có hỗ trợ buổi tập có cấu trúc và tài khoản vẫn đang liên kết.",
      ],
    },
    {
      heading: "Quyền riêng tư, xuất và xóa dữ liệu",
      body: [
        `Để yêu cầu bản sao dữ liệu, chỉnh sửa, hoặc xóa tài khoản cùng toàn bộ dữ liệu liên quan, hãy gửi email tới ${CONTACT}. Chúng tôi phản hồi trong vòng 30 ngày.`,
        "Chính sách quyền riêng tư tại /privacy giải thích chúng tôi thu thập gì, sử dụng trí tuệ nhân tạo ra sao, lưu dữ liệu bao lâu và cách thu hồi quyền truy cập.",
      ],
    },
    {
      heading: "Báo cáo vấn đề bảo mật",
      body: [
        `Nếu bạn cho rằng đã phát hiện lỗ hổng bảo mật, hãy gửi email chi tiết tới ${CONTACT}. Vui lòng không công bố công khai trước khi chúng tôi kịp phản hồi.`,
      ],
    },
  ],
  footer:
    "Uphill AI chỉ cung cấp hướng dẫn về thể chất và hiệu suất. Đây không phải thiết bị y tế và không cung cấp lời khuyên y tế. Hãy tham khảo ý kiến bác sĩ trước khi bắt đầu hoặc thay đổi chương trình tập luyện.",
};
