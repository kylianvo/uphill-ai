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
    vi: "Mức cường độ mà cơ thể chuyển từ đốt mỡ là chủ yếu sang dựa nhiều hơn vào carb. Tập dưới ngưỡng này giúp xây \"động cơ hiếu khí\" mà không gây mệt mỏi tích lũy.",
  },
  ant: {
    en: "The effort where lactate starts piling up faster than your body clears it — roughly your \"hard but sustainable for about an hour\" pace.",
    vi: "Mức cường độ mà lactate tích tụ nhanh hơn tốc độ cơ thể đào thải — gần với pace \"khó nhưng có thể duy trì khoảng 1 giờ\" của bạn.",
  },
  zones: {
    en: "Five effort bands anchored to your own AeT and AnT, not a generic percentage of max HR. Zone 1-2 = easy/aerobic, Zone 3 = tempo, Zone 4-5 = threshold/VO2max.",
    vi: "Năm dải cường độ neo theo AeT và AnT của chính bạn, không phải phần trăm chung của nhịp tim tối đa. Zone 1-2 = nhẹ/hiếu khí, Zone 3 = tempo, Zone 4-5 = ngưỡng/VO2max.",
  },
  eighty_twenty: {
    en: "The split elite endurance athletes train by — roughly 80% easy, 20% hard — because too much moderate-intensity work causes fatigue without building fitness.",
    vi: "Tỷ lệ mà các vận động viên sức bền hàng đầu áp dụng — khoảng 80% tập nhẹ, 20% tập nặng — vì tập quá nhiều ở cường độ trung bình gây mệt mỏi mà không cải thiện thể lực tương xứng.",
  },
  muscular_endurance: {
    en: "Your muscles' ability to keep firing efficiently for hours — trained with hill sprints, step-ups, and downhill-specific work, distinct from raw strength or aerobic capacity.",
    vi: "Khả năng cơ bắp duy trì hoạt động hiệu quả trong nhiều giờ — rèn luyện qua hill sprints, step-ups và bài tập chuyên biệt cho xuống dốc, khác với sức mạnh thuần túy hay thể lực hiếu khí.",
  },
  rag: {
    en: "Instead of answering purely from memory, the AI first looks up relevant facts from a trusted database, then writes its answer using those facts.",
    vi: "Thay vì trả lời hoàn toàn từ trí nhớ, AI tra cứu dữ kiện liên quan từ một cơ sở dữ liệu đáng tin cậy trước, rồi mới viết câu trả lời dựa trên đó.",
  },
  grounded: {
    en: "A response backed by a specific, retrievable source in the knowledge base, rather than the model's general training data.",
    vi: "Phản hồi dựa trên một nguồn cụ thể, có thể truy xuất trong knowledge base, thay vì dữ liệu huấn luyện chung của model.",
  },
  ab_c_goals: {
    en: "Three finish-time targets for one race — A (ambitious, everything goes right), B (realistic/expected), C (safe, banks margin for a bad day).",
    vi: "Ba mục tiêu thời gian về đích cho một giải — A (ambitious, mọi thứ thuận lợi), B (realistic), C (safe, dư margin cho ngày xui).",
  },
  base_flat_pace: {
    en: "Your pace on flat, sea-level ground with no accumulated fatigue — the \"pure fitness\" number every other prediction is built from.",
    vi: "Pace của bạn trên đường bằng, ngang mực nước biển, chưa tích lũy mệt mỏi — con số \"thể lực thuần\" mà mọi dự đoán khác được xây dựng từ đó.",
  },
  rank_transfer: {
    en: "Estimating your finish time on a new race by comparing it to how you'd have ranked in a past one — the same logic sites like UltraSignup use.",
    vi: "Ước tính thời gian về đích ở một giải mới bằng cách so sánh với thứ hạng bạn có thể đạt ở một giải đã chạy.",
  },
  grade_adjusted_pace: {
    en: "Your pace converted to its flat-ground equivalent, accounting for how much harder climbing (or how much descending helps) actually costs metabolically.",
    vi: "Pace của bạn được quy đổi về tương đương trên đường bằng, tính đến chi phí chuyển hóa thực tế của việc leo dốc (hoặc lợi thế của việc xuống dốc).",
  },
  minetti_curve: {
    en: "A published physiology model (Minetti et al., 2002) of the metabolic energy cost of running at different uphill/downhill grades.",
    vi: "Mô hình sinh lý học đã công bố (Minetti và cộng sự, 2002) về chi phí năng lượng chuyển hóa khi chạy ở các độ dốc lên/xuống khác nhau.",
  },
  durability: {
    en: "How much your pace naturally slows as accumulated distance wears on your legs, independent of terrain — modeled starting after roughly 15km of flat-equivalent running.",
    vi: "Mức độ pace tự nhiên chậm lại khi quãng đường tích lũy làm mỏi đôi chân, độc lập với địa hình — bắt đầu tính từ khoảng 15km quy đổi tương đương đường bằng.",
  },
  split_bias: {
    en: "Deliberately running the second half faster (or holding even effort) rather than starting fast and fading.",
    vi: "Chiến thuật chủ động chạy nửa sau nhanh hơn (hoặc giữ effort đều) thay vì xuất phát nhanh rồi cố bám trụ.",
  },
  altitude_penalty: {
    en: "The pace cost of running at elevation, where thinner air reduces oxygen delivery — applied above roughly 1,500m in this model.",
    vi: "Chi phí pace khi chạy ở độ cao, nơi không khí loãng làm giảm khả năng cung cấp oxy — áp dụng trên khoảng 1.500m.",
  },
  stack_height: {
    en: "The thickness of cushioning between your foot and the ground — more stack generally means more shock absorption but less ground feel.",
    vi: "Độ dày lớp đệm giữa bàn chân và mặt đất — stack càng cao thường càng êm nhưng cảm nhận mặt đường càng ít.",
  },
  drop: {
    en: "The height difference between a shoe's heel and forefoot — lower drop encourages a more midfoot/forefoot strike, higher drop favors heel strikers.",
    vi: "Chênh lệch độ cao giữa gót và mũi giày — drop thấp khuyến khích tiếp đất bằng giữa/mũi bàn chân, drop cao phù hợp người tiếp đất bằng gót.",
  },
  carbon_plate: {
    en: "A rigid plate embedded in the midsole that acts like a lever, improving running economy at faster paces.",
    vi: "Tấm cứng gắn trong đế giữa, hoạt động như một đòn bẩy giúp cải thiện hiệu suất chạy ở pace nhanh.",
  },
  lug_depth: {
    en: "How deep a trail shoe's outsole tread is — deeper lugs grip better in mud/loose terrain, shallower lugs suit hardpack and roads.",
    vi: "Độ sâu của gai đế giày trail — gai sâu bám tốt hơn trên bùn/địa hình lỏng lẻo, gai nông phù hợp đường cứng.",
  },
  catalog_grounded: {
    en: "Recommended only from a verified, curated database of real products, not generated freely by the AI.",
    vi: "Chỉ gợi ý từ một cơ sở dữ liệu sản phẩm thật, đã được xác minh — không phải do AI tự sinh ra.",
  },
  carb_oxidation: {
    en: "How many grams of carbohydrate your gut and muscles can actually absorb and burn per hour during exercise — roughly 60-90g/hour is the trainable range for most athletes.",
    vi: "Số gram carbohydrate mà dạ dày và cơ bắp bạn thực sự có thể hấp thụ và đốt mỗi giờ — khoảng 60-90g/giờ là mức trần luyện tập được với hầu hết vận động viên.",
  },
  sodium_rate: {
    en: "How much sodium you need to replace per hour based on sweat losses — too little risks cramping, too much can cause GI distress.",
    vi: "Lượng sodium cần bù mỗi giờ dựa trên lượng mất qua mồ hôi — bù quá ít dễ gây chuột rút, bù quá nhiều có thể gây rối loạn tiêu hóa.",
  },
  gut_training: {
    en: "Practicing your actual race-day fueling plan during training runs, so your digestive system adapts to processing calories under exercise stress.",
    vi: "Luyện tập đúng kế hoạch dinh dưỡng ngày thi đấu trong các buổi chạy tập, để hệ tiêu hóa thích nghi với việc xử lý calo dưới áp lực vận động.",
  },
};
