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
    vi: "Ngưỡng Aerobic Threshold mà tại đó cơ thể chuyển từ đốt mỡ là chính sang sử dụng nhiều carb hơn. Tập luyện dưới ngưỡng này giúp xây dựng nền tảng hiếu khí vững chắc mà không gây quá tải mệt mỏi.",
  },
  ant: {
    en: "The effort where lactate starts piling up faster than your body clears it — roughly your \"hard but sustainable for about an hour\" pace.",
    vi: "Ngưỡng Anaerobic Threshold mà tại đó lactate tích tụ nhanh hơn tốc độ cơ thể đào thải — tương đương mức pace nỗ lực cao mà bạn có thể duy trì bền bỉ trong khoảng 1 giờ.",
  },
  zones: {
    en: "Five effort bands anchored to your own AeT and AnT, not a generic percentage of max HR. Zone 1-2 = easy/aerobic, Zone 3 = tempo, Zone 4-5 = threshold/VO2max.",
    vi: "5 vùng nhịp tim (Zones) được xác định chính xác theo ngưỡng AeT và AnT của riêng bạn, thay vì tính theo % công thức chung. Zone 1-2 là Easy/Aerobic, Zone 3 là Tempo, Zone 4-5 là Threshold/VO2max.",
  },
  eighty_twenty: {
    en: "The split elite endurance athletes train by — roughly 80% easy, 20% hard — because too much moderate-intensity work causes fatigue without building fitness.",
    vi: "Nguyên tắc 80/20 chuẩn mực của các vận động viên sức bền hàng đầu — khoảng 80% thời lượng ở cường độ nhẹ (Easy), 20% ở cường độ cao — tránh vùng xám (moderate) gây mệt mỏi mà ít mang lại tiến bộ.",
  },
  muscular_endurance: {
    en: "Your muscles' ability to keep firing efficiently for hours — trained with hill sprints, step-ups, and downhill-specific work, distinct from raw strength or aerobic capacity.",
    vi: "Khả năng phát lực bền bỉ của cơ bắp qua nhiều giờ leo dốc liên tục — được rèn luyện bằng Hill Sprints, Step-ups và các bài tập chuyên biệt cho đổ dốc, khác biệt với sức mạnh tối đa hay dung tích hiếu khí.",
  },
  rag: {
    en: "Instead of answering purely from memory, the AI first looks up relevant facts from a trusted database, then writes its answer using those facts.",
    vi: "Kiến trúc RAG (Retrieval-Augmented Generation): Thay vì suy đoán tự do, AI sẽ tra cứu các dữ kiện chuẩn xác từ kho tri thức trước, sau đó tổng hợp câu trả lời dựa trên tài liệu khoa học đó.",
  },
  grounded: {
    en: "A response backed by a specific, retrievable source in the knowledge base, rather than the model's general training data.",
    vi: "Câu trả lời được đối chiếu và bảo chứng trực tiếp từ tài liệu nguồn trong Knowledge Base, đảm bảo tính chuẩn xác và khoa học.",
  },
  ab_c_goals: {
    en: "Three finish-time targets for one race — A (ambitious, everything goes right), B (realistic/expected), C (safe, banks margin for a bad day).",
    vi: "3 kịch bản mục tiêu thời gian cho ngày thi đấu — Kế hoạch A (Ambitious, khi phong độ và điều kiện hoàn hảo), B (Realistic, mục tiêu kỳ vọng thực tế), C (Safe, phương án an toàn khi gặp sự cố).",
  },
  base_flat_pace: {
    en: "Your pace on flat, sea-level ground with no accumulated fatigue — the \"pure fitness\" number every other prediction is built from.",
    vi: "Pace của bạn trên đường bằng phẳng ngang mực nước biển khi thể lực sung mãn — chỉ số thể lực gốc để làm căn cứ tính toán cho mọi cung đường.",
  },
  rank_transfer: {
    en: "Estimating your finish time on a new race by comparing it to how you'd have ranked in a past one — the same logic sites like UltraSignup use.",
    vi: "Phương pháp ước tính thời gian về đích ở giải đấu mới dựa trên thứ hạng percentile bạn từng đạt được ở giải đấu trước đó (tương tự thuật toán của UltraSignup).",
  },
  grade_adjusted_pace: {
    en: "Your pace converted to its flat-ground equivalent, accounting for how much harder climbing (or how much descending helps) actually costs metabolically.",
    vi: "Pace tương đương trên đường bằng (GAP - Grade Adjusted Pace), quy đổi chính xác chi phí năng lượng tiêu hao khi leo dốc hoặc lợi thế khi đổ dốc.",
  },
  minetti_curve: {
    en: "A published physiology model (Minetti et al., 2002) of the metabolic energy cost of running at different uphill/downhill grades.",
    vi: "Mô hình tiêu hao năng lượng thể chất (Minetti và cộng sự, 2002) tính toán năng lượng tiêu tốn khi chạy ở các độ dốc lên/xuống khác nhau.",
  },
  durability: {
    en: "How much your pace naturally slows as accumulated distance wears on your legs, independent of terrain — modeled starting after roughly 15km of flat-equivalent running.",
    vi: "Mức độ suy giảm Pace tự nhiên do mỏi cơ tích lũy theo quãng đường dài — mô hình tính toán sự suy giảm này sau khoảng 15km quy đổi tương đương đường bằng.",
  },
  split_bias: {
    en: "Deliberately running the second half faster (or holding even effort) rather than starting fast and fading.",
    vi: "Chiến thuật phân phối sức (Negative Split hoặc Even Effort) — chủ động giữ sức nửa đầu và tăng tốc nửa sau thay vì xuất phát quá nhanh dẫn đến đuối sức.",
  },
  altitude_penalty: {
    en: "The pace cost of running at elevation, where thinner air reduces oxygen delivery — applied above roughly 1,500m in this model.",
    vi: "Hệ số suy giảm thể lực do độ cao — không khí loãng làm giảm lượng oxy cung cấp cho cơ bắp, áp dụng tính toán từ độ cao 1.500m trở lên.",
  },
  stack_height: {
    en: "The thickness of cushioning between your foot and the ground — more stack generally means more shock absorption but less ground feel.",
    vi: "Độ dày bộ đệm đế giữa bàn chân và mặt đất — Stack Height cao giúp giảm chấn và êm hơn nhưng giảm cảm giác tiếp đất (Ground Feel).",
  },
  drop: {
    en: "The height difference between a shoe's heel and forefoot — lower drop encourages a more midfoot/forefoot strike, higher drop favors heel strikers.",
    vi: "Độ chênh lệch chiều cao giữa gót và mũi giày (Heel-to-toe Drop) — Drop thấp phù hợp tiếp đất giữa/mũi chân (Midfoot/Forefoot), Drop cao hỗ trợ người tiếp đất bằng gót (Heel Strike).",
  },
  carbon_plate: {
    en: "A rigid plate embedded in the midsole that acts like a lever, improving running economy at faster paces.",
    vi: "Tấm Carbon Plate đặt trong đế giữa giày đóng vai trò như đòn bẩy trợ lực, tối ưu hiệu suất năng lượng (Running Economy) ở tốc độ cao.",
  },
  lug_depth: {
    en: "How deep a trail shoe's outsole tread is — deeper lugs grip better in mud/loose terrain, shallower lugs suit hardpack and roads.",
    vi: "Độ sâu vấu gai đế ngoài (Lug Depth) của giày trail — gai sâu bám tốt trên bùn và địa hình trơn trượt, gai nông tối ưu cho đường nén cứng (Hardpack) và đường bằng.",
  },
  catalog_grounded: {
    en: "Recommended only from a verified, curated database of real products, not generated freely by the AI.",
    vi: "Gợi ý trang thiết bị dựa trên danh mục sản phẩm thực tế đã được kiểm chứng và chọn lọc, không phải do AI tự suy diễn.",
  },
  carb_oxidation: {
    en: "How many grams of carbohydrate your gut and muscles can actually absorb and burn per hour during exercise — roughly 60-90g/hour is the trainable range for most athletes.",
    vi: "Tốc độ oxy hóa và hấp thụ Carbohydrate tối đa của hệ tiêu hóa và cơ bắp mỗi giờ (khoảng 60-90g Carbs/giờ đối với vận động viên được rèn luyện).",
  },
  sodium_rate: {
    en: "How much sodium you need to replace per hour based on sweat losses — too little risks cramping, too much can cause GI distress.",
    vi: "Lượng Sodium (Natri) và điện giải cần bù mỗi giờ dựa trên lượng mồ hôi thất thoát — thiếu hụt gây chuột rút, dư thừa có thể gây rối loạn tiêu hóa.",
  },
  gut_training: {
    en: "Practicing your actual race-day fueling plan during training runs, so your digestive system adapts to processing calories under exercise stress.",
    vi: "Phương pháp rèn luyện hệ tiêu hóa (Gut Training) trong các buổi tập dài để dạ dày thích nghi hoàn hảo với việc hấp thụ năng lượng ở cường độ vận động cao trong ngày race.",
  },
};
