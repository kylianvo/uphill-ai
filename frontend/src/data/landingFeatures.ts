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
      tagline: "Giáo án của bạn, xây trên cuốn sách mà những người giỏi nhất môn này viết ra.",
      cardBlurb: "Lịch tập hàng tuần bài bản, dựa trên Training for the Uphill Athlete — cuốn sách của Kilian Jornet, Scott Johnston và Steve House — điều chỉnh theo đúng ngưỡng thể lực, tiền sử chấn thương và giải mục tiêu của bạn.",
      overview: "Coach Uphill xây tuần tập quanh triết lý \"hiếu khí là gốc\" của Training for the Uphill Athlete — cuốn sách viết bởi huyền thoại ultra-runner Kilian Jornet, HLV leo núi kỳ cựu Scott Johnston, và nhà leo núi Steve House. Không phải một mẫu giáo án dùng chung cho mọi người — mỗi buổi tập được sinh ra từ chỉ số thật của chính bạn.",
      howItWorks: [
        "{{term:zones}}5 vùng nhịp tim{{/term}} neo theo ngưỡng {{term:aet}}AeT{{/term}} và {{term:ant}}AnT{{/term}} của riêng bạn, không phải công thức tính theo tuổi chung chung.",
        "Tự động canh nguyên tắc {{term:eighty_twenty}}80/20{{/term}} — hệ thống rà lại mỗi tuần để đảm bảo ít nhất ~80% khối lượng ở cường độ nhẹ.",
        "Bài tập {{term:muscular_endurance}}sức bền cơ bắp{{/term}} — hill sprints, weighted step-ups — cách Johnston giải quyết chuyện chân \"hết pin\" ở đoạn xuống dốc cuối giải.",
        "Chế độ treadmill quy đổi buổi chạy ngoài trời thành cặp tốc độ/độ dốc chính xác, cho ngày mưa gió hoặc không tiện ra đường.",
      ],
      personalizedNote: "Dựa trên ngưỡng thể lực, tiền sử chấn thương và khối lượng tập hiện tại của bạn.",
      personalizedChips: ["AeT / AnT", "Tiền sử chấn thương", "Địa hình giải mục tiêu"],
      alwaysUpdated: "Knowledge base huấn luyện được chắt lọc từ nguồn gốc rõ ràng và làm mới định kỳ qua một quy trình quản trị riêng — lời khuyên không bị đóng khung theo một giai đoạn tập luyện cũ.",
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
      tagline: "Hỏi gì cũng được. Trả lời dựa trên khoa học tập luyện thật, không đoán mò.",
      cardBlurb: "Hỏi về pacing, dinh dưỡng, hay \"đầu gối hơi nhói vậy có nên chạy tiếp không\" — Coach Uphill trả lời dựa trên knowledge base đã được chọn lọc, và sẵn sàng nói \"chưa chắc\" thay vì bịa ra câu trả lời.",
      overview: "Coach Uphill chạy trên Gemini 2.5 Flash, nhưng không trả lời kiểu \"nghĩ gì nói nấy\" — mọi câu trả lời đều được {{term:rag}}RAG{{/term}}-{{term:grounded}}grounded{{/term}}, dựa trên knowledge base đã chọn lọc trước khi trả lời.",
      howItWorks: [
        "Câu hỏi của bạn được đối chiếu với kho kiến thức về triết lý tập luyện, khoa học dinh dưỡng và dữ liệu gear trước khi model trả lời.",
        "Nguyên tắc huấn luyện được cài sẵn: triết lý aerobic-first của Johnston cho trail, nguyên tắc 80/20 cho road, công thức bù nước theo sweat rate, và tư vấn giày dựa trên cơ sinh học bàn chân.",
        "Không bịa khi không chắc — nếu knowledge base không có thông tin, chatbot nói thẳng và quay về nguyên tắc huấn luyện chung thay vì tự nghĩ ra chi tiết.",
        "Đọc được giáo án bạn đang chạy — hỏi \"hôm nay tập gì\" là nó tham chiếu đúng lịch tập thật của bạn.",
      ],
      personalizedNote: "Dùng giáo án đang chạy và hồ sơ chạy bộ của bạn.",
      personalizedChips: ["Giáo án đang hoạt động", "Mục tiêu & chấn thương", "Song ngữ Anh / Việt"],
      alwaysUpdated: "Dùng chung knowledge base với các tính năng khác — dữ liệu mới thêm vào pipeline sẽ tự động lên trong câu trả lời chat.",
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
      tagline: "Biến phong độ hiện tại — hoặc một giải đã chạy — thành mục tiêu về đích thực tế.",
      cardBlurb: "Dự đoán thời gian về đích trên bất kỳ cung đường nào từ kết quả một giải trước hoặc pace hiện tại, rồi chia thành 3 mục tiêu: Ambitious, Realistic, Safe.",
      overview: "Goal Determiner chạy ngược đúng công thức vật lý pacing của Pace Strategy: đưa vào pace nền trên đường bằng hoặc kết quả một giải đã chạy, hệ thống dự đoán thời gian về đích ở cung đường mới — rồi chia thành 3 mục tiêu cụ thể cho ngày đua.",
      howItWorks: [
        "Hai cách nhập phong độ: {{term:base_flat_pace}}pace nền trên đường bằng{{/term}} trực tiếp, hoặc thời gian về đích một giải đã biết cung đường.",
        "Điều chỉnh theo thời gian còn lại đến giải: giả định cải thiện khoảng 0.25%/tuần, tối đa 5%.",
        "Mục tiêu {{term:ab_c_goals}}A/B/C{{/term}} lệch có chủ đích — Ambitious nhanh hơn dự đoán ~5%, Safe chậm hơn ~8%.",
        "{{term:rank_transfer}}Rank transfer{{/term}} so thứ hạng dự đoán của bạn với runner về đích các năm trước, khi có dữ liệu.",
        "Dùng chung engine với Pace Strategy, có chủ đích — mục tiêu và kế hoạch pacing không bao giờ \"đá\" nhau.",
      ],
      personalizedNote: "Dựa trên pace hoặc lịch sử giải đấu của bạn và hồ sơ chính xác cung đường mục tiêu.",
      personalizedChips: ["Pace / lịch sử giải đấu", "Khoảng cách & độ cao cung đường"],
      alwaysUpdated: "Lấy dữ liệu từ cùng database cung đường mà Pace Strategy, Gear Finder và Nutrition đang dùng.",
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
      tagline: "Pacing từng checkpoint, đúng theo cung đường của bạn.",
      cardBlurb: "Độ dốc, độ cao, mệt mỏi tích lũy, kể cả thời tiết thật ngày đua — tất cả đều được tính vào, không chỉ đơn giản lấy quãng đường chia cho thời gian mục tiêu.",
      overview: "Pace Strategy mô phỏng cách pace của bạn thực sự thay đổi theo từng đoạn đường, dựa trên yêu cầu thể chất thật của cung đường đó — rồi giải ngược lại để ra đúng thời gian về đích bạn muốn.",
      howItWorks: [
        "Độ dốc: dùng {{term:minetti_curve}}đường cong Minetti{{/term}}, có giảm chấn cho đoạn xuống dốc và chặn trần cho dốc quá gắt.",
        "{{term:altitude_penalty}}Phạt độ cao{{/term}} áp dụng khi vượt 1.500m, nếu cung đường có dữ liệu.",
        "{{term:durability}}Mệt mỏi tích lũy{{/term}} bắt đầu sau khoảng 15km quy đổi tương đương đường bằng.",
        "Thời tiết thật: nhiệt độ trên 15°C và mưa đều làm chậm pace thật.",
        "{{term:split_bias}}Split bias{{/term}} — chọn negative split hoặc giữ effort đều.",
      ],
      personalizedNote: "Dựa trên cân nặng, file GPX cung đường và thời tiết thật ngày thi đấu của bạn.",
      personalizedChips: ["Cân nặng", "File GPX", "Thời tiết thật"],
      alwaysUpdated: "Thời tiết lấy trực tiếp từ API dự báo thời gian thực mỗi lần bạn tạo kế hoạch, không phải số trung bình cố định theo mùa.",
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
      tagline: "Gợi ý giày từ catalog thật, chọn lọc kỹ — không đoán bừa.",
      cardBlurb: "Khớp với bàn chân, địa hình, ngân sách và giải mục tiêu của bạn, dựa trên catalog giày trail/road hiện hành đã được chọn lọc — mỗi gợi ý đều truy ra được sản phẩm thật.",
      overview: "Gear Finder không để AI tự bịa tên giày — mọi gợi ý đều {{term:catalog_grounded}}lần ra được một sản phẩm thật{{/term}} trong catalog đầy đủ, đã chọn lọc kỹ.",
      howItWorks: [
        "Đưa nguyên catalog vào ngữ cảnh AI cho mỗi lần hỏi, không chỉ tìm vài kết quả gần giống nhất — tránh bỏ sót đôi giày hợp nhất.",
        "Chỉ lấy từ các bài review uy tín, cho một nhóm thương hiệu cố định — Hoka, Salomon, Nike, adidas, Asics, On, Altra, Norda, Saucony, Brooks, New Balance và vài hãng khác.",
        "Cơ chế chống bịa: sau khi model gợi ý xong, hệ thống đối chiếu lại với catalog thật; tên nào không có trong catalog sẽ bị gắn cờ.",
        "Khớp theo {{term:stack_height}}stack height{{/term}}, {{term:drop}}drop{{/term}}, {{term:carbon_plate}}carbon plate{{/term}} và {{term:lug_depth}}lug depth{{/term}}.",
      ],
      personalizedNote: "Dựa trên sở thích form giày, ngân sách và địa hình giải bạn đã chọn.",
      personalizedChips: ["Form giày / thương hiệu", "Ngân sách", "Địa hình giải"],
      alwaysUpdated: "Catalog được làm mới định kỳ qua quy trình chọn lọc do admin kiểm soát.",
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
      tagline: "Kế hoạch dinh dưỡng theo từng giờ, từ sản phẩm thật.",
      cardBlurb: "Carb, sodium và định dạng (gel, chew, thức ăn thật) khớp theo cự ly giải, thời tiết nóng và mức dạ dày bạn chịu được — dựa trên catalog các sản phẩm dinh dưỡng phổ biến.",
      overview: "Nutrition Lab xây chiến lược dinh dưỡng đúng như cách một chuyên gia dinh dưỡng thể thao làm: bắt đầu từ mục tiêu carb và sodium của bạn, rồi lấp đầy bằng sản phẩm thật trong catalog, chia theo từng giờ.",
      howItWorks: [
        "Mặc định 60g {{term:carb_oxidation}}carb oxidation{{/term}}/giờ và 500mg {{term:sodium_rate}}sodium{{/term}}/giờ, tự tăng sodium lên tới 1.000mg/giờ khi trời nóng.",
        "Đưa nguyên catalog vào, giống Gear Finder — AI thấy toàn bộ sản phẩm (gel, chew, nước uống, thức ăn thật) cho mỗi lần hỏi.",
        "Ra kế hoạch theo từng giờ — một danh sách cụ thể: ăn/uống gì, lúc nào — không chỉ liệt kê sản phẩm chung chung.",
        "Có tính {{term:gut_training}}gut training{{/term}} — tập cho dạ dày quen dần với khối lượng nạp ngày đua, không thử mới vào ngày thi đấu.",
      ],
      personalizedNote: "Dựa trên cự ly giải, thời tiết dự kiến và giáo án bạn đang chạy.",
      personalizedChips: ["Cự ly & độ cao giải", "Thời tiết", "Định dạng ưu tiên"],
      alwaysUpdated: "Catalog sản phẩm được làm mới qua cùng quy trình chọn lọc như Gear Finder.",
    },
  },
];
