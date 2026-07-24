export type GlossaryKey =
  | "aet"
  | "ant"
  | "zones"
  | "eighty_twenty"
  | "muscular_endurance"
  | "rag"
  | "grounded"
  | "ab_c_goals"
  | "base_flat_pace"
  | "rank_transfer"
  | "grade_adjusted_pace"
  | "minetti_curve"
  | "durability"
  | "split_bias"
  | "altitude_penalty"
  | "stack_height"
  | "drop"
  | "carbon_plate"
  | "lug_depth"
  | "catalog_grounded"
  | "carb_oxidation"
  | "sodium_rate"
  | "gut_training";

export type GlossaryDefinition = { en: string; vi: string };

export const GLOSSARY: Record<GlossaryKey, GlossaryDefinition> = {
  aet: {
    en: "The effort level where your body shifts from mostly burning fat to relying more on carbs. Training below this builds your aerobic engine without digging a fatigue hole.",
    vi: "Ngưỡng mà cơ thể chuyển từ đốt mỡ là chính sang dùng nhiều carb hơn. Tập dưới ngưỡng này giúp xây nền hiếu khí mà không đào hố mệt mỏi.",
  },
  ant: {
    en: "The effort where lactate starts piling up faster than your body clears it — roughly your \"hard but sustainable for about an hour\" pace.",
    vi: "Ngưỡng mà lactate tích tụ nhanh hơn tốc độ cơ thể đào thải — đại khái là pace \"khó nhưng ráng giữ được khoảng 1 tiếng\" của bạn.",
  },
  zones: {
    en: "Five effort bands anchored to your own AeT and AnT, not a generic percentage of max HR. Zone 1-2 = easy/aerobic, Zone 3 = tempo, Zone 4-5 = threshold/VO2max.",
    vi: "Năm mức cường độ neo theo AeT và AnT của chính bạn, không phải % chung của nhịp tim tối đa. Zone 1-2 là nhẹ/hiếu khí, Zone 3 là tempo, Zone 4-5 là ngưỡng/VO2max.",
  },
  eighty_twenty: {
    en: "The split elite endurance athletes train by — roughly 80% easy, 20% hard — because too much moderate-intensity work causes fatigue without building fitness.",
    vi: "Tỷ lệ mà dân sức bền đỉnh cao vẫn tập theo — khoảng 80% nhẹ, 20% nặng — vì tập nhiều ở mức trung bình chỉ làm mệt mà không lên phong độ bao nhiêu.",
  },
  muscular_endurance: {
    en: "Your muscles' ability to keep firing efficiently for hours — trained with hill sprints, step-ups, and downhill-specific work, distinct from raw strength or aerobic capacity.",
    vi: "Khả năng cơ bắp \"cày\" hiệu quả trong nhiều giờ liền — khác với sức mạnh hay thể lực hiếu khí thuần túy — luyện bằng hill sprints, step-ups và các bài chuyên cho xuống dốc.",
  },
  rag: {
    en: "Instead of answering purely from memory, the AI first looks up relevant facts from a trusted database, then writes its answer using those facts.",
    vi: "Thay vì trả lời hoàn toàn theo trí nhớ, AI tra dữ kiện từ một kho dữ liệu đáng tin trước, rồi mới dựa vào đó viết câu trả lời — giống việc tra tài liệu trước khi trả lời thay vì đoán đại.",
  },
  grounded: {
    en: "A response backed by a specific, retrievable source in the knowledge base, rather than the model's general training data.",
    vi: "Câu trả lời bám vào một nguồn cụ thể, tra được trong knowledge base, chứ không phải \"nói theo cảm tính\" từ dữ liệu huấn luyện chung của model.",
  },
  ab_c_goals: {
    en: "Three finish-time targets for one race — A (ambitious, everything goes right), B (realistic/expected), C (safe, banks margin for a bad day).",
    vi: "Ba mục tiêu thời gian cho một giải — A (ambitious, mọi thứ thuận lợi), B (realistic, mức kỳ vọng bình thường), C (safe, chừa margin cho ngày xui) — để dù hôm đó ra sao bạn cũng có sẵn kế hoạch.",
  },
  base_flat_pace: {
    en: "Your pace on flat, sea-level ground with no accumulated fatigue — the \"pure fitness\" number every other prediction is built from.",
    vi: "Pace của bạn trên đường bằng, ngang mực nước biển, chưa cộng dồn mệt mỏi — con số \"phong độ gốc\" mà mọi dự đoán khác đều tính ra từ đây.",
  },
  rank_transfer: {
    en: "Estimating your finish time on a new race by comparing it to how you'd have ranked in a past one — the same logic sites like UltraSignup use.",
    vi: "Ước tính thời gian về đích ở giải mới bằng cách so với thứ hạng bạn từng đạt ở một giải khác — đúng logic mà các trang như UltraSignup hay dùng.",
  },
  grade_adjusted_pace: {
    en: "Your pace converted to its flat-ground equivalent, accounting for how much harder climbing (or how much descending helps) actually costs metabolically.",
    vi: "Pace của bạn quy đổi về tương đương trên đường bằng, tính luôn chi phí thật của việc leo dốc (hoặc lợi thế khi xuống dốc).",
  },
  minetti_curve: {
    en: "A published physiology model (Minetti et al., 2002) of the metabolic energy cost of running at different uphill/downhill grades.",
    vi: "Mô hình sinh lý học đã công bố (Minetti và cộng sự, 2002) về năng lượng tiêu tốn khi chạy ở các độ dốc lên/xuống khác nhau — lý do vì sao dốc 20% mệt hơn dốc 10% không chỉ gấp đôi mà hơn nhiều.",
  },
  durability: {
    en: "How much your pace naturally slows as accumulated distance wears on your legs, independent of terrain — modeled starting after roughly 15km of flat-equivalent running.",
    vi: "Mức pace tự nhiên chậm lại khi quãng đường tích lũy làm mỏi chân, không liên quan tới địa hình — mô hình này tính từ khoảng 15km quy đổi tương đương đường bằng trở đi.",
  },
  split_bias: {
    en: "Deliberately running the second half faster (or holding even effort) rather than starting fast and fading.",
    vi: "Chủ động chạy nửa sau nhanh hơn nửa đầu (hoặc giữ effort đều), thay vì xuất phát hết ga rồi ráng bám trụ — đã được chứng minh hiệu quả hơn ở phần lớn cự ly sức bền.",
  },
  altitude_penalty: {
    en: "The pace cost of running at elevation, where thinner air reduces oxygen delivery — applied above roughly 1,500m in this model.",
    vi: "Phần pace bị chậm đi khi chạy ở độ cao, do không khí loãng làm giảm oxy cung cấp cho cơ thể — mô hình này áp dụng từ khoảng 1.500m trở lên.",
  },
  stack_height: {
    en: "The thickness of cushioning between your foot and the ground — more stack generally means more shock absorption but less ground feel.",
    vi: "Độ dày lớp đệm giữa bàn chân và mặt đất — stack càng cao thường càng êm, nhưng cảm giác mặt đường (ground feel) càng ít.",
  },
  drop: {
    en: "The height difference between a shoe's heel and forefoot — lower drop encourages a more midfoot/forefoot strike, higher drop favors heel strikers.",
    vi: "Chênh lệch độ cao giữa gót và mũi giày — drop thấp hợp người tiếp đất giữa/mũi bàn chân, drop cao hợp người tiếp đất bằng gót.",
  },
  carbon_plate: {
    en: "A rigid plate embedded in the midsole that acts like a lever, improving running economy at faster paces.",
    vi: "Tấm cứng gắn trong đế giữa, hoạt động như đòn bẩy giúp chạy hiệu quả hơn ở pace nhanh — hữu ích nhất cho race pace, ít cần thiết cho chạy nhẹ trên trail.",
  },
  lug_depth: {
    en: "How deep a trail shoe's outsole tread is — deeper lugs grip better in mud/loose terrain, shallower lugs suit hardpack and roads.",
    vi: "Độ sâu gai đế của giày trail — gai sâu bám tốt hơn trên bùn, địa hình lỏng lẻo; gai nông hợp đường cứng và đường nhựa.",
  },
  catalog_grounded: {
    en: "Recommended only from a verified, curated database of real products, not generated freely by the AI.",
    vi: "Chỉ gợi ý từ một database sản phẩm thật, đã được xác minh — không phải AI tự nghĩ ra.",
  },
  carb_oxidation: {
    en: "How many grams of carbohydrate your gut and muscles can actually absorb and burn per hour during exercise — roughly 60-90g/hour is the trainable range for most athletes.",
    vi: "Số gram carb mà dạ dày và cơ bắp bạn thực sự hấp thụ và đốt được mỗi giờ khi vận động — mức trần mà kế hoạch dinh dưỡng dựa vào (khoảng 60-90g/giờ là mức đa số vận động viên luyện tập được).",
  },
  sodium_rate: {
    en: "How much sodium you need to replace per hour based on sweat losses — too little risks cramping, too much can cause GI distress.",
    vi: "Lượng sodium cần bù mỗi giờ dựa trên lượng mất qua mồ hôi — bù thiếu dễ chuột rút ở các nỗ lực dài và nóng, bù thừa dễ rối loạn tiêu hóa.",
  },
  gut_training: {
    en: "Practicing your actual race-day fueling plan during training runs, so your digestive system adapts to processing calories under exercise stress.",
    vi: "Tập cho dạ dày quen với đúng kế hoạch dinh dưỡng ngày đua ngay trong các buổi chạy tập, để hệ tiêu hóa thích nghi dần với việc xử lý calo khi đang vận động — yếu tố quyết định lớn nhất để tránh sự cố tiêu hóa ngày thi đấu.",
  },
};
