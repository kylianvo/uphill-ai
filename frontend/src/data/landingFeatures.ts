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
        "5-zone heart rate model anchored on your own {{term:aet}}AeT{{/term}} and {{term:ant}}AnT{{/term}}, not age-predicted max HR.",
        "Automatic {{term:eighty_twenty}}80/20{{/term}} audit keeps every week at least ~80% easy.",
        "{{term:muscular_endurance}}Muscular endurance{{/term}} blocks — hill sprints, weighted step-ups — for legs that don't give out on descents.",
        "Treadmill mode converts any session into an exact grade-adjusted speed/incline pair.",
      ],
      personalizedNote: "Built from your thresholds, injury history, and active training load — see Your Profile below.",
      personalizedChips: ["AeT / AnT", "Injury history", "Goal race terrain"],
      alwaysUpdated: "The coaching knowledge base is periodically redistilled from primary sources, so advice isn't frozen to one training era.",
    },
    vi: {
      tagline: "Giáo án tập luyện của bạn, xây dựng trên cuốn sách mà những người giỏi nhất môn thể thao này đã viết.",
      cardBlurb: "Giáo án tập luyện hàng tuần bài bản dựa trên Training for the Uphill Athlete — điều chỉnh theo ngưỡng thể lực, tiền sử chấn thương và giải đấu mục tiêu của bạn.",
      overview: "Coach Uphill xây dựng tuần tập dựa trên triết lý aerobic-first của Training for the Uphill Athlete — đồng tác giả bởi Kilian Jornet, Scott Johnston và Steve House — mỗi buổi tập được tạo dựa trên chỉ số thật của bạn, không phải mẫu chung.",
      howItWorks: [
        "Mô hình 5 vùng nhịp tim neo theo {{term:aet}}AeT{{/term}} và {{term:ant}}AnT{{/term}} của chính bạn, không chỉ nhịp tim tối đa theo tuổi.",
        "Tự động kiểm tra nguyên tắc {{term:eighty_twenty}}80/20{{/term}} mỗi tuần.",
        "Bài tập {{term:muscular_endurance}}sức bền cơ bắp{{/term}} — hill sprints, weighted step-ups — cho đôi chân không \"hết pin\" khi xuống dốc.",
        "Chế độ treadmill chuyển đổi buổi tập ngoài trời thành cặp tốc độ/độ dốc chính xác.",
      ],
      personalizedNote: "Xây dựng từ ngưỡng thể lực, tiền sử chấn thương và khối lượng tập hiện tại — xem Hồ sơ của bạn bên dưới.",
      personalizedChips: ["AeT / AnT", "Tiền sử chấn thương", "Địa hình giải mục tiêu"],
      alwaysUpdated: "Knowledge base huấn luyện được \"chưng cất\" lại định kỳ từ nguồn gốc chính thống, nên lời khuyên không bị đóng băng.",
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
      personalizedNote: "Uses your active plan and running profile — see Your Profile below.",
      personalizedChips: ["Active plan", "Goals & injury notes", "English / Vietnamese"],
      alwaysUpdated: "Shares the same knowledge base as the rest of the app — new gear, science, and race data flow into chat automatically.",
    },
    vi: {
      tagline: "Hỏi bất cứ điều gì. Nhận câu trả lời dựa trên khoa học tập luyện thật.",
      cardBlurb: "Pacing, dinh dưỡng, \"có nên chạy tiếp khi đầu gối hơi nhói không\" — Coach Uphill trả lời dựa trên knowledge base được tuyển chọn, và nói \"tôi không chắc\" thay vì đoán bừa.",
      overview: "Coach Uphill chạy trên Gemini 2.5 Flash, nhưng mọi câu trả lời đều được {{term:rag}}RAG{{/term}} {{term:grounded}}grounded{{/term}} dựa trên knowledge base được tuyển chọn trước khi trả lời.",
      howItWorks: [
        "Câu hỏi của bạn được đối chiếu với triết lý tập luyện, khoa học dinh dưỡng và dữ liệu gear trước khi model trả lời.",
        "Nguyên tắc huấn luyện cài sẵn trong system prompt: aerobic-first cho trail, 80/20 cho road, công thức bù nước theo sweat rate, tư vấn giày theo cơ sinh học.",
        "Từ chối bịa đặt — nếu knowledge base không có thông tin, chatbot nói rõ thay vì tự nghĩ ra chi tiết.",
        "Đọc giáo án đang hoạt động — hỏi \"hôm nay tập gì\" và nó tham chiếu lịch tập thật.",
      ],
      personalizedNote: "Dùng giáo án đang hoạt động và hồ sơ chạy bộ của bạn — xem Hồ sơ của bạn bên dưới.",
      personalizedChips: ["Giáo án đang hoạt động", "Mục tiêu & chấn thương", "Song ngữ Anh / Việt"],
      alwaysUpdated: "Dùng chung knowledge base với các tính năng khác — dữ liệu mới tự động phản ánh vào câu trả lời chat.",
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
      personalizedNote: "Uses your pace history and the target course's exact profile — see Your Profile below.",
      personalizedChips: ["Pace / race history", "Course distance & elevation"],
      alwaysUpdated: "Pulls from the same curated race-course database used by Pace Strategy, Gear Finder, and Nutrition.",
    },
    vi: {
      tagline: "Biến thể lực hiện tại — hoặc một giải đã chạy — thành mục tiêu về đích thực tế.",
      cardBlurb: "Dự đoán thời gian về đích trên bất kỳ cung đường nào từ kết quả giải trước hoặc pace hiện tại, rồi chia thành 3 mục tiêu Ambitious, Realistic và Safe.",
      overview: "Goal Determiner chạy ngược lại vật lý pacing của Pace Strategy: nhập pace hoặc kết quả một giải đã chạy, hệ thống dự đoán thời gian về đích trên cung đường mới.",
      howItWorks: [
        "Hai cách nhập: {{term:base_flat_pace}}pace nền trên đường bằng{{/term}} trực tiếp, hoặc thời gian về đích một giải đã biết cung đường.",
        "Điều chỉnh theo thời gian đến giải: giả định cải thiện ~0.25%/tuần, giới hạn tối đa 5%.",
        "Mục tiêu {{term:ab_c_goals}}A/B/C{{/term}} cố ý bất đối xứng — Ambitious nhanh hơn ~5%, Safe chậm hơn ~8%.",
        "{{term:rank_transfer}}Rank transfer{{/term}} kiểm tra chéo mục tiêu với người về đích trước đó, khi có dữ liệu.",
        "Dùng chung engine với Pace Strategy, có chủ đích — mục tiêu và kế hoạch pacing không bao giờ mâu thuẫn.",
      ],
      personalizedNote: "Dùng lịch sử pace/giải đấu của bạn và hồ sơ chính xác cung đường mục tiêu — xem Hồ sơ của bạn bên dưới.",
      personalizedChips: ["Pace / lịch sử giải đấu", "Khoảng cách & độ cao cung đường"],
      alwaysUpdated: "Lấy dữ liệu từ cùng database cung đường được tuyển chọn mà Pace Strategy, Gear Finder và Nutrition đang dùng.",
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
      personalizedNote: "Uses your body weight, GPX route, and live race-day weather — see Your Profile below.",
      personalizedChips: ["Body weight", "GPX route", "Live weather"],
      alwaysUpdated: "Weather comes from a live forecast API pulled fresh for each plan, not a seasonal average.",
    },
    vi: {
      tagline: "Pacing chi tiết theo từng checkpoint cho đúng cung đường của bạn.",
      cardBlurb: "Độ dốc, độ cao, mệt mỏi tích lũy và thời tiết thật ngày thi đấu đều được tính vào — không chỉ quãng đường chia cho thời gian mục tiêu.",
      overview: "Pace Strategy mô phỏng cách pace của bạn thay đổi theo từng đoạn dựa trên yêu cầu thể chất thật của cung đường, rồi giải ngược để đạt đúng thời gian về đích.",
      howItWorks: [
        "Độ dốc: dùng {{term:minetti_curve}}đường cong Minetti{{/term}}, có giảm chấn cho đoạn xuống dốc và giới hạn hiệu suất đi bộ cho dốc gắt.",
        "{{term:altitude_penalty}}Phạt độ cao{{/term}} áp dụng trên khoảng 1.500m.",
        "{{term:durability}}Mệt mỏi tích lũy{{/term}} bắt đầu sau khoảng 15km quy đổi tương đương đường bằng.",
        "Thời tiết thật: nhiệt độ trên 15°C và mưa đều gây chậm pace thực sự.",
        "{{term:split_bias}}Split bias{{/term}} — chọn negative split hoặc pace đều.",
      ],
      personalizedNote: "Dùng cân nặng, file GPX cung đường và thời tiết thật ngày thi đấu của bạn — xem Hồ sơ của bạn bên dưới.",
      personalizedChips: ["Cân nặng", "File GPX", "Thời tiết thật"],
      alwaysUpdated: "Thời tiết lấy từ API dự báo thời gian thực cho mỗi lần tạo kế hoạch, không phải số liệu trung bình.",
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
      personalizedNote: "Uses your fit preferences, budget, and matched race terrain — see Your Profile below.",
      personalizedChips: ["Fit / brand preference", "Budget", "Race terrain"],
      alwaysUpdated: "The catalog is refreshed through a periodic, admin-curated distillation pass.",
    },
    vi: {
      tagline: "Gợi ý giày từ một catalog thật, được tuyển chọn kỹ — không đoán bừa.",
      cardBlurb: "Khớp với bàn chân, địa hình, ngân sách và giải mục tiêu của bạn từ catalog giày trail/road hiện hành — mỗi gợi ý đều truy được về sản phẩm thật.",
      overview: "Gear Finder không để AI tự \"bịa\" tên giày — mọi gợi ý đều {{term:catalog_grounded}}truy ngược được về catalog thật{{/term}}.",
      howItWorks: [
        "Toàn bộ catalog đã \"chưng cất\" được đưa vào mỗi truy vấn, nên không có rủi ro bỏ sót đôi giày phù hợp.",
        "Chỉ tuyển chọn từ các bài review uy tín cho một danh sách thương hiệu cố định — Hoka, Salomon, Nike, adidas, Asics, On, Altra, Norda, Saucony, Brooks, New Balance và nhiều hơn.",
        "Cơ chế chống bịa đối chiếu lại mọi gợi ý với catalog thật sau khi tạo ra.",
        "Khớp theo {{term:stack_height}}stack height{{/term}}, {{term:drop}}drop{{/term}}, {{term:carbon_plate}}carbon plate{{/term}} và {{term:lug_depth}}lug depth{{/term}}.",
      ],
      personalizedNote: "Dùng sở thích form giày, ngân sách và địa hình giải đã match của bạn — xem Hồ sơ của bạn bên dưới.",
      personalizedChips: ["Form giày / thương hiệu", "Ngân sách", "Địa hình giải"],
      alwaysUpdated: "Catalog được làm mới qua quy trình \"chưng cất\" định kỳ do admin kiểm soát.",
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
      personalizedNote: "Uses your race distance, weather, and active plan context — see Your Profile below.",
      personalizedChips: ["Race distance & elevation", "Weather", "Format preference"],
      alwaysUpdated: "Product catalog refreshed through the same curated distillation pipeline as Gear Finder.",
    },
    vi: {
      tagline: "Kế hoạch dinh dưỡng chi tiết theo từng giờ, từ sản phẩm thật.",
      cardBlurb: "Carb, sodium và định dạng khớp theo cự ly giải, thời tiết nóng và khả năng dung nạp của dạ dày bạn — dùng catalog các sản phẩm dinh dưỡng phổ biến.",
      overview: "Nutrition Lab xây dựng chiến lược dinh dưỡng như một chuyên gia dinh dưỡng thể thao: bắt đầu từ mục tiêu của bạn, rồi lấp đầy bằng sản phẩm thật, theo từng giờ.",
      howItWorks: [
        "Mặc định 60g {{term:carb_oxidation}}carb oxidation{{/term}}/giờ và 500mg {{term:sodium_rate}}sodium{{/term}}/giờ, tăng sodium lên tới 1.000mg/giờ khi trời nóng.",
        "Grounding trên toàn bộ catalog — thấy toàn bộ catalog sản phẩm đã \"chưng cất\" (gel, chew, nước uống, thức ăn thật) cho mỗi yêu cầu.",
        "Kết quả là danh sách hành động có cấu trúc theo từng giờ, không chỉ là danh sách sản phẩm.",
        "Có tính đến {{term:gut_training}}gut training{{/term}} — luyện tập khối lượng nạp ngày thi đấu trong tập luyện, không thử mới vào ngày đua.",
      ],
      personalizedNote: "Dùng cự ly giải, thời tiết dự kiến và bối cảnh giáo án đang hoạt động của bạn — xem Hồ sơ của bạn bên dưới.",
      personalizedChips: ["Cự ly & độ cao giải", "Thời tiết", "Định dạng ưu tiên"],
      alwaysUpdated: "Catalog sản phẩm được làm mới qua cùng pipeline \"chưng cất\" như Gear Finder.",
    },
  },
];
