import type { LegalContent } from "@/components/LegalShell";

/**
 * Privacy notice content.
 *
 * Structured to satisfy the six disclosures required by COROS API Agreement
 * Section 9.1 -- (a) data categories, (b) how used, (c) retention, (d) AI /
 * model use, (e) how to revoke, (f) how to request deletion -- so this page
 * doubles as the compliance artifact for partner API reviews.
 */

const CONTACT = "vvviet123@gmail.com";

export const privacyEn: LegalContent = {
  title: "Privacy Notice",
  updated: "Last updated: 2 September 2026",
  intro: [
    "Uphill AI Vietnam (“Uphill AI”, “we”, “us”) provides an AI-assisted training platform for trail and mountain runners. This notice explains what personal data we collect, why we collect it, how long we keep it, how we use artificial intelligence, and how you can revoke access or have your data deleted.",
    `If you have any question about this notice or about your data, contact our privacy contact at ${CONTACT}.`,
  ],
  sections: [
    {
      heading: "1. What data we collect",
      body: ["We collect the following categories of personal data."],
      bullets: [
        "Account data — your email address, name, and the account identifier provided by Google or Facebook if you sign in with them. We never receive or store your password for those services.",
        "Profile and physiology — date of birth or age, gender, height, weight, maximum and resting heart rate, aerobic and anaerobic threshold heart rate, training pace zones, weekly training volume, and any injury history you choose to enter.",
        "Training plans and workouts — the plans we generate for you, your scheduled and completed sessions, session notes, and perceived-effort ratings.",
        "Connected device data — if you connect a device account such as COROS, we receive the data you authorise: completed activity records (time, distance, pace, heart rate, elevation, route), and daily health metrics such as sleep, heart-rate variability and resting heart rate. We receive this only after you explicitly authorise it, and only for your own account.",
        "Files you upload — activity files (.FIT) and route files (.GPX) you choose to upload.",
        "Usage data — pages viewed, actions taken in the app, session identifier, browser user agent, and timestamps, used to understand how the product is used and to diagnose faults.",
        "Optional credentials — if you supply your own AI provider API key, we store it to run your requests under your key rather than ours.",
      ],
    },
    {
      heading: "2. How we use your data",
      bullets: [
        "To create and adapt your training plan, and to keep your training zones accurate.",
        "To match your completed activities against your planned sessions and show you how you executed them.",
        "To assess recovery and readiness, and to suggest adjustments to upcoming sessions.",
        "To publish your planned workouts to a connected device account when you ask us to.",
        "To operate, secure, debug and improve the service.",
        "To communicate with you about your account and, if you enable them, training reminders.",
      ],
    },
    {
      heading: "3. Artificial intelligence and automated processing",
      body: [
        "Coaching guidance in Uphill AI is generated with a large language model. When you request a plan, ask the coach a question, or receive a recommendation, relevant parts of your profile, training history and connected-device data are sent to our AI provider (Google, via the Gemini API) to produce a response for you.",
        "We use your data to generate output for you and only for you. We do not use your personal data, or data from a connected device account, to train general-purpose or foundation AI models. We do not use it for advertising, data brokerage, or profiling across customers, and we never sell or licence it.",
        "Access to this data is limited to authorised personnel, and we review model outputs periodically for privacy risk.",
        "All guidance produced by Uphill AI is for fitness and performance purposes only. It is not medical advice, a clinical diagnosis, or a health assessment, and it must not be relied on as such. Consult a qualified medical professional before starting or changing a training programme.",
      ],
    },
    {
      heading: "4. Who we share data with",
      body: [
        "We do not sell your personal data. We share it only with service providers who process it on our behalf, under obligations at least as protective as this notice:",
      ],
      bullets: [
        "Google — the Gemini API, to generate coaching content; and Google Sign-In if you use it to authenticate.",
        "Meta — Facebook Login, only if you choose to sign in with Facebook.",
        "Our hosting and infrastructure providers, who store the data that runs the service.",
      ],
    },
    {
      heading: "5. Connected device accounts",
      body: [
        "Connecting a device account is entirely optional, and you choose which categories of data to authorise at the point of connection.",
        "We use connected-device data solely to provide coaching features back to you. We do not disclose one athlete's device data to another user of Uphill AI, except where you expressly enable coach sharing (see below).",
        "Where we display data that originated from a COROS device, we identify COROS as the source and the device model it came from.",
      ],
    },
    {
      heading: "6. Coach sharing",
      body: [
        "Uphill AI lets you optionally share your training with a coach on the platform. This sharing happens only when you expressly enable it, is limited to the coach you choose, and you can withdraw it at any time. Until you enable it, no other user can see your training or device data.",
      ],
    },
    {
      heading: "7. How long we keep your data",
      bullets: [
        "Account, profile and training data — for as long as your account is active.",
        "Connected-device data — for as long as the connection is active and the data is needed to provide your coaching features. If you disconnect a device account or delete your Uphill AI account, we delete or de-identify the associated device data within 24 hours, and in no case retain it longer than 90 days after you revoke access.",
        "Detailed second-by-second activity records — retained for up to 90 days. The summary metrics derived from them (time in zone, elevation, training load) are kept with your training history so your long-term progression remains intact.",
        "Usage data — retained in aggregate for product analytics.",
        "We may retain limited records for longer where the law requires it, or to resolve a dispute or investigate abuse.",
      ],
    },
    {
      heading: "8. How to revoke access",
      body: [
        "You can disconnect a linked device account at any time from your Uphill AI profile settings; this stops any further data being received immediately. You can also revoke Uphill AI's access from within your device provider's own account settings, which has the same effect.",
        "Revoking access triggers the deletion described in section 7.",
      ],
    },
    {
      heading: "9. Your rights and how to exercise them",
      body: [
        "Depending on where you live, you may have the right to access your data, correct it, delete it, restrict or object to how it is processed, withdraw consent, and receive a copy in a portable format.",
        `To exercise any of these rights, or to request deletion of your account and all associated data, email ${CONTACT}. We will respond within 30 days. We may need to verify your identity before acting on a request.`,
      ],
    },
    {
      heading: "10. Security",
      body: [
        "We maintain administrative, technical and organisational safeguards appropriate to the sensitivity of the data, including encrypted transport (HTTPS/TLS) for all traffic, encrypted storage of third-party access tokens, least-privilege access controls, authentication and credential management, logging and monitoring, vulnerability patching, and an incident response process.",
        "No system is perfectly secure. If a breach affects your personal data, we will notify you and the relevant authorities as required by law.",
      ],
    },
    {
      heading: "11. International transfers",
      body: [
        "We operate from Vietnam and use service providers who may process data in other countries, including the United States. Where required, we rely on appropriate safeguards such as standard contractual clauses for those transfers.",
      ],
    },
    {
      heading: "12. Children",
      body: [
        "Uphill AI is not directed at children under 16, and we do not knowingly collect their personal data. If you believe a child has given us data, contact us and we will delete it.",
      ],
    },
    {
      heading: "13. Changes to this notice",
      body: [
        "If we materially change how we use your data, we will update this page and, where the law requires it, ask for your consent again. The date at the top always reflects the current version.",
      ],
    },
    {
      heading: "14. Contact",
      body: [
        `Uphill AI Vietnam — privacy contact: ${CONTACT}. We aim to respond within 5 business days.`,
      ],
    },
  ],
  footer:
    "Uphill AI provides fitness and performance guidance only. It is not a medical device and does not provide medical advice.",
};

