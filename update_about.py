with open("frontend/src/app/page.tsx", "r") as f:
    content = f.read()

# Block A Title
content = content.replace(
    '              <h4 style={{ color: \'var(--text-primary)\', margin: 0, fontSize: \'20px\', fontWeight: 600 }}>\n                {lang === "en" ? "The AI + RAG Architecture" : "Kiến trúc AI + RAG"}\n              </h4>',
    '              <h4 style={{ color: \'var(--text-primary)\', margin: 0, fontSize: \'20px\', fontWeight: 600 }}>\n                {lang === "en" ? "The LLM + RAG Architecture" : "Kiến trúc LLM + RAG"}\n              </h4>'
)

# Block A Body 1
content = content.replace(
    '{lang === "en" \n                ? "Uphill.AI leverages state-of-the-art Retrieval-Augmented Generation (RAG). Instead of generating generic fitness advice, our AI engine specifically retrieves and synthesizes the gold-standard endurance science from " \n                : "Uphill.AI sử dụng kiến trúc Retrieval-Augmented Generation (RAG) tối tân. Thay vì đưa ra lời khuyên chung chung, AI của chúng tôi trích xuất và tổng hợp kiến thức khoa học sức bền chuẩn mực từ cuốn "}',
    '{lang === "en" \n                ? "Uphill.AI leverages state-of-the-art LLM + Retrieval-Augmented Generation (RAG). Instead of generating generic fitness advice, our AI engine specifically retrieves and synthesizes the gold-standard endurance science from " \n                : "Uphill.AI ứng dụng công nghệ LLM + Retrieval-Augmented Generation (RAG). Thay vì đưa ra những lời khuyên tập luyện chung chung, hệ thống AI của chúng tôi tập trung tìm kiếm và tổng hợp các kiến thức khoa học sức bền cốt lõi từ cuốn sách "}'
)

# Block A Body 2
content = content.replace(
    '{lang === "en" \n                ? " to ensure your training plans are rooted in proven aerobic capacity building and terrain-specific muscular endurance."\n                : " để đảm bảo giáo án của bạn bắt nguồn từ các phương pháp xây dựng nền tảng hiếu khí và sức bền cơ bắp đặc thù đã được chứng minh."}',
    '{lang === "en" \n                ? " to ensure your training plans are rooted in proven aerobic capacity building and terrain-specific muscular endurance."\n                : ". Nhờ đó, các giáo án tập luyện của bạn luôn được xây dựng dựa trên những phương pháp cải thiện sức bền hiếu khí và sức bền cơ bắp đặc thù theo từng địa hình đã được kiểm chứng."}'
)

# Block B Title
content = content.replace(
    '{lang === "en" ? "Built for Runners" : "Dành cho Runner"}',
    '{lang === "en" ? "Built for Runners" : "Dành cho những Runners"}'
)

# Block B Body 1
content = content.replace(
    '{lang === "en"\n                ? "Created by a trail runner with an IT, AI, and Data Engineering background. After experiencing immense personal growth racing the "\n                : "Được phát triển bởi một trail runner có nền tảng về IT, AI, và Data Engineering. Sau khi đạt được sự phát triển vượt bậc và hoàn thành "\n              }',
    '{lang === "en"\n                ? "Created by a trail runner with an IT, AI, and Data Engineering background. After experiencing immense personal growth racing the "\n                : "Ứng dụng được xây dựng bởi một trail runner có background về IT, AI và Data Engineering. Sau khi tự mình trải nghiệm sự tiến bộ rõ rệt tại giải "\n              }'
)

# Block B Bold text
content = content.replace(
    '<strong style={{ color: "var(--text-primary)" }}>Ultra-Trail Australia by UTMB (50km in the Blue Mountains, NSW)</strong>',
    '<strong style={{ color: "var(--text-primary)" }}>{lang === "en" ? "Ultra-Trail Australia by UTMB (in the Blue Mountains, NSW)" : "Ultra-Trail Australia của UTMB (Blue Mountains, bang New South Wales, Úc)"}</strong>'
)

