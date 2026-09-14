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
      tagline: "Plan tập của bạn, xây dựng từ cuốn sách của những tượng đài đường núi.",
      cardBlurb: "Lịch tập tuần bài bản dựa trên cuốn Training for the Uphill Athlete — thiết kế theo đúng ngưỡng tim, tiền sử chấn thương và giải đấu mục tiêu của bạn.",
      overview: "Coach Uphill lên lịch tập xoay quanh triết lý ưu tiên nền tảng hiếu khí (aerobic) của cuốn Training for the Uphill Athlete (đồng tác giả bởi Kilian Jornet, Scott Johnston và Steve House) — mỗi bài chạy đều được tạo theo đúng chỉ số của bạn, không dùng template rập khuôn.",
      howItWorks: [
        "{{term:zones}}Mô hình 5 vùng nhịp tim{{/term}} dựa trên đúng ngưỡng {{term:aet}}AeT{{/term}} và {{term:ant}}AnT{{/term}} của bạn, không tính theo công thức Max HR theo tuổi.",
        "Tự động kiểm tra tỷ lệ {{term:eighty_twenty}}80/20{{/term}} để đảm bảo mỗi tuần có ít nhất ~80% thời lượng chạy Easy.",
        "Các bài tập {{term:muscular_endurance}}Muscular Endurance (ME){{/term}} — Hill Sprint, Weighted Step-up — giúp chân không bị quá tải khi đổ dốc dài.",
        "Chế độ Treadmill quy đổi mọi bài chạy thành cặp thông số Tốc độ và Độ dốc (Incline) chính xác trên máy chạy bộ.",
      ],
      personalizedNote: "Dựa trên ngưỡng tim, tiền sử chấn thương và khối lượng tập luyện hiện tại của bạn.",
      personalizedChips: ["AeT / AnT", "Tiền sử chấn thương", "Địa hình giải chạy"],
      alwaysUpdated: "Kho kiến thức huấn luyện được chắt lọc định kỳ từ tài liệu gốc, giúp nội dung không bị lỗi thời.",
    },
  },
  {
    id: "chatbot",
    icon: "Robot",
    en: {
      tagline: "Ask anything. Get an answer grounded in real training science.",
      cardBlurb: "Pacing, fueling, \"should I run through this knee twinge\" — Coach Uphill answers from a curated knowledge base, and says \"I don't know\" rather than guess.",
      overview: "Coach Uphill runs on Gemini 3.8 Flash, but every answer is {{term:rag}}RAG{{/term}}-{{term:grounded}}grounded{{/term}} against a curated knowledge base before it replies.",
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
      tagline: "Hỏi đáp cùng AI Coach. Câu trả lời dựa trên khoa học thể thao thực tế.",
      cardBlurb: "Từ pacing, fueling, đến \"đầu gối hơi nhói có nên chạy tiếp không\" — Coach Uphill trả lời dựa trên kho kiến thức đã tuyển chọn, và thà nói \"tôi không biết\" chứ không đoán mò.",
      overview: "Coach Uphill chạy trên nền tảng Gemini 3.8 Flash, nhưng mỗi câu trả lời đều được {{term:grounded}}đối chiếu{{/term}} với {{term:rag}}kho kiến thức{{/term}} đã tuyển chọn trước khi phản hồi.",
      howItWorks: [
        "Câu hỏi của bạn được đối chiếu với nguyên lý tập luyện, khoa học dinh dưỡng và dữ liệu thiết bị trước khi đưa ra câu trả lời.",
        "Nguyên lý huấn luyện cốt lõi: ưu tiên nền tảng Aerobic cho trail, tỷ lệ 80/20 cho road, tính toán bù nước theo Sweat Rate và chọn giày theo cơ sinh học bàn chân.",
        "Không bịa thông tin — nếu kho kiến thức chưa có dữ liệu, Coach sẽ nói rõ thay vì tự ý bịa ra chi tiết.",
        "Đọc trực tiếp plan đang tập — chỉ cần hỏi \"hôm nay tập bài gì\", Coach sẽ mở đúng lịch tập của bạn.",
      ],
      personalizedNote: "Dựa trên plan đang chạy và profile chạy bộ của bạn.",
      personalizedChips: ["Plan đang chạy", "Mục tiêu & chấn thương", "Song ngữ Anh / Việt"],
      alwaysUpdated: "Dùng chung kho kiến thức với toàn bộ ứng dụng — trang thiết bị, khoa học và dữ liệu giải chạy mới luôn được cập nhật tự động.",
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
      tagline: "Biến thể lực hiện tại — hoặc kết quả race cũ — thành mục tiêu thi đấu thực tế.",
      cardBlurb: "Dự đoán thời gian về đích trên mọi cung đường từ kết quả race cũ hoặc pace hiện tại, rồi chia thành 3 mốc mục tiêu: Ambitious, Realistic và Safe.",
      overview: "Goal Determiner dùng chung mô hình tính toán với Pace Strategy theo chiều ngược lại: chỉ cần nhập pace đường bằng hoặc kết quả race cũ, công cụ sẽ dự đoán thời gian về đích trên cung đường mới.",
      howItWorks: [
        "Hai cách nhập: nhập trực tiếp {{term:base_flat_pace}}base flat pace{{/term}}, hoặc thời gian về đích ở một giải chạy trước đó.",
        "Hệ số thời gian đến ngày race tính toán mức tiến bộ ~0.25%/tuần, tối đa 5%.",
        "Mục tiêu {{term:ab_c_goals}}A/B/C goals{{/term}} phân bổ bất đối xứng: Ambitious nhanh hơn ~5%, Safe chậm hơn ~8%.",
        "{{term:rank_transfer}}Rank transfer{{/term}} đối chiếu mục tiêu với thứ hạng của các finisher mùa trước (khi có dữ liệu).",
        "Chạy cùng thuật toán với Pace Strategy — đảm bảo mục tiêu và kế hoạch pacing luôn đồng nhất.",
      ],
      personalizedNote: "Dựa trên lịch sử pace và thông số địa hình chính xác của cung đường mục tiêu.",
      personalizedChips: ["Lịch sử Pace / Race", "Cự ly & D+"],
      alwaysUpdated: "Dùng chung cơ sở dữ liệu đường chạy đã tuyển chọn với Pace Strategy, Gear Vault và Nutrition Lab.",
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
      tagline: "Chiến thuật pacing chi tiết theo từng checkpoint trên cung đường của bạn.",
      cardBlurb: "Độ dốc, độ cao, độ mỏi và thời tiết ngày race đều được tính vào từng split — không phải chỉ lấy quãng đường chia cho thời gian.",
      overview: "Pace Strategy mô phỏng sự thay đổi pace theo từng đoạn dựa trên địa hình thực tế của cung đường, từ đó tính ngược lại để bạn chạm mốc thời gian mục tiêu.",
      howItWorks: [
        "Độ dốc: áp dụng {{term:minetti_curve}}đường cong tiêu hao năng lượng Minetti{{/term}}, có giảm chấn khi đổ dốc và tối ưu sức bền đi bộ khi dốc gắt.",
        "{{term:altitude_penalty}}Ảnh hưởng độ cao{{/term}} áp dụng khi chạy trên 1.500m.",
        "{{term:durability}}Độ mỏi tích lũy{{/term}} bắt đầu tác động sau khoảng 15km tương đương đường bằng.",
        "Thời tiết thực tế: nắng nóng trên 15°C và trời mưa đều được tính vào hệ số giảm pace thực tế.",
        "{{term:split_bias}}Split bias{{/term}} — tùy chỉnh chiến thuật Negative Split (nửa sau nhanh hơn) hoặc Even Effort (giữ sức đều).",
      ],
      personalizedNote: "Dựa trên cân nặng, tracklog GPX và thời tiết thực tế ngày race.",
      personalizedChips: ["Cân nặng", "Tracklog GPX", "Thời tiết ngày race"],
      alwaysUpdated: "Dữ liệu thời tiết được lấy từ API dự báo thời gian thực mỗi khi bạn lên plan, không dùng nhiệt độ trung bình mùa.",
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
      tagline: "Gợi ý giày từ danh mục sản phẩm thực tế đã tuyển chọn — không suy đoán tùy tiện.",
      cardBlurb: "Chọn giày theo form chân, bề mặt địa hình, ngân sách và giải race mục tiêu từ danh mục giày trail & road đã tuyển chọn — mọi đề xuất đều truy được về sản phẩm thật.",
      overview: "Gear Finder không để AI tự bịa tên giày — mọi đề xuất đều {{term:catalog_grounded}}dựa trên danh mục sản phẩm thực tế{{/term}}.",
      howItWorks: [
        "Toàn bộ danh mục được nạp vào mỗi lần hỏi, nên không mẫu nào bị bỏ sót vì tìm kiếm gần đúng.",
        "Tuyển chọn từ các bài đánh giá chuyên môn của các hãng: Hoka, Salomon, Nike, adidas, Asics, On, Altra, Norda, Saucony, Brooks, New Balance...",
        "Bộ lọc chống sai lệch kiểm tra lại từng mẫu giày được gợi ý với danh mục sản phẩm thật.",
        "So khớp theo {{term:stack_height}}stack height{{/term}}, {{term:drop}}drop{{/term}}, {{term:carbon_plate}}carbon plate{{/term}} và {{term:lug_depth}}độ sâu gai đế (lug depth){{/term}}.",
      ],
      personalizedNote: "Dựa trên form chân, ngân sách và địa hình giải race của bạn.",
      personalizedChips: ["Form chân / Thương hiệu", "Ngân sách", "Địa hình race"],
      alwaysUpdated: "Danh mục sản phẩm được rà soát và cập nhật định kỳ bởi ban quản trị.",
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
      tagline: "Plan fueling chi tiết theo từng giờ, xây dựng từ sản phẩm thực tế.",
      cardBlurb: "Lượng carbs, sodium và dạng sản phẩm được tính theo cự ly race, thời tiết nắng nóng và khả năng dung nạp của đường ruột — từ danh mục dinh dưỡng thể thao đã tuyển chọn.",
      overview: "Nutrition Lab xây dựng chiến lược fueling cho race giống như chuyên gia dinh dưỡng thể thao: xuất phát từ mục tiêu của bạn, sau đó điền từng sản phẩm cụ thể theo từng giờ.",
      howItWorks: [
        "Mặc định 60g {{term:carb_oxidation}}carb oxidation{{/term}}/giờ và 500mg {{term:sodium_rate}}sodium{{/term}}/giờ, tự động tăng lên đến 1.000mg/giờ khi trời nóng.",
        "Dựa trên danh mục sản phẩm đầy đủ (gel, chews, bột pha nước, thức ăn thật) cho mỗi lần tính toán.",
        "Kết quả là danh sách hành động cụ thể theo từng giờ, không chỉ là bảng liệt kê sản phẩm.",
        "Chú trọng {{term:gut_training}}gut training{{/term}} — tập nạp dinh dưỡng ngay trong các bài tập, tuyệt đối không thử món mới vào ngày race.",
      ],
      personalizedNote: "Dựa trên cự ly race, thời tiết và plan tập đang chạy của bạn.",
      personalizedChips: ["Cự ly & D+", "Thời tiết", "Dạng sản phẩm"],
      alwaysUpdated: "Danh mục sản phẩm được cập nhật qua cùng quy trình tuyển chọn với Gear Finder.",
    },
  },
];
