import re

# 1. Update translations.ts
with open("frontend/src/app/translations.ts", "r") as f:
    t_content = f.read()

t_content = t_content.replace('tab_philosophy: "Philosophy"', 'tab_about: "About Us"')
t_content = t_content.replace('home_feat_philosophy_title: "Coaching Philosophy"', 'home_feat_about_title: "About Us"')
t_content = t_content.replace('home_feat_philosophy_desc: "Learn about aerobic volume accumulation, cardiac drift tests, lactate thresholds, and why 80% of your training volume should remain easy."', 'home_feat_about_desc: "Learn about our AI engine, RAG architecture, and the origin story of Uphill.AI."')
t_content = t_content.replace('header_philosophy_desc: "Training philosophy and principles"', 'header_about_desc: "The story, engine, and philosophy behind Uphill.AI"')

t_content = t_content.replace('tab_philosophy: "Philosophy"', 'tab_about: "Về Chúng Tôi"') # In case there's another occurrence
t_content = t_content.replace('tab_philosophy: "Về Chúng Tôi"', 'tab_about: "Về Chúng Tôi"')
# Ensure Vietnamese translations are correct
t_content = t_content.replace('home_feat_philosophy_title: "Triết Lý Huấn Luyện"', 'home_feat_about_title: "Về Chúng Tôi"')
t_content = t_content.replace('home_feat_philosophy_desc: "Khám phá các phương pháp tích lũy thể tích hiếu khí (aerobic volume), bài kiểm tra độ trôi nhịp tim (cardiac drift tests), ngưỡng lactate và lý do vì sao 80% khối lượng tập luyện nên ở mức nhẹ nhàng."', 'home_feat_about_desc: "Khám phá kiến trúc AI, nền tảng RAG và câu chuyện khởi nguồn của Uphill.AI."')
t_content = t_content.replace('header_philosophy_desc: "Triết lý và các nguyên tắc huấn luyện cốt lõi"', 'header_about_desc: "Câu chuyện, nền tảng công nghệ, và triết lý của Uphill.AI"')

# Sometimes it might not match perfectly, let's just use regex for safety:
t_content = re.sub(r'tab_philosophy:\s*"(.*?)"', r'tab_about: "\1"', t_content)
t_content = t_content.replace('tab_about: "Philosophy"', 'tab_about: "About Us"')

with open("frontend/src/app/translations.ts", "w") as f:
    f.write(t_content)

# 2. Update page.tsx
with open("frontend/src/app/page.tsx", "r") as f:
    p_content = f.read()

# Replace "philosophy" string literals with "about"
p_content = p_content.replace('"philosophy"', '"about"')
p_content = p_content.replace("'philosophy'", "'about'")
p_content = p_content.replace('tab_philosophy', 'tab_about')
p_content = p_content.replace('header_philosophy_desc', 'header_about_desc')

# Add 'Code' import if missing
if 'Code' not in p_content.split('} from "@phosphor-icons/react"')[0]:
    p_content = p_content.replace('import { \n  Robot', 'import { \n  Code, Robot')

# Extract renderPhilosophy
start_idx = p_content.find("const renderPhilosophy = (isMobile: boolean) => {")
end_idx = p_content.find("const renderChat = (isMobile: boolean) => {", start_idx)