# Block B Body 2
content = content.replace(
    '{lang === "en"\n                ? " using these exact principles, this app was built to democratize that specific training science for everyone."\n                : " bằng những nguyên tắc này, ứng dụng được tạo ra để mang kiến thức chuẩn mực đó tới mọi runner."\n              }',
    '{lang === "en"\n                ? " using these exact principles, this app was built to democratize that specific training science for everyone."\n                : " nhờ áp dụng chính xác các nguyên lý này, ứng dụng được ra đời với mong muốn chia sẻ và đưa những kiến thức khoa học tập luyện chuyên sâu này đến gần hơn với tất cả mọi người."\n              }'
)

# Block C Body 1
content = content.replace(
    '<h5 style={{ color: "var(--text-primary)", fontSize: "16px", marginBottom: "8px" }}>{lang === "en" ? "Aerobic Volume" : "Khối lượng Hiếu khí"}</h5>',
    '<h5 style={{ color: "var(--text-primary)", fontSize: "16px", marginBottom: "8px" }}>{lang === "en" ? "Aerobic Volume" : "Tích lũy Hiếu khí (Aerobic Volume)"}</h5>'
)

content = content.replace(
    '{lang === "en" ? "Long-term athletic success in the mountains is built upon a foundation of structured, high-volume aerobic capacity training." : "Thành công thể thao lâu dài được xây dựng trên nền tảng của việc tập luyện dung tích hiếu khí khối lượng lớn, có cấu trúc."}',
    '{lang === "en" ? "Long-term athletic success in the mountains is built upon a foundation of structured, high-volume aerobic capacity training." : "Thành quả tập luyện lâu dài trên những cung đường dốc được xây dựng từ nền tảng tập luyện sức bền hiếu khí một cách bài bản và đều đặn."}'
)

# Block C Body 2
content = content.replace(
    '<h5 style={{ color: "var(--text-primary)", fontSize: "16px", marginBottom: "8px" }}>{lang === "en" ? "Muscular Endurance" : "Sức bền Cơ bắp"}</h5>',
    '<h5 style={{ color: "var(--text-primary)", fontSize: "16px", marginBottom: "8px" }}>{lang === "en" ? "Muscular Endurance" : "Sức bền Cơ bắp (Muscular Endurance)"}</h5>'
)

content = content.replace(
    '{lang === "en" ? "Building resistance to localized muscular fatigue ensures you can sustain efforts over vertical terrain for hours." : "Khả năng kháng mệt mỏi cơ bắp cục bộ giúp bạn duy trì nỗ lực trên địa hình dốc đứng trong nhiều giờ."}',
    '{lang === "en" ? "Building resistance to localized muscular fatigue ensures you can sustain efforts over vertical terrain for hours." : "Việc rèn luyện khả năng chống chịu mỏi cơ cục bộ sẽ giúp bạn duy trì được sự dẻo dai và ổn định khi leo dốc liên tục suốt nhiều giờ liền."}'
)

# Block C Body 3
content = content.replace(
    '<h5 style={{ color: "var(--text-primary)", fontSize: "16px", marginBottom: "8px" }}>{lang === "en" ? "The Authors" : "Sự tri ân"}</h5>',
    '<h5 style={{ color: "var(--text-primary)", fontSize: "16px", marginBottom: "8px" }}>{lang === "en" ? "The Authors of \\"Training for the Uphill Athlete\\"" : "Về các Tác giả của quyển sách \\"Training for the Uphill Athlete\\" (The Authors)"}</h5>'
)

content = content.replace(
    '{lang === "en" ? "Dedicated to Steve House, Scott Johnston, and Kilian Jornet for their groundbreaking work in Nordic endurance science." : "Dành sự tri ân tới Steve House, Scott Johnston và Kilian Jornet vì những công trình tiên phong của họ trong khoa học sức bền."}',
    '{lang === "en" ? "We express our deepest gratitude to Steve House, Scott Johnston, and Kilian Jornet for their groundbreaking work in endurance science and trail running." : "Ứng dụng xin được bày tỏ lòng tri ân sâu sắc đến Steve House, Scott Johnston và Kilian Jornet vì những đóng góp mang tính nền tảng của họ cho khoa học sức bền và chạy trail."}'
)


with open("frontend/src/app/page.tsx", "w") as f:
    f.write(content)

