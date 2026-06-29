/* eslint-disable @typescript-eslint/no-explicit-any */
import React, { useState, useEffect, useRef } from "react";
import { useAppContext } from "../contexts/AppContext";
import { translations } from "../app/translations";
import { WarningCircle, Trophy, Barbell, Clock, Lightning, Sneaker, Target, Calendar, House, Plant, Code, Plus, Trash, Brain, PersonSimpleRun, Mountains } from "@phosphor-icons/react";

export default function AboutTab({ isMobile, handleTabSwitch }: { isMobile: boolean, handleTabSwitch?: (tab: string) => void }) {
  const ctx = useAppContext();
  const { lang, user, activePlan, setAuthModalOpen, activeTab } = ctx as any;
  const t = (key: keyof typeof translations.en) => translations[lang as keyof typeof translations]?.[key] || translations.en[key] || key;

  const [startBtnHovered, setStartBtnHovered] = useState(false);

  const renderBody = () => {

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

          <div className="snow-glass" style={{

            gridColumn: isMobile ? 'auto' : 'span 2',

            padding: '32px',

            borderRadius: '32px'

          }}>

            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '20px' }}>

              <div style={{ width: '48px', height: '48px', borderRadius: '16px', background: 'rgba(255, 255, 255, 0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>

                <Brain size={28} color="var(--text-primary)" weight="duotone" />

              </div>

              <h4 style={{ color: 'var(--text-primary)', margin: 0, fontSize: '20px', fontWeight: 600 }}>

                {lang === "en" ? "The LLM + RAG Architecture" : "Kiến trúc LLM + RAG"}

              </h4>

            </div>

            <p style={{ fontSize: '15px', lineHeight: '1.7', color: 'var(--text-secondary)', marginBottom: '0' }}>

              {lang === "en"

                ? "Uphill.AI leverages state-of-the-art LLM + Retrieval-Augmented Generation (RAG). Instead of generating generic fitness advice, our AI engine specifically retrieves and synthesizes the gold-standard endurance science from "

                : "Uphill.AI ứng dụng công nghệ LLM + Retrieval-Augmented Generation (RAG). Thay vì đưa ra những lời khuyên tập luyện chung chung, hệ thống AI của chúng tôi tập trung tìm kiếm và tổng hợp các kiến thức khoa học sức bền cốt lõi từ cuốn sách "}

              <a href="https://www.amazon.com/Training-Uphill-Athlete-Mountain-Mountaineers/dp/B088MKG7DS/" target="_blank" rel="noopener noreferrer" style={{ color: "var(--accent-primary)", textDecoration: "underline", fontWeight: "600" }}>

                Training for the Uphill Athlete

              </a>

              {lang === "en"

                ? " to ensure your training plans are rooted in proven aerobic capacity building and terrain-specific muscular endurance."

                : ". Nhờ đó, các giáo án tập luyện của bạn luôn được xây dựng dựa trên những phương pháp cải thiện sức bền hiếu khí và sức bền cơ bắp đặc thù theo từng địa hình đã được kiểm chứng."}

            </p>

          </div>



          {/* Block B: Author Motivation */}

          <div className="snow-glass" style={{

            padding: '32px',

            borderRadius: '32px'

          }}>

             <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '20px' }}>

              <div style={{ width: '48px', height: '48px', borderRadius: '16px', background: 'rgba(255, 255, 255, 0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>

                <PersonSimpleRun size={28} color="var(--text-primary)" weight="duotone" />

              </div>

              <h4 style={{ color: 'var(--text-primary)', margin: 0, fontSize: '20px', fontWeight: 600 }}>

                {lang === "en" ? "Built for Runners" : "Dành cho những Runners"}

              </h4>

            </div>

            <p style={{ fontSize: '15px', lineHeight: '1.7', color: 'var(--text-secondary)' }}>

              {lang === "en"

                ? "Created by a trail runner with an IT, AI, and Data Engineering background. After experiencing immense personal growth racing the "

                : "Ứng dụng được xây dựng bởi một trail runner có background về IT, AI và Data Engineering. Sau khi tự mình trải nghiệm sự tiến bộ rõ rệt tại giải "

              }

              <strong style={{ color: "var(--text-primary)" }}>{lang === "en" ? "Ultra-Trail Australia by UTMB (in the Blue Mountains, NSW)" : "Ultra-Trail Australia của UTMB (Blue Mountains, bang New South Wales, Úc)"}</strong>

              {lang === "en"

                ? " using these exact principles, this app was built to democratize that specific training science for everyone."

                : " nhờ áp dụng chính xác các nguyên lý này, ứng dụng được ra đời với mong muốn chia sẻ và đưa những kiến thức khoa học tập luyện chuyên sâu này đến gần hơn với tất cả mọi người."

              }

            </p>

          </div>



          {/* Block C: Core Source & Philosophy (Span 3 cols) */}

          <div className="snow-glass" style={{

            gridColumn: isMobile ? 'auto' : 'span 3',

            padding: '32px',

            borderRadius: '32px'

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

                  <h5 style={{ color: "var(--text-primary)", fontSize: "16px", marginBottom: "8px" }}>{lang === "en" ? "Aerobic Volume" : "Tích lũy Hiếu khí"}</h5>

                  <p style={{ fontSize: "14px", color: "var(--text-secondary)", lineHeight: "1.6" }}>

                    {lang === "en" ? "Long-term athletic success in the mountains is built upon a foundation of structured, high-volume aerobic capacity training." : "Thành quả tập luyện lâu dài trên những cung đường dốc được xây dựng từ nền tảng tập luyện sức bền hiếu khí một cách bài bản và đều đặn."}

                  </p>

               </div>

               <div>

                  <h5 style={{ color: "var(--text-primary)", fontSize: "16px", marginBottom: "8px" }}>{lang === "en" ? "Muscular Endurance" : "Sức bền Cơ bắp"}</h5>

                  <p style={{ fontSize: "14px", color: "var(--text-secondary)", lineHeight: "1.6" }}>

                    {lang === "en" ? "Building resistance to localized muscular fatigue ensures you can sustain efforts over vertical terrain for hours." : "Việc rèn luyện khả năng chống chịu mỏi cơ cục bộ sẽ giúp bạn duy trì được sự dẻo dai và ổn định khi leo dốc liên tục suốt nhiều giờ liền."}

                  </p>

               </div>

               <div>

                  <h5 style={{ color: "var(--text-primary)", fontSize: "16px", marginBottom: "8px" }}>{lang === "en" ? "The Authors of \"Training for the Uphill Athlete\"" : "Về các Tác giả của quyển sách \"Training for the Uphill Athlete\""}</h5>

                  <p style={{ fontSize: "14px", color: "var(--text-secondary)", lineHeight: "1.6" }}>

                    {lang === "en" ? "We express our deepest gratitude to Steve House, Scott Johnston, and Kilian Jornet for their groundbreaking work in endurance science and trail running." : "Ứng dụng xin được bày tỏ lòng tri ân sâu sắc đến Steve House, Scott Johnston và Kilian Jornet vì những đóng góp mang tính nền tảng của họ cho khoa học sức bền và chạy trail."}

                  </p>

               </div>

            </div>

          </div>

        </div>

      </div>

    );

  };

  return renderBody();
}