export const privacyVi: LegalContent = {
  title: "Chính sách quyền riêng tư",
  updated: "Cập nhật lần cuối: ngày 2 tháng 9 năm 2026",
  intro: [
    "Uphill AI Vietnam (“Uphill AI”, “chúng tôi”) cung cấp nền tảng huấn luyện có hỗ trợ trí tuệ nhân tạo dành cho vận động viên chạy địa hình (trail) và chạy núi. Chính sách này giải thích chúng tôi thu thập dữ liệu cá nhân nào, vì sao thu thập, lưu trong bao lâu, cách chúng tôi sử dụng trí tuệ nhân tạo, và cách bạn thu hồi quyền truy cập hoặc yêu cầu xóa dữ liệu.",
    `Nếu bạn có bất kỳ câu hỏi nào về chính sách này hoặc về dữ liệu của mình, vui lòng liên hệ ${CONTACT}.`,
  ],
  sections: [
    {
      heading: "1. Dữ liệu chúng tôi thu thập",
      body: ["Chúng tôi thu thập các nhóm dữ liệu cá nhân sau."],
      bullets: [
        "Dữ liệu tài khoản — địa chỉ email, tên, và mã định danh tài khoản từ Google hoặc Facebook nếu bạn đăng nhập bằng các dịch vụ đó. Chúng tôi không bao giờ nhận hay lưu mật khẩu của bạn ở các dịch vụ này.",
        "Hồ sơ và chỉ số sinh lý — ngày sinh hoặc tuổi, giới tính, chiều cao, cân nặng, nhịp tim tối đa và nhịp tim nghỉ, nhịp tim ngưỡng hiếu khí và yếm khí, vùng tốc độ tập luyện, khối lượng tập hàng tuần, và lịch sử chấn thương nếu bạn cung cấp.",
        "Kế hoạch và buổi tập — kế hoạch chúng tôi tạo cho bạn, các buổi tập đã lên lịch và đã hoàn thành, ghi chú và mức độ gắng sức cảm nhận.",
        "Dữ liệu từ thiết bị đã liên kết — nếu bạn liên kết tài khoản thiết bị như COROS, chúng tôi nhận dữ liệu mà bạn cho phép: bản ghi hoạt động đã hoàn thành (thời gian, quãng đường, tốc độ, nhịp tim, độ cao, lộ trình) và chỉ số sức khỏe hàng ngày như giấc ngủ, biến thiên nhịp tim và nhịp tim nghỉ. Chúng tôi chỉ nhận sau khi bạn cho phép rõ ràng, và chỉ cho riêng tài khoản của bạn.",
        "Tệp bạn tải lên — tệp hoạt động (.FIT) và tệp lộ trình (.GPX) bạn chọn tải lên.",
        "Dữ liệu sử dụng — trang đã xem, thao tác trong ứng dụng, mã phiên, trình duyệt và dấu thời gian, dùng để hiểu cách sản phẩm được sử dụng và khắc phục sự cố.",
        "Thông tin xác thực tùy chọn — nếu bạn cung cấp khóa API trí tuệ nhân tạo riêng, chúng tôi lưu để chạy yêu cầu bằng khóa của bạn thay vì của chúng tôi.",
      ],
    },
    {
      heading: "2. Cách chúng tôi sử dụng dữ liệu",
      bullets: [
        "Tạo và điều chỉnh kế hoạch tập luyện, và giữ các vùng tập của bạn chính xác.",
        "Đối chiếu hoạt động đã hoàn thành với buổi tập đã lên kế hoạch và cho bạn thấy mức độ thực hiện.",
        "Đánh giá khả năng hồi phục và sẵn sàng, đề xuất điều chỉnh cho các buổi tập sắp tới.",
        "Gửi buổi tập đã lên kế hoạch sang tài khoản thiết bị đã liên kết khi bạn yêu cầu.",
        "Vận hành, bảo mật, gỡ lỗi và cải thiện dịch vụ.",
        "Liên lạc với bạn về tài khoản và gửi nhắc nhở tập luyện nếu bạn bật tính năng này.",
      ],
    },
    {
      heading: "3. Trí tuệ nhân tạo và xử lý tự động",
      body: [
        "Hướng dẫn huấn luyện trong Uphill AI được tạo bằng mô hình ngôn ngữ lớn. Khi bạn yêu cầu một kế hoạch, đặt câu hỏi cho huấn luyện viên, hoặc nhận một đề xuất, các phần liên quan trong hồ sơ, lịch sử tập luyện và dữ liệu thiết bị của bạn được gửi tới nhà cung cấp trí tuệ nhân tạo (Google, qua Gemini API) để tạo câu trả lời cho bạn.",
        "Chúng tôi dùng dữ liệu của bạn để tạo kết quả cho riêng bạn. Chúng tôi không dùng dữ liệu cá nhân của bạn, hay dữ liệu từ tài khoản thiết bị đã liên kết, để huấn luyện các mô hình trí tuệ nhân tạo đa dụng hoặc mô hình nền tảng. Chúng tôi không dùng cho quảng cáo, môi giới dữ liệu, hay lập hồ sơ xuyên khách hàng, và không bao giờ bán hay cấp phép dữ liệu đó.",
        "Quyền truy cập dữ liệu này chỉ giới hạn cho nhân sự được ủy quyền, và chúng tôi định kỳ rà soát kết quả của mô hình để phát hiện rủi ro về quyền riêng tư.",
        "Mọi hướng dẫn do Uphill AI tạo ra chỉ nhằm mục đích thể chất và hiệu suất. Đây không phải lời khuyên y tế, chẩn đoán lâm sàng hay đánh giá sức khỏe, và không được sử dụng thay thế. Hãy tham khảo ý kiến bác sĩ trước khi bắt đầu hoặc thay đổi chương trình tập luyện.",
      ],
    },
    {
      heading: "4. Chia sẻ dữ liệu với ai",
      body: [
        "Chúng tôi không bán dữ liệu cá nhân của bạn. Chúng tôi chỉ chia sẻ với các nhà cung cấp dịch vụ xử lý thay mặt chúng tôi, theo các nghĩa vụ bảo vệ tương đương hoặc cao hơn chính sách này:",
      ],
      bullets: [
        "Google — Gemini API để tạo nội dung huấn luyện; và Google Sign-In nếu bạn dùng để đăng nhập.",
        "Meta — Facebook Login, chỉ khi bạn chọn đăng nhập bằng Facebook.",
        "Các nhà cung cấp hạ tầng và lưu trữ vận hành dịch vụ.",
      ],
    },
    {
      heading: "5. Tài khoản thiết bị đã liên kết",
      body: [
        "Việc liên kết tài khoản thiết bị là hoàn toàn tùy chọn, và bạn chọn nhóm dữ liệu nào được cho phép ngay tại thời điểm liên kết.",
        "Chúng tôi chỉ dùng dữ liệu thiết bị để cung cấp tính năng huấn luyện cho chính bạn. Chúng tôi không tiết lộ dữ liệu thiết bị của một vận động viên cho người dùng khác của Uphill AI, trừ khi bạn chủ động bật tính năng chia sẻ với huấn luyện viên (xem bên dưới).",
        "Khi hiển thị dữ liệu có nguồn gốc từ thiết bị COROS, chúng tôi ghi rõ COROS là nguồn dữ liệu và mẫu thiết bị tương ứng.",
      ],
    },
    {
      heading: "6. Chia sẻ với huấn luyện viên",
      body: [
        "Uphill AI cho phép bạn tùy chọn chia sẻ quá trình tập luyện với một huấn luyện viên trên nền tảng. Việc này chỉ diễn ra khi bạn chủ động bật, chỉ giới hạn ở huấn luyện viên bạn chọn, và bạn có thể thu hồi bất kỳ lúc nào. Trước khi bạn bật, không người dùng nào khác thấy được dữ liệu tập luyện hay thiết bị của bạn.",
      ],
    },
    {
      heading: "7. Thời gian lưu trữ dữ liệu",
      bullets: [
        "Dữ liệu tài khoản, hồ sơ và tập luyện — trong suốt thời gian tài khoản còn hoạt động.",
        "Dữ liệu thiết bị đã liên kết — trong thời gian liên kết còn hiệu lực và dữ liệu còn cần cho tính năng huấn luyện. Nếu bạn hủy liên kết hoặc xóa tài khoản Uphill AI, chúng tôi xóa hoặc ẩn danh dữ liệu thiết bị liên quan trong vòng 24 giờ, và trong mọi trường hợp không giữ quá 90 ngày sau khi bạn thu hồi quyền truy cập.",
        "Bản ghi hoạt động chi tiết theo từng giây — lưu tối đa 90 ngày. Các chỉ số tổng hợp rút ra từ đó (thời gian trong vùng, độ cao, tải tập luyện) được giữ cùng lịch sử tập luyện để tiến trình dài hạn của bạn không bị mất.",
        "Dữ liệu sử dụng — lưu dưới dạng tổng hợp phục vụ phân tích sản phẩm.",
        "Chúng tôi có thể lưu một số hồ sơ giới hạn lâu hơn khi pháp luật yêu cầu, hoặc để giải quyết tranh chấp và điều tra hành vi lạm dụng.",
      ],
    },
    {
      heading: "8. Cách thu hồi quyền truy cập",
      body: [
        "Bạn có thể hủy liên kết tài khoản thiết bị bất kỳ lúc nào trong phần cài đặt hồ sơ Uphill AI; việc này dừng ngay mọi dữ liệu gửi về sau đó. Bạn cũng có thể thu hồi quyền truy cập của Uphill AI ngay trong phần cài đặt tài khoản của nhà cung cấp thiết bị, với hiệu lực tương đương.",
        "Việc thu hồi sẽ kích hoạt quy trình xóa nêu tại mục 7.",
      ],
    },
    {
      heading: "9. Quyền của bạn và cách thực hiện",
      body: [
        "Tùy nơi bạn sinh sống, bạn có thể có quyền truy cập, chỉnh sửa, xóa dữ liệu, hạn chế hoặc phản đối việc xử lý, rút lại sự đồng ý, và nhận bản sao dữ liệu ở định dạng có thể chuyển giao.",
        `Để thực hiện các quyền này, hoặc yêu cầu xóa tài khoản và toàn bộ dữ liệu liên quan, vui lòng gửi email tới ${CONTACT}. Chúng tôi sẽ phản hồi trong vòng 30 ngày và có thể cần xác minh danh tính trước khi thực hiện.`,
      ],
    },
    {
      heading: "10. Bảo mật",
      body: [
        "Chúng tôi duy trì các biện pháp bảo vệ về quản lý, kỹ thuật và tổ chức tương xứng với mức độ nhạy cảm của dữ liệu, bao gồm mã hóa đường truyền (HTTPS/TLS), mã hóa khi lưu trữ mã truy cập của bên thứ ba, kiểm soát truy cập theo nguyên tắc tối thiểu, quản lý xác thực, ghi nhật ký và giám sát, vá lỗ hổng, và quy trình ứng phó sự cố.",
        "Không hệ thống nào an toàn tuyệt đối. Nếu xảy ra sự cố ảnh hưởng đến dữ liệu cá nhân của bạn, chúng tôi sẽ thông báo cho bạn và cơ quan có thẩm quyền theo quy định pháp luật.",
      ],
    },
    {
      heading: "11. Chuyển dữ liệu quốc tế",
      body: [
        "Chúng tôi hoạt động tại Việt Nam và sử dụng các nhà cung cấp dịch vụ có thể xử lý dữ liệu ở quốc gia khác, bao gồm Hoa Kỳ. Khi cần thiết, chúng tôi áp dụng các biện pháp bảo vệ phù hợp như điều khoản hợp đồng tiêu chuẩn cho các chuyển giao đó.",
      ],
    },
    {
      heading: "12. Trẻ em",
      body: [
        "Uphill AI không hướng đến trẻ em dưới 16 tuổi và chúng tôi không cố ý thu thập dữ liệu cá nhân của trẻ em. Nếu bạn cho rằng một trẻ em đã cung cấp dữ liệu cho chúng tôi, hãy liên hệ để chúng tôi xóa.",
      ],
    },
    {
      heading: "13. Thay đổi chính sách",
      body: [
        "Nếu chúng tôi thay đổi đáng kể cách sử dụng dữ liệu, chúng tôi sẽ cập nhật trang này và xin lại sự đồng ý của bạn khi pháp luật yêu cầu. Ngày ở đầu trang luôn phản ánh phiên bản hiện hành.",
      ],
    },
    {
      heading: "14. Liên hệ",
      body: [
        `Uphill AI Vietnam — đầu mối về quyền riêng tư: ${CONTACT}. Chúng tôi cố gắng phản hồi trong 5 ngày làm việc.`,
      ],
    },
  ],
  footer:
    "Uphill AI chỉ cung cấp hướng dẫn về thể chất và hiệu suất. Đây không phải thiết bị y tế và không cung cấp lời khuyên y tế.",
};
