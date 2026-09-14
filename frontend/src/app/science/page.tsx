"use client";
import React from "react";
import Link from "next/link";
import {
  MapPin,
  CalendarBlank,
  ArrowsClockwise,
  Trophy,
  ShieldCheck,
  CheckCircle,
  Gauge,
  Crosshair,
  Sneaker,
  BowlFood,
  Robot,
  ArrowLeft,
  BookOpen,
  Flask,
  Compass,
  Barbell,
} from "@phosphor-icons/react";
import { useAppContext } from "@/contexts/AppContext";
import { translations } from "../translations";
import { ProfileExplainer } from "@/components/landing/ProfileExplainer";
import { FeatureGrid } from "@/components/landing/FeatureGrid";
import { useIsMobileViewport } from "@/hooks/useIsMobileViewport";

export default function SciencePage() {
  const { lang, setLang } = useAppContext() as {
    lang: "en" | "vi";
    setLang: (l: "en" | "vi") => void;
  };
  const t = (key: keyof typeof translations.en) =>
    translations[lang]?.[key] || translations.en[key] || key;
  const isMobile = useIsMobileViewport();

  const sectionStyle: React.CSSProperties = {
    scrollMarginTop: "90px",
    background: "rgba(255, 255, 255, 0.95)",
    backdropFilter: "blur(20px)",
    WebkitBackdropFilter: "blur(20px)",
    border: "1px solid rgba(0, 0, 0, 0.08)",
    borderRadius: "24px",
    padding: isMobile ? "24px 20px" : "36px 36px",
    marginBottom: "32px",
    boxShadow: "0 8px 30px rgba(0, 0, 0, 0.04)",
  };

  const badgeStyle: React.CSSProperties = {
    display: "inline-flex",
    alignItems: "center",
    gap: "6px",
    background: "rgba(25, 206, 139, 0.12)",
    color: "var(--accent-primary)",
    padding: "4px 12px",
    borderRadius: "9999px",
    fontSize: "12px",
    fontWeight: 700,
    marginBottom: "12px",
  };

  const citationBoxStyle: React.CSSProperties = {
    background: "#f8fafc",
    borderLeft: "3px solid var(--accent-primary)",
    borderRadius: "0 12px 12px 0",
    padding: "12px 16px",
    marginTop: "16px",
    fontSize: "13px",
    color: "#475569",
    lineHeight: 1.5,
  };

  return (
    <main
      style={{
        minHeight: "100dvh",
        padding: "32px 16px 96px",
        boxSizing: "border-box",
        background: "#f8fafc",
        color: "#111827",
      }}
    >
      <div style={{ maxWidth: "1000px", margin: "0 auto" }}>
        {/* Top bar with back link and lang switcher */}
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            marginBottom: "28px",
          }}
        >
          <Link
            href="/"
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: "6px",
              fontSize: "14px",
              fontWeight: 600,
              color: "var(--accent-primary)",
              textDecoration: "none",
            }}
          >
            <ArrowLeft size={16} weight="bold" />
            <span>{t("landing_science_back")}</span>
          </Link>

          {/* Segmented Language Selector */}
          <div
            style={{
              display: "inline-flex",
              alignItems: "center",
              background: "rgba(0, 0, 0, 0.05)",
              borderRadius: "9999px",
              padding: "3px",
              border: "1px solid rgba(0, 0, 0, 0.08)",
            }}
          >
            <button
              type="button"
              onClick={() => setLang("en")}
              style={{
                border: "none",
                background: lang === "en" ? "#ffffff" : "transparent",
                color: lang === "en" ? "#111827" : "#6b7280",
                fontWeight: lang === "en" ? 700 : 500,
                fontSize: "12px",
                padding: "4px 10px",
                borderRadius: "9999px",
                cursor: "pointer",
                boxShadow: lang === "en" ? "0 1px 3px rgba(0, 0, 0, 0.1)" : "none",
                transition: "all 0.15s ease",
                display: "inline-flex",
                alignItems: "center",
                gap: "4px",
              }}
              aria-label="Switch to English"
            >
              <span>🇺🇸</span>
              <span>EN</span>
            </button>
            <button
              type="button"
              onClick={() => setLang("vi")}
              style={{
                border: "none",
                background: lang === "vi" ? "#ffffff" : "transparent",
                color: lang === "vi" ? "#111827" : "#6b7280",
                fontWeight: lang === "vi" ? 700 : 500,
                fontSize: "12px",
                padding: "4px 10px",
                borderRadius: "9999px",
                cursor: "pointer",
                boxShadow: lang === "vi" ? "0 1px 3px rgba(0, 0, 0, 0.1)" : "none",
                transition: "all 0.15s ease",
                display: "inline-flex",
                alignItems: "center",
                gap: "4px",
              }}
              aria-label="Switch to Vietnamese"
            >
              <span>🇻🇳</span>
              <span>VI</span>
            </button>
          </div>
        </div>

        {/* Hero Header */}
        <div style={{ textAlign: "center", marginBottom: "40px" }}>
          <div style={badgeStyle}>
            <Flask size={16} weight="duotone" />
            <span>
              {lang === "vi"
                ? "CƠ SỞ KHOA HỌC & NỀN TẢNG DỰA TRÊN NGUỒN UY TÍN"
                : "EXERCISE PHYSIOLOGY & SCIENTIFIC GROUNDING"}
            </span>
          </div>
          <h1
            style={{
              fontFamily: "var(--font-schibsted), sans-serif",
              fontSize: "clamp(30px, 4.5vw, 46px)",
              fontWeight: 800,
              color: "#111827",
              letterSpacing: "-1.2px",
              margin: "0 0 12px",
            }}
          >
            {t("landing_science_title")}
          </h1>
          <p
            style={{
              fontSize: "17px",
              color: "#4b5563",
              maxWidth: "680px",
              margin: "0 auto",
              lineHeight: 1.5,
            }}
          >
            {t("landing_science_subtitle")}
          </p>
        </div>

        {/* Quick Navigation Jump Bar */}
        <div
          style={{
            background: "#ffffff",
            padding: "12px 16px",
            borderRadius: "16px",
            border: "1px solid rgba(0, 0, 0, 0.08)",
            marginBottom: "36px",
            boxShadow: "0 4px 16px rgba(0,0,0,0.03)",
            display: "flex",
            flexWrap: "wrap",
            gap: "8px",
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          <span style={{ fontSize: "12px", fontWeight: 700, color: "#6b7280", textTransform: "uppercase" }}>
            {lang === "vi" ? "Chuyển nhanh:" : "Jump to:"}
          </span>
          {[
            { href: "#thresholds", label: lang === "vi" ? "Ngưỡng AeT/AnT" : "Thresholds & AeT" },
            { href: "#adaptation", label: lang === "vi" ? "Thích ứng tuần" : "Adaptation & RPE" },
            { href: "#block-evaluation", label: lang === "vi" ? "Đánh giá Block" : "Block Review" },
            { href: "#muscular-endurance", label: "Muscular Endurance (ME)" },
            { href: "#coach-grounding", label: lang === "vi" ? "Trợ lý AI Coach" : "Coach Uphill RAG" },
            { href: "#pace-physics", label: lang === "vi" ? "Pace Strategy" : "Pace Strategy (Minetti)" },
            { href: "#goal-prediction", label: lang === "vi" ? "Goal Determiner" : "Goal Determiner (A/B/C)" },
            { href: "#gear-grounding", label: lang === "vi" ? "Gear Finder" : "Gear Catalog Grounding" },
            { href: "#nutrition-grounding", label: lang === "vi" ? "Nutrition Lab" : "Nutrition Science" },
          ].map((item) => (
            <a
              key={item.href}
              href={item.href}
              style={{
                fontSize: "12px",
                fontWeight: 600,
                color: "#374151",
                textDecoration: "none",
                background: "#f3f4f6",
                padding: "4px 10px",
                borderRadius: "8px",
                transition: "background 0.15s ease",
              }}
            >
              {item.label}
            </a>
          ))}
        </div>

        {/* Profile Explainer */}
        <div style={{ marginBottom: "40px", display: "flex", justifyContent: "center" }}>
          <ProfileExplainer lang={lang} />
        </div>

        {/* ── 1. STEP 1 & 2: THRESHOLDS (#thresholds) ───────────────── */}
        <section id="thresholds" style={sectionStyle}>
          <div style={badgeStyle}>
            <MapPin size={15} weight="bold" />
            <span>{lang === "vi" ? "BƯỚC 01 & 02 · HIỆU CHUẨN NGƯỠNG" : "STEPS 01 & 02 · THRESHOLD PRECISION"}</span>
          </div>
          <h2 style={{ fontSize: "24px", fontWeight: 800, color: "#111827", margin: "0 0 12px", letterSpacing: "-0.5px" }}>
            {lang === "vi"
              ? "Ngưỡng AeT / AnT & Mô Hình 5 Zone Nhịp Tim Cá Nhân Hóa"
              : "AeT / AnT Thresholds & The Individual 5-Zone Model"}
          </h2>
          <p style={{ fontSize: "15.5px", lineHeight: 1.65, color: "#374151", margin: "0 0 14px" }}>
            {lang === "vi"
              ? "Phần lớn runner chạy bền mắc Hội chứng Thiếu hụt Aerobic (Aerobic Deficiency Syndrome - ADS) vì chạy Easy quá nhanh, đẩy tim vào vùng lơ lửng và đốt cạn glycogen thay vì đốt mỡ. Coach Uphill xây dựng plan tập dựa trên hai ngưỡng thể chất thực tế: Aerobic Threshold (AeT) và Anaerobic Threshold (AnT) — thay vì các công thức 220-trừ-tuổi rập khuôn. Các bài chạy Zone 2 được chặn cứng dưới trần AeT để xây dựng mạng lưới ty thể dày đặc, giúp bạn duy trì khối lượng chạy trail mà không bị cạn năng lượng."
              : "Most endurance athletes suffer from Aerobic Deficiency Syndrome (ADS) because their 'easy' runs drift into a gray zone, burning glycogen instead of fatty acids. Coach Uphill anchors your training on your actual Aerobic Threshold (AeT) and Anaerobic Threshold (AnT) — not arbitrary 220-minus-age formulas. Zone 2 sessions are hard-capped below your AeT ceiling to build dense mitochondrial networks, allowing you to sustain mountain mileage without glycogen depletion."}
          </p>
          <div style={citationBoxStyle}>
            <div style={{ fontWeight: 700, color: "#0f172a", marginBottom: "4px" }}>
              <BookOpen size={16} style={{ display: "inline", verticalAlign: "middle", marginRight: "6px" }} />
              {lang === "vi" ? "Nguồn tài liệu gốc:" : "Primary Source Citation:"}
            </div>
            <em>Training for the Uphill Athlete</em> (2019) by Steve House, Scott Johnston, and Kilian Jornet. Chapter 3: &ldquo;Physiology of Endurance: Aerobic and Anaerobic Threshold Testing.&rdquo;
          </div>
        </section>

        {/* ── 2. STEP 3: ADAPTATION (#adaptation) ───────────────────── */}
        <section id="adaptation" style={sectionStyle}>
          <div style={badgeStyle}>
            <ArrowsClockwise size={15} weight="bold" />
            <span>{lang === "vi" ? "BƯỚC 03 · THÍCH ỨNG LINH HOẠT" : "STEP 03 · DYNAMIC ADAPTATION"}</span>
          </div>
          <h2 style={{ fontSize: "24px", fontWeight: 800, color: "#111827", margin: "0 0 12px", letterSpacing: "-0.5px" }}>
            {lang === "vi"
              ? "Độ Mỏi Thần Kinh - Cơ & Tự Động Điều Chỉnh Khối Lượng"
              : "Neuromuscular Fatigue & Adaptive Volume Scaling"}
          </h2>
          <p style={{ fontSize: "15.5px", lineHeight: 1.65, color: "#374151", margin: "0 0 14px" }}>
            {lang === "vi"
              ? "Các plan tập cố định dễ dẫn đến quá tải hoặc chấn thương vì bỏ qua stress cuộc sống, thiếu ngủ hay cơ bắp bị tàn phá khi đổ dốc. Coach Uphill kết hợp bộ chọn cảm giác chân 5 mức độ cùng tính năng theo dõi trượt nhịp tim (cardiac drift / aerobic decoupling) sau các bài Long Run. Nếu nhịp tim trượt hơn 5% so với pace hoặc bạn mệt ở mức 4–5, hệ thống sẽ tự động xếp lại lịch, hạ khối lượng tuần và chuyển thành Recovery Run thay vì ép bạn tập nặng."
              : "Rigid static plans fail because they ignore life stress, sleep deficits, and muscle damage from mountain descents. Coach Uphill incorporates a 5-level somatic feeling selector combined with cardiac drift (aerobic decoupling) tracking. If your heart rate drifts more than 5% relative to pace over a long run, or your subjective fatigue reaches Level 4/5, the engine automatically reschedules sessions, inserting recovery runs instead of forcing high-intensity workouts."}
          </p>
          <div style={citationBoxStyle}>
            <div style={{ fontWeight: 700, color: "#0f172a", marginBottom: "4px" }}>
              <BookOpen size={16} style={{ display: "inline", verticalAlign: "middle", marginRight: "6px" }} />
              {lang === "vi" ? "Nguồn tài liệu gốc:" : "Primary Source Citation:"}
            </div>
            Foster et al. (2001). &ldquo;A new approach to monitoring exercise training.&rdquo; <em>Journal of Strength and Conditioning Research</em>; and Seiler, S. (2010). &ldquo;What is best practice for training intensity and duration distribution in endurance athletes?&rdquo;
          </div>
        </section>

        {/* ── 3. STEP 4: BLOCK EVALUATION (#block-evaluation) ────────── */}
        <section id="block-evaluation" style={sectionStyle}>
          <div style={badgeStyle}>
            <Trophy size={15} weight="bold" />
            <span>{lang === "vi" ? "BƯỚC 04 · REVIEW BLOCK 4 TUẦN" : "STEP 04 · 4-WEEK BLOCK REVIEW"}</span>
          </div>
          <h2 style={{ fontSize: "24px", fontWeight: 800, color: "#111827", margin: "0 0 12px", letterSpacing: "-0.5px" }}>
            {lang === "vi"
              ? "Đánh Giá Block 4 Tuần & Tịnh Tiến Sang Block Tiếp Theo"
              : "4-Week Mesocycle Evaluation & Block-to-Block Progression"}
          </h2>
          <p style={{ fontSize: "15.5px", lineHeight: 1.65, color: "#374151", margin: "0 0 14px" }}>
            {lang === "vi"
              ? "Khả năng thích ứng của cơ thể trong chạy ultra diễn ra tốt nhất theo chu kỳ mesocycle 4 tuần: 3 tuần tăng tải lũy tiến + 1 tuần Deload hồi phục. Cuối mỗi block, Coach Uphill sẽ kiểm tra: tổng khối lượng hoàn thành, tỷ lệ km chạy thuần dưới ngưỡng AeT, và độ sẵn sàng của cơ bắp qua các bài Muscular Endurance (ME). Điểm đánh giá (ví dụ Grade A · 94% Quality) sẽ trực tiếp quyết định trần khối lượng và cường độ ME cho Block tiếp theo."
              : "Endurance adaptations follow 4-week mesocycles: 3 weeks of progressive overload followed by 1 week of regenerative deloading. At the end of each 4-week block, Coach Uphill audits total completed volume, percentage of aerobic mileage strictly under AeT, and eccentric strength readiness. The resulting letter grade (e.g. Grade A · 94% Quality) dynamically parameters the next block's volume ceiling and muscular endurance intensity."}
          </p>
          <div style={citationBoxStyle}>
            <div style={{ fontWeight: 700, color: "#0f172a", marginBottom: "4px" }}>
              <BookOpen size={16} style={{ display: "inline", verticalAlign: "middle", marginRight: "6px" }} />
              {lang === "vi" ? "Nguồn tài liệu gốc:" : "Primary Source Citation:"}
            </div>
            Issurin, V. (2010). &ldquo;New horizons for the methodology and physiology of training block periodization.&rdquo; <em>Sports Medicine</em>, 40(3), 189-206.
          </div>
        </section>

        {/* ── 4. SIGNATURE METHODOLOGY: MUSCULAR ENDURANCE (#muscular-endurance) ── */}
        <section id="muscular-endurance" style={sectionStyle}>
          <div style={badgeStyle}>
            <Barbell size={15} weight="bold" />
            <span>
              {lang === "vi"
                ? "PHƯƠNG PHÁP CỐT LÕI · DẤU ẤN SCOTT JOHNSTON"
                : "SIGNATURE METHODOLOGY · SCOTT JOHNSTON"}
            </span>
          </div>
          <h2 style={{ fontSize: "24px", fontWeight: 800, color: "#111827", margin: "0 0 12px", letterSpacing: "-0.5px" }}>
            {lang === "vi"
              ? "Muscular Endurance (ME): Sức Bền Cơ Bắp & Cỗ Máy Vượt Đèo Dốc"
              : "Muscular Endurance (ME): Bridging Strength and Mountain Longevity"}
          </h2>
          <p style={{ fontSize: "15.5px", lineHeight: 1.65, color: "#374151", margin: "0 0 14px" }}>
            {lang === "vi"
              ? "Muscular Endurance (ME) là phương pháp huấn luyện mang dấu ấn đặc trưng của Scott Johnston, giải quyết mắt xích yếu nhất trong chạy trail đường núi và cự ly ultra. Trong khi sức mạnh thuần túy (pure strength) là năng lực thần kinh huy động các đơn vị vận động, còn sức bền hiếu khí là sự chuyển hóa năng lượng (ATP) bên trong tế bào, thì ME là cầu nối: rèn luyện các nhóm cơ đẩy (propelling muscles) duy trì tỷ lệ lực phát ra tương đối cao so với lực tối đa trong hàng nghìn bước chạy liên tục mà không bị suy giảm cơ học."
              : "Muscular Endurance (ME) is Scott Johnston's signature training methodology, solving the definitive bottleneck in mountain and ultra-endurance running. While pure strength is primarily neurologic (training the central nervous system to recruit high-threshold motor units), endurance is metabolic (turning over ATP within muscle mitochondria). ME forms the critical bridge: conditioning propelling muscles to sustain submaximal force output across thousands of continuous repetitions without mechanical breakdown."}
          </p>

          <div
            style={{
              display: "grid",
              gridTemplateColumns: isMobile ? "1fr" : "1fr 1fr",
              gap: "14px",
              margin: "20px 0",
            }}
          >
            <div
              style={{
                background: "#f9fafb",
                border: "1px solid rgba(0, 0, 0, 0.06)",
                borderRadius: "14px",
                padding: "16px 18px",
              }}
            >
              <div style={{ fontWeight: 700, fontSize: "14.5px", color: "#111827", marginBottom: "6px" }}>
                {lang === "vi"
                  ? "Trái tim không phải điểm giới hạn"
                  : "The Heart is Not the Limiter"}
              </div>
              <p style={{ fontSize: "13.5px", lineHeight: 1.6, color: "#4b5563", margin: 0 }}>
                {lang === "vi"
                  ? "Trong các race chạy bền nhiều giờ, runner thi đấu dưới mức VO2max và nhịp tim tối đa rất xa. Hệ tim mạch trung tâm dư thừa khả năng cung cấp oxy. Yếu tố lớn nhất gây tụt pace về cuối race là độ mỏi cơ bắp cục bộ (local muscular fatigue) ở cơ đùi, cơ mông và bắp chân. Khi cơ chân mất khả năng tạo lực, lượng oxy tim bơm tới trở nên vô nghĩa."
                  : "In multi-hour events, athletes operate far below their maximum heart rate and VO2max. The central cardiovascular system has excess oxygen delivery capacity. The primary determinant of late-race deceleration is local muscular fatigue in propelling leg muscles. If the legs cannot sustain force production, cardiac oxygen delivery is moot."}
              </p>
            </div>

            <div
              style={{
                background: "#f9fafb",
                border: "1px solid rgba(0, 0, 0, 0.06)",
                borderRadius: "14px",
                padding: "16px 18px",
              }}
            >
              <div style={{ fontWeight: 700, fontSize: "14.5px", color: "#111827", marginBottom: "6px" }}>
                {lang === "vi"
                  ? "Thích ứng sợi cơ 'Frontier' & Máy hút bụi Aerobic"
                  : "Adapting 'Frontier' Fibers & The Aerobic Vacuum"}
              </div>
              <p style={{ fontSize: "13.5px", lineHeight: 1.6, color: "#4b5563", margin: 0 }}>
                {lang === "vi"
                  ? "Khi sợi cơ chậm (ST) mỏi dần khi leo dốc, não bộ huy động sợi nhanh (FTa) tiền tuyến. Sợi FTa tạo lực lớn nhưng chóng cạn kiệt nếu thiếu ty thể. Bài tập ME buộc sợi FTa phát triển ty thể để có sức bền aerobic. Đồng thời, sợi ST đóng vai trò 'chiếc máy hút bụi', thu nạp và đốt cháy lượng lactate sinh ra bởi sợi FTa, đẩy lùi ngưỡng mỏi AeT và AnT."
                  : "As slow-twitch (ST) fibers fatigue over hours or steep gradients, the brain recruits fast-twitch (FTa) 'frontier' fibers. FTa produce high force but fatigue rapidly without aerobic capacity. ME forces these frontier fibers to undergo mitochondrial biogenesis. Meanwhile, ST fibers act as an 'aerobic vacuum cleaner', shuttling and consuming lactate to elevate both AeT and AnT."}
              </p>
            </div>

            <div
              style={{
                background: "#f9fafb",
                border: "1px solid rgba(0, 0, 0, 0.06)",
                borderRadius: "14px",
                padding: "16px 18px",
              }}
            >
              <div style={{ fontWeight: 700, fontSize: "14.5px", color: "#111827", marginBottom: "6px" }}>
                {lang === "vi"
                  ? "Độ mỏi cục bộ vs. Kiệt sức toàn thân"
                  : "Local Overload vs. Global Systemic Fatigue"}
              </div>
              <p style={{ fontSize: "13.5px", lineHeight: 1.6, color: "#4b5563", margin: 0 }}>
                {lang === "vi"
                  ? "Chạy interval Zone 3–4 gây kiệt sức toàn thân (tăng vọt cortisol, axit hóa máu, hao mòn thần kinh CNS) cần nhiều ngày để hồi. Bài tập ME (leo dốc đeo balo tạ 10–20% trọng lượng, gym leg circuit) dồn tải nặng cục bộ vào cơ đẩy nhưng giữ nhịp tim trong Zone 2, giúp hồi phục nhanh và bảo toàn khối lượng chạy nền hàng tuần."
                  : "High-intensity intervals (Zones 3–4) impose massive global systemic fatigue (elevated cortisol, acidosis, CNS drain), requiring extended recovery. ME sessions (weighted uphill hikes 10–20% bodyweight, gym leg circuits) isolate heavy local muscular overload while keeping heart rate in Zone 2, allowing rapid recovery and sustaining high weekly Zone 1–2 volume."}
              </p>
            </div>

            <div
              style={{
                background: "#f9fafb",
                border: "1px solid rgba(0, 0, 0, 0.06)",
                borderRadius: "14px",
                padding: "16px 18px",
              }}
            >
              <div style={{ fontWeight: 700, fontSize: "14.5px", color: "#111827", marginBottom: "6px" }}>
                {lang === "vi"
                  ? "Đệm lực lệch tâm khi đổ dốc & Kinh tế sải chân"
                  : "Eccentric Downhill Cushioning & Stride Economy"}
              </div>
              <p style={{ fontSize: "13.5px", lineHeight: 1.6, color: "#4b5563", margin: 0 }}>
                {lang === "vi"
                  ? "Cơ bắp khỏe chỉ cần dùng tỷ lệ lực tối đa thấp hơn mỗi bước, biến gân cơ thành lò xo đàn hồi tự nhiên. Các bài tập bật nhảy và đổ dốc trong phương pháp tập ME rèn luyện sức chịu đựng lệch tâm (eccentric fatigue resistance), bảo vệ đùi trước khỏi bị xé rách cơ học trên các cung dốc dài của race."
                  : "Stronger, fatigue-resistant muscles expend a smaller fraction of maximum force per stride, allowing tendons to act like springs. Jumping circuits and downhill protocols build eccentric fatigue resistance, shielding quadriceps and calves from structural breakdown during sustained mountain descents."}
              </p>
            </div>
          </div>

          <div style={citationBoxStyle}>
            <div style={{ fontWeight: 700, color: "#0f172a", marginBottom: "4px" }}>
              <BookOpen size={16} style={{ display: "inline", verticalAlign: "middle", marginRight: "6px" }} />
              {lang === "vi" ? "Nguồn tài liệu gốc:" : "Primary Source Citation:"}
            </div>
            <em>Training for the Uphill Athlete</em> (2019) by Steve House, Scott Johnston, and Kilian Jornet. Chapter 7: &ldquo;Strength Training: General Strength, Specific Strength, and Muscular Endurance&rdquo; (pp. 174–215). Supporting literature: Paavolainen et al. (1999) &ldquo;Neuromuscular characteristics and running economy&rdquo;; Støren et al. (2008) &ldquo;Maximal strength training improves running economy in distance runners.&rdquo;
          </div>
        </section>

        {/* ── 5. CHAT COACH: COACH UPHILL (#coach-grounding) ─────────── */}
        <section id="coach-grounding" style={sectionStyle}>
          <div style={badgeStyle}>
            <Robot size={15} weight="bold" />
            <span>{lang === "vi" ? "CHAT COACH · NGUYÊN TẮC DỰA TRÊN NGUỒN UY TÍN" : "CHAT COACH · SCIENTIFIC REFUSAL POLICY"}</span>
          </div>
          <h2 style={{ fontSize: "24px", fontWeight: 800, color: "#111827", margin: "0 0 12px", letterSpacing: "-0.5px" }}>
            {lang === "vi"
              ? "Coach Uphill RAG: Cơ Sở Dữ Liệu Thực Nghiệm & Nguyên Tắc Từ Chối"
              : "RAG Grounding & Medical / Ergogenic Refusal Behavior"}
          </h2>
          <p style={{ fontSize: "15.5px", lineHeight: 1.65, color: "#374151", margin: "0 0 14px" }}>
            {lang === "vi"
              ? "Điểm khác biệt cốt lõi giữa Coach Uphill và các AI thông thường là tuyệt đối không suy đoán hay hallucinate. Chạy trên nền tảng Gemini 3.8 Flash với kiến trúc RAG (Retrieval-Augmented Generation), mọi câu trả lời đều được đối chiếu với kho tài liệu khoa học thể thao đã tuyển chọn kỹ lưỡng. Khi được hỏi về thực phẩm bổ sung chưa có bằng chứng xác đáng (như BCAA trong khi chạy ultra) hay chẩn đoán đau khớp cấp tính, Coach Uphill trích dẫn tài liệu gốc (*Training for the Uphill Athlete*) và dứt khoát từ chối đưa ra chẩn đoán y khoa hay quảng bá thực phẩm vô căn cứ."
              : "The defining differentiator of Coach Uphill is its strict refusal to guess or hallucinate. Operating on Gemini 3.8 Flash with Retrieval-Augmented Generation (RAG), every prompt is verified against a curated sports science and physiology corpus. When asked about unproven ergogenic aids (e.g. BCAAs during ultra runs) or acute joint pain, Coach Uphill cites primary literature (*Training for the Uphill Athlete*) and explicitly refuses to fabricate medical diagnoses or endorse ungrounded supplements."}
          </p>
          <div style={citationBoxStyle}>
            <div style={{ fontWeight: 700, color: "#0f172a", marginBottom: "4px" }}>
              <ShieldCheck size={16} style={{ display: "inline", verticalAlign: "middle", marginRight: "6px" }} />
              {lang === "vi" ? "Kiến trúc kiểm soát an toàn:" : "Safety Guardrail Architecture:"}
            </div>
            Gemini 3.8 Flash with domain-constrained system prompts, strict temperature regulation (0.2), and automated RAG verification against peer-reviewed sports nutrition and biomechanics databases.
          </div>
        </section>

        {/* ── 5. TOOL: PACE STRATEGY (#pace-physics) ────────────────── */}
        <section id="pace-physics" style={sectionStyle}>
          <div style={badgeStyle}>
            <Gauge size={15} weight="bold" />
            <span>{lang === "vi" ? "CÔNG CỤ · VẬT LÝ ĐỘ DỐC & ĐỘ CAO" : "TOOL · SLOPE & ALTITUDE PHYSICS"}</span>
          </div>
          <h2 style={{ fontSize: "24px", fontWeight: 800, color: "#111827", margin: "0 0 12px", letterSpacing: "-0.5px" }}>
            {lang === "vi"
              ? "Pace Strategy: Đường Cong Năng Lượng Minetti, Độ Cao & Độ Mỏi"
              : "Pace Strategy: The Minetti Cost Curve, Altitude & Fatigue Physics"}
          </h2>
          <p style={{ fontSize: "15.5px", lineHeight: 1.65, color: "#374151", margin: "0 0 14px" }}>
            {lang === "vi"
              ? "Tính Pace chạy trail không thể dùng phép chia cự ly trên thời gian như đường road. Pace Strategy áp dụng phương trình tiêu hao năng lượng chuyển hóa của Minetti (2002) (J/kg/m theo hàm bậc 5 của độ dốc). Khi leo dốc gắt, công cụ tự chuyển sang mô hình Power Hike tiết kiệm sức; khi đổ dốc gắt, công cụ tính thêm hệ số hãm cơ bắp (eccentric impact). Ở độ cao trên 1.500m, hệ thống áp dụng hệ số suy giảm oxy aerobic, kết hợp với độ mỏi cơ bắp tích lũy sau 15km tương đương đường bằng."
              : "Trail pacing cannot be solved with flat arithmetic. Pace Strategy employs the landmark Minetti et al. (2002) metabolic energy cost curve (J/kg/m as a 5th-degree polynomial function of gradient). Steep ascents trigger a power-hiking efficiency model, while steep descents factor in eccentric impact damping. Beyond 1,500m elevation, an aerobic saturation penalty is applied, coupled with progressive durability fatigue decay beyond 15 flat-equivalent kilometers."}
          </p>
          <div style={citationBoxStyle}>
            <div style={{ fontWeight: 700, color: "#0f172a", marginBottom: "4px" }}>
              <BookOpen size={16} style={{ display: "inline", verticalAlign: "middle", marginRight: "6px" }} />
              {lang === "vi" ? "Nguồn tài liệu gốc:" : "Primary Source Citation:"}
            </div>
            Minetti, A. E. et al. (2002). &ldquo;Energy cost of walking and running at extreme uphill and downhill slopes.&rdquo; <em>Journal of Applied Physiology</em>, 93(3), 1039-1046.
          </div>
        </section>

        {/* ── 6. TOOL: GOAL DETERMINER (#goal-prediction) ───────────── */}
        <section id="goal-prediction" style={sectionStyle}>
          <div style={badgeStyle}>
            <Crosshair size={15} weight="bold" />
            <span>{lang === "vi" ? "CÔNG CỤ · DỰ ĐOÁN THỜI GIAN VỀ ĐÍCH" : "TOOL · FINISH TIME PREDICTION"}</span>
          </div>
          <h2 style={{ fontSize: "24px", fontWeight: 800, color: "#111827", margin: "0 0 12px", letterSpacing: "-0.5px" }}>
            {lang === "vi"
              ? "Goal Determiner: Mô Phỏng Ngược Minetti & Mục Tiêu A/B/C Bất Đối Xứng"
              : "Goal Determiner: Reverse Minetti Modeling & Asymmetric A/B/C Goals"}
          </h2>
          <p style={{ fontSize: "15.5px", lineHeight: 1.65, color: "#374151", margin: "0 0 14px" }}>
            {lang === "vi"
              ? "Goal Determiner giải bài toán mô hình vật lý Minetti theo chiều ngược lại: từ Base Flat Pace hoặc kết quả race gần nhất, hệ thống tính tổng năng lượng cần thiết cho toàn bộ cự ly và profile độ dốc mới để dự đoán thời gian về đích. Nhằm phòng ngừa rủi ro thời tiết hay đau bụng ngày race, hệ thống đưa ra 3 mốc mục tiêu bất đối xứng về mặt toán học: Ambitious (~5% nhanh hơn), Realistic (mục tiêu thực tế & khả thi nhất), và Safe (~8% phòng ngừa rủi ro)."
              : "Goal Determiner solves the Minetti physical model in reverse: given your base flat pace or a prior race result on a known profile, it calculates total metabolic work required for the new course distance and vertical profile. To protect against race-day weather or GI failure, it derives three mathematically asymmetric goals: Ambitious (~5% faster), Realistic (statistically optimal target), and Safe (~8% buffer), corroborated by historical percentile rank transfer."}
          </p>
          <div style={citationBoxStyle}>
            <div style={{ fontWeight: 700, color: "#0f172a", marginBottom: "4px" }}>
              <BookOpen size={16} style={{ display: "inline", verticalAlign: "middle", marginRight: "6px" }} />
              {lang === "vi" ? "Nguồn tài liệu gốc:" : "Primary Source Citation:"}
            </div>
            Vickers, R. R., &amp; Vertosick, S. (2016). &ldquo;An empirical algorithm for estimating marathon and ultra-marathon finishing times from training volume and past race performances.&rdquo; <em>Medicine &amp; Science in Sports &amp; Exercise</em>.
          </div>
        </section>

        {/* ── 7. TOOL: GEAR FINDER (#gear-grounding) ────────────────── */}
        <section id="gear-grounding" style={sectionStyle}>
          <div style={badgeStyle}>
            <Sneaker size={15} weight="bold" />
            <span>{lang === "vi" ? "CÔNG CỤ · DANH MỤC GIÀY TUYỂN CHỌN & THÔNG SỐ CƠ SINH HỌC" : "TOOL · CATALOG GROUNDING & SHOE GEOMETRY"}</span>
          </div>
          <h2 style={{ fontSize: "24px", fontWeight: 800, color: "#111827", margin: "0 0 12px", letterSpacing: "-0.5px" }}>
            {lang === "vi"
              ? "Gear Finder: Danh Mục Giày Tuyển Chọn & Đề Xuất Theo Cơ Sinh Học"
              : "Gear Finder: Curated Shoe Catalog & Biomechanical Matching"}
          </h2>
          <p style={{ fontSize: "15.5px", lineHeight: 1.65, color: "#374151", margin: "0 0 14px" }}>
            {lang === "vi"
              ? "AI tuyệt đối không được tự bịa ra những mẫu giày ảo. Gear Finder nạp danh mục giày trail và road thực tế đã được tuyển chọn (Salomon, Hoka, Nike, adidas, Asics, Altra, Norda...) trực tiếp vào prompt. Đề xuất bám sát các thông số cơ sinh học: độ dốc gót-mũi (drop, ví dụ 4mm vs 8mm tùy tải gân Achilles hay đùi trước), độ dày đệm (stack height), thiết kế gai đế (lug depth 4.5mm cho bùn đất trơn) và tấm bảo vệ bàn chân (rock plate). Một bước lọc thứ hai sẽ đối chiếu lại toàn bộ thông số với danh mục trước khi hiển thị."
              : "AI systems must never invent phantom shoe models. Gear Finder injects a verified, structured catalog of current trail and road shoes into the prompt window. Recommendations match exact biomechanical parameters: heel-to-toe drop (e.g. 4mm vs 8mm for Achilles vs quad load), stack height, lug geometry (4.5mm chevron lugs for wet clay), and rock plate protection. A secondary verification pass confirms the product exists in the catalog with 100% fidelity before presentation."}
          </p>
          <div style={citationBoxStyle}>
            <div style={{ fontWeight: 700, color: "#0f172a", marginBottom: "4px" }}>
              <Compass size={16} style={{ display: "inline", verticalAlign: "middle", marginRight: "6px" }} />
              {lang === "vi" ? "Cơ sở dữ liệu tuyển chọn:" : "Curated Product Registry:"}
            </div>
            Verified technical specifications compiled from lab testing (RunRepeat, Doctor of Running) and official manufacturer spec sheets (Salomon, Hoka, Nike, Altra, Asics, Saucony).
          </div>
        </section>

        {/* ── 8. TOOL: NUTRITION LAB (#nutrition-grounding) ─────────── */}
        <section id="nutrition-grounding" style={sectionStyle}>
          <div style={badgeStyle}>
            <BowlFood size={15} weight="bold" />
            <span>{lang === "vi" ? "CÔNG CỤ · CHUYỂN HÓA CARBS & ĐIỆN GIẢI" : "TOOL · EXOGENOUS CARB & SODIUM METABOLISM"}</span>
          </div>
          <h2 style={{ fontSize: "24px", fontWeight: 800, color: "#111827", margin: "0 0 12px", letterSpacing: "-0.5px" }}>
            {lang === "vi"
              ? "Nutrition Lab: Hấp Thụ 60–90g Carbs/Giờ & Gut Training"
              : "Nutrition Lab: 60–90g/hr Carbohydrate Oxidation & Gut Training"}
          </h2>
          <p style={{ fontSize: "15.5px", lineHeight: 1.65, color: "#374151", margin: "0 0 14px" }}>
            {lang === "vi"
              ? "Đau dạ dày / rối loạn tiêu hóa và hạ natri máu là hai nguyên nhân hàng đầu khiến runner DNF ở các cự ly ultra. Nutrition Lab tính toán mục tiêu fueling mỗi giờ dựa trên ngưỡng bão hòa của thụ thể đường ruột: 60g/giờ cho nguồn glucose đơn lẻ hoặc lên tới 90g/giờ với tỷ lệ đa nguồn 1:0.8 hoặc 2:1 (maltodextrin:fructose). Lượng muối (sodium) được tính từ 500mg đến 1.000mg/giờ tùy theo nhiệt độ ngày race. Quan trọng nhất, hệ thống yêu cầu thực hành Gut training trong các bài Long Run xuyên suốt các block tập để dạ dày kịp thích nghi trước ngày race."
              : "Gastrointestinal distress and hyponatremia are the primary causes of ultra-endurance DNFs. Nutrition Lab sets hourly targets aligned with intestinal transporter saturation: 60g/hr for single-source glucose or up to 90g/hr using multi-transportable 1:0.8 / 2:1 maltodextrin-to-fructose ratios. Sodium is scaled between 500mg and 1,000mg/hour based on forecasted ambient heat. Crucially, the engine mandates gut training during training blocks, ensuring intestinal tolerance prior to race day."}
          </p>
          <div style={citationBoxStyle}>
            <div style={{ fontWeight: 700, color: "#0f172a", marginBottom: "4px" }}>
              <BookOpen size={16} style={{ display: "inline", verticalAlign: "middle", marginRight: "6px" }} />
              {lang === "vi" ? "Nguồn tài liệu gốc:" : "Primary Source Citation:"}
            </div>
            Jeukendrup, A. (2014). &ldquo;A step towards personalized sports nutrition: carbohydrate intake during exercise.&rdquo; <em>Sports Medicine</em>, 44(Suppl 1), 25-33; and Costa et al. (2017). &ldquo;Gut-training: can the gut be trained to tolerate more fuel during endurance exercise?&rdquo;
          </div>
        </section>

        {/* Feature Grid Deep Dives & Modals */}
        <div style={{ marginTop: "48px" }}>
          <h3 style={{ textAlign: "center", fontSize: "20px", fontWeight: 700, color: "#111827", marginBottom: "20px" }}>
            {lang === "vi" ? "Khám phá chi tiết từng tính năng" : "Explore Feature Deep Dives"}
          </h3>
          <div style={{ display: "flex", justifyContent: "center" }}>
            <FeatureGrid lang={lang} isMobile={isMobile} />
          </div>
        </div>
      </div>
    </main>
  );
}