new_render_func = """const renderAboutUs = (isMobile: boolean) => {
    return (
      <div style={{ maxWidth: '1100px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '24px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px', marginBottom: '8px', padding: '0 16px' }}>
            <Mountains size={isMobile ? 28 : 36} color="var(--accent-primary)" weight="duotone" />
            <h3 className="card-title" style={{ margin: 0, fontSize: isMobile ? '24px' : '32px' }}>
              {lang === "en" ? "About Uphill.AI" : "Về Uphill.AI"}
            </h3>
        </div>
        
        {/* Bento Grid */}
        <div style={{ 
          display: 'grid', 
          gridTemplateColumns: isMobile ? '1fr' : 'repeat(3, 1fr)', 
          gap: '24px',
          padding: '0 16px' 
        }}>
          
          {/* Block A: The Engine (Span 2 cols on Desktop) */}
          <div className="card" style={{ 
            gridColumn: isMobile ? 'auto' : 'span 2',
            padding: '32px',
            background: 'rgba(255, 255, 255, 0.03)',
            backdropFilter: 'blur(32px)',
            WebkitBackdropFilter: 'blur(32px)',
            border: '1px solid rgba(255, 255, 255, 0.1)',
            borderRadius: '32px',
            boxShadow: 'inset 0 1px 0 rgba(255, 255, 255, 0.1)'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '20px' }}>
              <div style={{ width: '48px', height: '48px', borderRadius: '16px', background: 'rgba(255, 255, 255, 0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <Brain size={28} color="var(--text-primary)" weight="duotone" />
              </div>
              <h4 style={{ color: 'var(--text-primary)', margin: 0, fontSize: '20px', fontWeight: 600 }}>
                {lang === "en" ? "The AI + RAG Architecture" : "Kiến trúc AI + RAG"}
              </h4>
            </div>
            <p style={{ fontSize: '15px', lineHeight: '1.7', color: 'var(--text-secondary)', marginBottom: '0' }}>
              {lang === "en" 
                ? "Uphill.AI leverages state-of-the-art Retrieval-Augmented Generation (RAG). Instead of generating generic fitness advice, our AI engine specifically retrieves and synthesizes the gold-standard endurance science from " 
                : "Uphill.AI sử dụng kiến trúc Retrieval-Augmented Generation (RAG) tối tân. Thay vì đưa ra lời khuyên chung chung, AI của chúng tôi trích xuất và tổng hợp kiến thức khoa học sức bền chuẩn mực từ cuốn "}
              <a href="https://www.amazon.com/Training-Uphill-Athlete-Mountain-Mountaineers/dp/B088MKG7DS/" target="_blank" rel="noopener noreferrer" style={{ color: "var(--accent-primary)", textDecoration: "underline", fontWeight: "600" }}>
                Training for the Uphill Athlete
              </a>
              {lang === "en" 
                ? " to ensure your training plans are rooted in proven aerobic capacity building and terrain-specific muscular endurance."
                : " để đảm bảo giáo án của bạn bắt nguồn từ các phương pháp xây dựng nền tảng hiếu khí và sức bền cơ bắp đặc thù đã được chứng minh."}
            </p>
          </div>

          {/* Block B: Author Motivation */}
          <div className="card" style={{ 
            padding: '32px',
            background: 'rgba(255, 255, 255, 0.03)',
            backdropFilter: 'blur(32px)',
            WebkitBackdropFilter: 'blur(32px)',
            border: '1px solid rgba(255, 255, 255, 0.1)',
            borderRadius: '32px',
            boxShadow: 'inset 0 1px 0 rgba(255, 255, 255, 0.1)'
          }}>
             <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '20px' }}>
              <div style={{ width: '48px', height: '48px', borderRadius: '16px', background: 'rgba(255, 255, 255, 0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <PersonSimpleRun size={28} color="var(--text-primary)" weight="duotone" />
              </div>
              <h4 style={{ color: 'var(--text-primary)', margin: 0, fontSize: '20px', fontWeight: 600 }}>
                {lang === "en" ? "Built for Runners" : "Dành cho Runner"}
              </h4>
            </div>
            <p style={{ fontSize: '15px', lineHeight: '1.7', color: 'var(--text-secondary)' }}>
              {lang === "en"
                ? "Created by a trail runner with an IT, AI, and Data Engineering background. After experiencing immense personal growth racing the "
                : "Được phát triển bởi một trail runner có nền tảng về IT, AI, và Data Engineering. Sau khi đạt được sự phát triển vượt bậc và hoàn thành "
              }
              <strong style={{ color: "var(--text-primary)" }}>Ultra-Trail Australia by UTMB (50km in the Blue Mountains, NSW)</strong>
              {lang === "en"
                ? " using these exact principles, this app was built to democratize that specific training science for everyone."
                : " bằng những nguyên tắc này, ứng dụng được tạo ra để mang kiến thức chuẩn mực đó tới mọi runner."
              }
            </p>
          </div>

          {/* Block C: Core Source & Philosophy (Span 3 cols) */}
          <div className="card" style={{ 
            gridColumn: isMobile ? 'auto' : 'span 3',
            padding: '32px',
            background: 'rgba(255, 255, 255, 0.03)',
            backdropFilter: 'blur(32px)',
            WebkitBackdropFilter: 'blur(32px)',
            border: '1px solid rgba(255, 255, 255, 0.1)',
            borderRadius: '32px',
            boxShadow: 'inset 0 1px 0 rgba(255, 255, 255, 0.1)'
          }}>
             <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '20px' }}>
              <div style={{ width: '48px', height: '48px', borderRadius: '16px', background: 'rgba(255, 255, 255, 0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <Target size={28} color="var(--text-primary)" weight="duotone" />
              </div>
              <h4 style={{ color: 'var(--text-primary)', margin: 0, fontSize: '20px', fontWeight: 600 }}>
                {lang === "en" ? "The Core Philosophy" : "Triết Lý Huấn Luyện Cốt Lõi"}
              </h4>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : 'repeat(3, 1fr)', gap: '20px' }}>
               <div>
                  <h5 style={{ color: "var(--text-primary)", fontSize: "16px", marginBottom: "8px" }}>{lang === "en" ? "Aerobic Volume" : "Khối lượng Hiếu khí"}</h5>
                  <p style={{ fontSize: "14px", color: "var(--text-secondary)", lineHeight: "1.6" }}>
                    {lang === "en" ? "Long-term athletic success in the mountains is built upon a foundation of structured, high-volume aerobic capacity training." : "Thành công thể thao lâu dài được xây dựng trên nền tảng của việc tập luyện dung tích hiếu khí khối lượng lớn, có cấu trúc."}
                  </p>
               </div>
               <div>
                  <h5 style={{ color: "var(--text-primary)", fontSize: "16px", marginBottom: "8px" }}>{lang === "en" ? "Muscular Endurance" : "Sức bền Cơ bắp"}</h5>
                  <p style={{ fontSize: "14px", color: "var(--text-secondary)", lineHeight: "1.6" }}>
                    {lang === "en" ? "Building resistance to localized muscular fatigue ensures you can sustain efforts over vertical terrain for hours." : "Khả năng kháng mệt mỏi cơ bắp cục bộ giúp bạn duy trì nỗ lực trên địa hình dốc đứng trong nhiều giờ."}
                  </p>
               </div>
               <div>
                  <h5 style={{ color: "var(--text-primary)", fontSize: "16px", marginBottom: "8px" }}>{lang === "en" ? "The Authors" : "Sự tri ân"}</h5>
                  <p style={{ fontSize: "14px", color: "var(--text-secondary)", lineHeight: "1.6" }}>
                    {lang === "en" ? "Dedicated to Steve House, Scott Johnston, and Kilian Jornet for their groundbreaking work in Nordic endurance science." : "Dành sự tri ân tới Steve House, Scott Johnston và Kilian Jornet vì những công trình tiên phong của họ trong khoa học sức bền."}
                  </p>
               </div>
            </div>
          </div>
        </div>
      </div>
    );
  };
"""

p_content = p_content[:start_idx] + new_render_func + p_content[end_idx:]

# Let's fix the invocation in the activeTab switch
p_content = p_content.replace('renderPhilosophy(isMobile)', 'renderAboutUs(isMobile)')

with open("frontend/src/app/page.tsx", "w") as f:
    f.write(p_content)

