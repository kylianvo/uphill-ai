export type FeatureId = "scheduler" | "chatbot" | "goal" | "pace" | "gear" | "nutrition";
export type FeatureIcon = "Calendar" | "Robot" | "Crosshair" | "Gauge" | "Sneaker" | "BowlFood";

export type FeatureCopy = {
  tagline: string;
  cardBlurb: string;
  overview: string;
  howItWorks: string[];
  personalizedNote: string;
  personalizedChips: string[];
  alwaysUpdated: string;
};

export type FeatureContent = {
  id: FeatureId;
  icon: FeatureIcon;
  en: FeatureCopy;
  vi: FeatureCopy;
};

export const LANDING_FEATURES: FeatureContent[] = [
  {
    id: "scheduler",
    icon: "Calendar",
    en: {
      tagline: "Your training plan, built on the book the sport's best wrote.",
      cardBlurb: "Structured weekly training grounded in Training for the Uphill Athlete — adapted to your own thresholds, injury history, and goal race.",
      overview: "Coach Uphill builds your week around the aerobic-first philosophy of Training for the Uphill Athlete, co-written by Kilian Jornet, Scott Johnston, and Steve House — every session is generated against your own numbers, not a generic template.",
      howItWorks: [
        "{{term:zones}}5-zone heart rate model{{/term}} anchored on your own {{term:aet}}AeT{{/term}} and {{term:ant}}AnT{{/term}}, not age-predicted max HR.",
        "Automatic {{term:eighty_twenty}}80/20{{/term}} audit keeps every week at least ~80% easy.",
        "{{term:muscular_endurance}}Muscular endurance{{/term}} blocks — hill sprints, weighted step-ups — for legs that don't give out on descents.",
        "Treadmill mode converts any session into an exact grade-adjusted speed/incline pair.",
      ],
      personalizedNote: "Built from your thresholds, injury history, and active training load.",
      personalizedChips: ["AeT / AnT", "Injury history", "Goal race terrain"],
      alwaysUpdated: "The coaching knowledge base is periodically redistilled from primary sources, so advice isn't frozen to one training era.",
    },
    vi: {
      tagline: "Giáo án của bạn, xây dựng trên nền tảng khoa học huấn luyện đỉnh cao.",
      cardBlurb: "Lịch tập hàng tuần bài bản, dựa trên Training for the Uphill Athlete — cuốn sách kinh điển của Kilian Jornet, Scott Johnston và Steve House — cá nhân hóa theo đúng ngưỡng thể lực, tiền sử chấn thương và giải mục tiêu của bạn.",
      overview: "Coach Uphill xây dựng chu kỳ tập luyện xoay quanh triết lý \"hiếu khí (aerobic) là nền tảng\" của Training for the Uphill Athlete — được đúc kết bởi kỷ lục gia ultra-trail Kilian Jornet, HLV Scott Johnston và Steve House. Không dùng giáo án đại trà — từng bài tập được thiết kế riêng từ chỉ số thể chất thực tế của bạn.",
      howItWorks: [
        "{{term:zones}}5 vùng nhịp tim (Zones){{/term}} neo theo ngưỡng {{term:aet}}AeT{{/term}} và {{term:ant}}AnT{{/term}} của riêng bạn, thay vì công thức ước tính theo tuổi thông thường.",
        "Tự động tối ưu nguyên tắc {{term:eighty_twenty}}80/20{{/term}} — hệ thống cân bằng mỗi tuần để đảm bảo ít nhất ~80% thời lượng ở cường độ Easy.",
        "Bài tập {{term:muscular_endurance}}Muscular Endurance (Sức bền cơ bắp){{/term}} — Hill Sprints, Weighted Step-ups — giải quyết triệt để tình trạng mỏi cơ và kiệt sức ở những đoạn đổ dốc dài cuối giải.",
        "Chế độ Treadmill quy đổi các bài chạy đồi dốc ngoài trời thành cặp Tốc độ/Độ dốc (Incline) chính xác trên máy chạy bộ.",
      ],
      personalizedNote: "Dựa trên ngưỡng thể lực, tiền sử chấn thương và khối lượng tập luyện hiện tại của bạn.",
      personalizedChips: ["AeT / AnT", "Tiền sử chấn thương", "Địa hình giải mục tiêu"],
      alwaysUpdated: "Knowledge Base huấn luyện được chắt lọc từ tài liệu chuẩn khoa học và cập nhật liên tục — giáo án luôn đồng hành cùng sự tiến bộ của bạn.",
    },
  },
  {
    id: "chatbot",
    icon: "Robot",
    en: {
      tagline: "Ask anything. Get an answer grounded in real training science.",
      cardBlurb: "Pacing, fueling, \"should I run through this knee twinge\" — Coach Uphill answers from a curated knowledge base, and says \"I don't know\" rather than guess.",
      overview: "Coach Uphill runs on Gemini 2.5 Flash, but every answer is {{term:rag}}RAG{{/term}}-{{term:grounded}}grounded{{/term}} against a curated knowledge base before it replies.",
      howItWorks: [
        "Your question is matched against training philosophy, nutrition science, and gear data before the model answers.",
        "Coaching principles are built into the system prompt: aerobic-first trail methodology, 80/20 for road running, sweat-rate hydration math, biomechanics-first shoe fitting.",
        "Refuses to fabricate — if the knowledge base doesn't cover it, it says so instead of inventing specifics.",
        "Reads your active plan — ask \"what's today's workout\" and it references your real calendar.",
      ],
      personalizedNote: "Uses your active plan and running profile.",
      personalizedChips: ["Active plan", "Goals & injury notes", "English / Vietnamese"],
      alwaysUpdated: "Shares the same knowledge base as the rest of the app — new gear, science, and race data flow into chat automatically.",
    },
    vi: {
      tagline: "Hỏi đáp chuyên sâu cùng AI Coach. Câu trả lời chuẩn khoa học, có căn cứ rõ ràng.",
      cardBlurb: "Hỏi về Pacing, Fueling, xử lý chấn thương — Coach Uphill trả lời dựa trên Knowledge Base đã được kiểm chứng khoa học, tuyệt đối không suy đoán tùy tiện.",
      overview: "Coach Uphill vận hành trên nền tảng Gemini 2.5 Flash kết hợp kiến trúc {{term:rag}}RAG{{/term}}-{{term:grounded}}Grounded{{/term}}, đối chiếu trực tiếp dữ liệu huấn luyện từ kho tri thức trước khi đưa ra câu trả lời.",
      howItWorks: [
        "Câu hỏi của bạn được đối chiếu với kho tri thức về nguyên lý huấn luyện, khoa học dinh dưỡng và trang thiết bị.",
        "Nguyên tắc huấn luyện chuẩn: phương pháp Aerobic-first cho trail, nguyên tắc 80/20, công thức bù nước/điện giải theo Sweat Rate, và tư vấn giày dựa trên cơ sinh học bàn chân.",
        "Độ tin cậy cao — nếu Knowledge Base không có dữ liệu, AI Coach sẽ thông báo rõ ràng và quay về các nguyên tắc cốt lõi thay vì suy đoán thông tin sai lệch.",
        "Đồng bộ với giáo án đang tập — hỏi \"hôm nay tập gì\", AI Coach sẽ tham chiếu chính xác lịch tập thực tế của bạn.",
      ],
      personalizedNote: "Dựa trên giáo án đang hoạt động và hồ sơ thể chất của bạn.",
      personalizedChips: ["Giáo án đang hoạt động", "Mục tiêu & tiền sử chấn thương", "Song ngữ Anh / Việt"],
      alwaysUpdated: "Dùng chung Knowledge Base với toàn bộ nền tảng — dữ liệu khoa học và sản phẩm mới luôn được cập nhật tự động.",
    },
  },
  {
    id: "goal",
    icon: "Crosshair",
    en: {
      tagline: "Turn your fitness — or a past race — into a real race-day target.",
      cardBlurb: "Predicts your finish time on any course from a past result or current pace, then splits it into Ambitious, Realistic, and Safe goals.",
      overview: "Goal Determiner runs the same pacing physics as Pace Strategy in reverse: feed it a pace or a past result, and it predicts your finish time on a new course.",
      howItWorks: [
        "Two ways in: your {{term:base_flat_pace}}base flat pace{{/term}} directly, or a past finish time on a known course.",
        "Time-to-race adjustment assumes ~0.25%/week improvement, capped at 5% total.",
        "{{term:ab_c_goals}}A/B/C goals{{/term}}, deliberately asymmetric — Ambitious ~5% faster, Safe ~8% slower.",
        "{{term:rank_transfer}}Rank transfer{{/term}} sanity-checks the target against past finishers, when data exists.",
        "Same engine as Pace Strategy, on purpose — your goal and your pacing plan never disagree.",
      ],
      personalizedNote: "Uses your pace history and the target course's exact profile.",
      personalizedChips: ["Pace / race history", "Course distance & elevation"],
      alwaysUpdated: "Pulls from the same curated race-course database used by Pace Strategy, Gear Finder, and Nutrition.",
    },
    vi: {
      tagline: "Xác định mục tiêu về đích thực tế từ phong độ hiện tại hoặc giải chạy gần nhất.",
      cardBlurb: "Dự đoán thời gian hoàn thành trên mọi cung đường từ thành tích cũ hoặc Pace hiện tại, thiết lập 3 kịch bản mục tiêu: Ambitious, Realistic, Safe.",
      overview: "Goal Determiner sử dụng mô hình vật lý tương tự Pace Strategy: dựa trên Base Flat Pace hoặc kết quả giải đấu trước, hệ thống dự đoán thời gian về đích cho cung đường mới và phân bổ mục tiêu rõ ràng.",
      howItWorks: [
        "Hai phương thức nhập dữ liệu: {{term:base_flat_pace}}Base Flat Pace (Pace đường bằng){{/term}} hoặc thành tích giải chạy gần nhất.",
        "Hiệu chỉnh thời gian chuẩn bị trước giải: tính toán mức cải thiện thể lực ~0.25%/tuần (tối đa 5%).",
        "Kịch bản mục tiêu {{term:ab_c_goals}}A/B/C Goals{{/term}} — Kế hoạch A (Ambitious: nhanh hơn ~5%), B (Realistic: thực tế), C (Safe: dự phòng an toàn chậm hơn ~8%).",
        "{{term:rank_transfer}}Rank Transfer{{/term}} đối chiếu thứ hạng percentile của bạn với kết quả các mùa giải trước.",
        "Đồng bộ với công cụ Pace Strategy để đảm bảo mục tiêu và kế hoạch Pacing luôn khớp nhau.",
      ],
      personalizedNote: "Dựa trên lịch sử Pace/thành tích của bạn và thông số chính xác của cung đường mục tiêu.",
      personalizedChips: ["Pace / Lịch sử giải đấu", "Cự ly & Elevation Gain (D+)"],
      alwaysUpdated: "Khai thác dữ liệu từ cùng cơ sở dữ liệu đường chạy với Pace Strategy, Gear Vault và Nutrition Lab.",
    },
  },
  {
    id: "pace",
    icon: "Gauge",
    en: {
      tagline: "Checkpoint-by-checkpoint pacing for your exact course.",
      cardBlurb: "Grade, altitude, fatigue, and live race-day weather all factored into your splits — not just distance divided by goal time.",
      overview: "Pace Strategy models how your pace actually changes segment by segment based on the real physical demands of the course, then solves backwards to hit your target finish time.",
      howItWorks: [
        "Grade: uses the {{term:minetti_curve}}Minetti cost curve{{/term}}, with damping on descents and a hiking-economy cap on steep climbs.",
        "{{term:altitude_penalty}}Altitude penalty{{/term}} applies above ~1,500m elevation.",
        "{{term:durability}}Fatigue decay{{/term}} kicks in after roughly 15 flat-equivalent km.",
        "Live weather: heat above 15°C and rain both apply real slowdown penalties.",
        "{{term:split_bias}}Split bias{{/term}} — dial in a negative split or even effort.",
      ],
      personalizedNote: "Uses your body weight, GPX route, and live race-day weather.",
      personalizedChips: ["Body weight", "GPX route", "Live weather"],
      alwaysUpdated: "Weather comes from a live forecast API pulled fresh for each plan, not a seasonal average.",
    },
    vi: {
      tagline: "Chiến thuật Pace Strategy chi tiết theo từng Checkpoint.",
      cardBlurb: "Độ dốc, độ cao, mệt mỏi tích lũy và thời tiết ngày thi đấu đều được tính toán vào từng Split — không chỉ chia đều quãng đường cho thời gian.",
      overview: "Pace Strategy mô phỏng sự biến thiên nỗ lực và Pace theo từng đoạn dốc thực tế của cung đường, từ đó phân bổ thời gian tối ưu để bạn đạt mốc Target Time mong muốn.",
      howItWorks: [
        "Độ dốc: áp dụng mô hình {{term:minetti_curve}}Minetti Curve{{/term}} có bù trừ lực hãm khi xuống dốc và tối ưu sức bền đi bộ (Power Hike) khi dốc gắt.",
        "{{term:altitude_penalty}}Ảnh hưởng độ cao{{/term}}: áp dụng tính toán giảm hiệu suất hiếu khí ở độ cao trên 1.500m.",
        "{{term:durability}}Hệ số mỏi tích lũy (Fatigue Decay){{/term}}: bắt đầu tác động sau khoảng 15km tương đương đường bằng.",
        "Thời tiết thực tế: nhiệt độ cao trên 15°C và mưa gió đều được quy đổi thành hệ số điều chỉnh Pace tương ứng.",
        "{{term:split_bias}}Split Bias{{/term}} — tùy chỉnh chiến thuật Negative Split (nửa sau nhanh hơn) hoặc Even Effort (giữ sức đều).",
      ],
      personalizedNote: "Dựa trên cân nặng, file GPX cung đường và thời tiết thực tế ngày thi đấu.",
      personalizedChips: ["Cân nặng", "File GPX", "Thời tiết thực tế"],
      alwaysUpdated: "Dữ liệu thời tiết được cập nhật từ API dự báo thời gian thực mỗi khi bạn lập kế hoạch.",
    },
  },
  {
    id: "gear",
    icon: "Sneaker",
    en: {
      tagline: "Shoe recommendations from a real, curated catalog — never guessed.",
      cardBlurb: "Matched to your foot, surface, budget, and goal race from a curated catalog of current trail and road shoes — every rec traces back to a real product.",
      overview: "Gear Finder doesn't let the AI freestyle shoe names — every recommendation traces back to a real, {{term:catalog_grounded}}catalog-grounded{{/term}} entry.",
      howItWorks: [
        "The full distilled catalog is injected for every query, so nothing gets missed to a semantic-search near-miss.",
        "Curated only from major reviews across a fixed brand set — Hoka, Salomon, Nike, adidas, Asics, On, Altra, Norda, Saucony, Brooks, New Balance, and more.",
        "Hallucination guard checks every recommendation against the real catalog after generation.",
        "Matches on {{term:stack_height}}stack height{{/term}}, {{term:drop}}drop{{/term}}, {{term:carbon_plate}}carbon plate{{/term}}, and {{term:lug_depth}}lug depth{{/term}}.",
      ],
      personalizedNote: "Uses your fit preferences, budget, and matched race terrain.",
      personalizedChips: ["Fit / brand preference", "Budget", "Race terrain"],
      alwaysUpdated: "The catalog is refreshed through a periodic, admin-curated distillation pass.",
    },
    vi: {
      tagline: "Gợi ý giày chạy từ cơ sở dữ liệu sản phẩm thật — chuẩn xác và minh bạch.",
      cardBlurb: "So khớp chính xác theo form chân, bề mặt địa hình, ngân sách và cự ly giải mục tiêu từ danh mục giày Trail & Road tuyển chọn — mọi đề xuất đều là sản phẩm thực tế.",
      overview: "Gear Vault không sử dụng AI suy diễn tự do — mọi gợi ý đều được {{term:catalog_grounded}}bảo chứng từ danh mục sản phẩm thực tế{{/term}} đã được kiểm chứng kỹ lưỡng.",
      howItWorks: [
        "Nạp toàn bộ danh mục sản phẩm vào ngữ cảnh xử lý, đảm bảo tìm ra đôi giày phù hợp nhất với đặc tính của bạn.",
        "Tuyển chọn từ các nguồn đánh giá uy tín hàng đầu cho các thương hiệu lớn: Hoka, Salomon, Nike, adidas, Asics, On, Altra, Norda, Saucony, Brooks, New Balance...",
        "Cơ chế kiểm định chống sai sót: kiểm tra đối chiếu từng mẫu giày với danh mục chính hãng sau khi gợi ý.",
        "So khớp chi tiết theo {{term:stack_height}}Stack Height{{/term}}, {{term:drop}}Drop (độ dốc đế){{/term}}, {{term:carbon_plate}}Carbon Plate{{/term}} và {{term:lug_depth}}Lug Depth (gai đế){{/term}}.",
      ],
      personalizedNote: "Dựa trên sở thích form giày, ngân sách và địa hình giải chạy của bạn.",
      personalizedChips: ["Form giày / Thương hiệu", "Ngân sách", "Địa hình giải chạy"],
      alwaysUpdated: "Danh mục sản phẩm được làm mới và cập nhật định kỳ.",
    },
  },
  {
    id: "nutrition",
    icon: "BowlFood",
    en: {
      tagline: "An hour-by-hour fueling plan, built from real products.",
      cardBlurb: "Carbs, sodium, and format matched to your race length, the heat, and your gut tolerance — using a curated catalog of popular nutrition products.",
      overview: "Nutrition Lab builds a race-fueling strategy the way a sports dietitian would: starting from your targets, then filling in with real products, hour by hour.",
      howItWorks: [
        "Defaults to 60g {{term:carb_oxidation}}carb oxidation{{/term}}/hour and 500mg {{term:sodium_rate}}sodium{{/term}}/hour, scaling sodium toward 1,000mg/hour in heat.",
        "Full-catalog grounding — sees the entire distilled product catalog (gels, chews, drink mixes, real food) for every request.",
        "Output is a structured hour-by-hour action list, not just a product list.",
        "{{term:gut_training}}Gut-training{{/term}}-aware — built on practicing race-day intake in training, not trying something new on race day.",
      ],
      personalizedNote: "Uses your race distance, weather, and active plan context.",
      personalizedChips: ["Race distance & elevation", "Weather", "Format preference"],
      alwaysUpdated: "Product catalog refreshed through the same curated distillation pipeline as Gear Finder.",
    },
    vi: {
      tagline: "Chiến lược Fueling & Dinh dưỡng theo từng giờ từ sản phẩm thực tế.",
      cardBlurb: "Tính toán lượng Carbs, Sodium và dạng sản phẩm (Gel, Chews, Nước điện giải, Thức ăn thật) phù hợp với cự ly, điều kiện thời tiết và khả năng dung nạp của hệ tiêu hóa.",
      overview: "Nutrition Lab xây dựng kế hoạch Fueling chuẩn xác như một chuyên gia dinh dưỡng thể thao: xuất phát từ nhu cầu năng lượng của bạn và phân bổ chi tiết theo từng mốc giờ thi đấu.",
      howItWorks: [
        "Mặc định mục tiêu 60g {{term:carb_oxidation}}Carb Oxidation{{/term}}/giờ và 500mg {{term:sodium_rate}}Sodium{{/term}}/giờ, tự động tăng lượng điện giải lên tới 1.000mg/giờ khi thời tiết nắng nóng.",
        "Khai thác toàn bộ danh mục sản phẩm năng lượng thực tế (Gel năng lượng, Chews, Bột điện giải, Thức ăn thật).",
        "Kế hoạch chi tiết theo từng giờ: thời điểm và lượng dung nạp cụ thể — không chỉ là danh sách sản phẩm rời rạc.",
        "Định hướng {{term:gut_training}}Gut Training{{/term}} — khuyến khích thực hành chiến lược Fueling ngay trong các bài tập Long Run, tránh thử nghiệm mới trong ngày race.",
      ],
      personalizedNote: "Dựa trên cự ly giải đấu, thời tiết dự kiến và giáo án bạn đang tập luyện.",
      personalizedChips: ["Cự ly & Elevation Gain (D+)", "Thời tiết", "Dạng sản phẩm ưu tiên"],
      alwaysUpdated: "Danh mục dinh dưỡng được đồng bộ và cập nhật liên tục cùng hệ sinh thái Gear Vault.",
    },
  },
];
