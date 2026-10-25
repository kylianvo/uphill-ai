package ai.uphill.app.core.knowledge
object CuratedKnowledge {
    fun cards(lang: String): List<KnowledgeCard> {
        val vi = lang == "vi"
        return listOf(
            KnowledgeCard(
                1,
                if (vi) "Thiếu nền Aerobic" else "Aerobic Deficiency Syndrome (ADS)",
                if (vi)
                    "Nền Aerobic chưa đủ khiến cơ thể dùng glycogen ngay cả khi đi bộ. Tập Zone 1–2 đều đặn giúp cơ thể dùng chất béo làm nguồn năng lượng chính."
                else
                    "When aerobic capacity is undertrained, the body burns glycogen even at walking paces. Building a deep Zone 1-2 aerobic base shifts your metabolism to burn fat as the primary fuel source.",
                if (vi)
                    listOf(
                        "Giữ 80–85% khối lượng tuần dưới AeT, ở pace vẫn nói chuyện thoải mái.",
                        "Kiểm tra AeT bằng HR drift: HR tăng dưới 5% trong một giờ chạy đều.",
                        "Cần 12–24 tuần tập nhẹ đều đặn để xây lại nền Aerobic.",
                    )
                else
                    listOf(
                        "Keep 80-85% of weekly volume below AeT (conversational nose-breathing pace).",
                        "Testing AeT via heart rate drift test: HR should rise less than 5% over an hour at constant speed.",
                        "Patience is key: rebuilding mitochondrial density takes 12 to 24 weeks of consistent low-intensity volume.",
                    ),
                topic = "Training",
                sourceLabel = "Training for the Uphill Athlete",
            ),
            KnowledgeCard(
                2,
                if (vi) "Gut training: 60–90g Carbs / giờ" else "Gut Training: 60-90g Carbs / Hour",
                if (vi)
                    "Ultra trên 4 giờ cần Carbs để giữ glycogen. Tập fueling trong Long Run để đường ruột quen với lượng Carbs cao."
                else
                    "During ultras longer than 4 hours, exogenous carbohydrate oxidation preserves liver and muscle glycogen. The gut must be systematically trained in long runs to tolerate high carb flux.",
                if (vi)
                    listOf(
                        "Dùng glucose và fructose theo tỷ lệ 2:1 hoặc 1:0,8.",
                        "Tập dùng 20–30g Carbs mỗi 20 phút với 150ml nước.",
                        "Tránh đồ ăn nhiều chất béo hoặc protein khi leo dốc gắng sức.",
                    )
                else
                    listOf(
                        "Utilize a 2:1 or 1:0.8 glucose-to-fructose ratio to utilize separate intestinal transporters (SGLT1 and GLUT5).",
                        "Practice race-day fueling frequency: 20-30g every 20 minutes with 150ml water.",
                        "Avoid high-fat or high-protein solids during steep high-exertion climbs when blood flow is diverted from the gut.",
                    ),
                topic = "Nutrition",
                sourceLabel = "Jeukendrup Sports Nutrition",
            ),
            KnowledgeCard(
                3,
                if (vi) "Chi phí độ dốc và ngưỡng hiking"
                else "Minetti Gradient Cost & The Hike Threshold",
                if (vi)
                    "Chi phí năng lượng tăng mạnh khi dốc trên 15%. Chuyển sang power hiking ở dốc khoảng 18–20% để giữ glycogen."
                else
                    "Metabolic cost per meter rises exponentially once gradient exceeds 15%. Efficient ultra runners transition from running to power hiking at ~18-20% grade to conserve glycogen.",
                if (vi)
                    listOf(
                        "Dốc trên 20%: chạy có thể tốn hơn 35% năng lượng mà không nhanh hơn nhiều.",
                        "Dùng gậy để giảm tải cho đầu gối.",
                        "Rút ngắn sải chân, giữ HR dưới AeT khi leo.",
                    )
                else
                    listOf(
                        "On grades steeper than 20%, running burns up to 35% more energy per vertical meter than power hiking for negligible speed gain.",
                        "Use trekking poles to engage latissimus and core musculature, offloading knee extensors.",
                        "Shorten stride cadence on climbs to keep heart rate strictly clamped below AeT.",
                    ),
                topic = "Pacing",
                sourceLabel = "Minetti (2002) Energetics of Locomotion",
            ),
            KnowledgeCard(
                4,
                if (vi) "Phục hồi gân và giấc ngủ" else "Tendon Remodeling & Sleep Architecture",
                if (vi) "Giấc ngủ sâu hỗ trợ tổng hợp collagen và phục hồi thần kinh cơ."
                else
                    "Connective tissue collagen synthesis and neuromuscular recovery peak during deep slow-wave sleep (NREM Stage 3/4) through pulsatile human growth hormone release.",
                if (vi)
                    listOf(
                        "Giữ giờ ngủ đều, ngủ 8–9 giờ trong tuần tập cao điểm.",
                        "Theo dõi Resting HR và HRV; HRV giảm nhiều ngày có thể báo mệt.",
                        "Magnesium glycinate và chiết xuất tart cherry có thể hỗ trợ thư giãn cơ.",
                    )
                else
                    listOf(
                        "Prioritize consistent sleep schedules: 8-9 hours per night during peak training weeks.",
                        "Track resting HR and HRV trends: sustained multi-day drops in HRV indicate sympathetic fatigue.",
                        "Magnesium glycinate (300-400mg) and tart cherry extract promote muscle relaxation and reduce inflammatory soreness.",
                    ),
                topic = "Recovery",
                sourceLabel = "Matthew Walker: Why We Sleep",
            ),
            KnowledgeCard(
                5,
                if (vi) "Chia nhỏ race 100K" else "Segmenting 100K: The 3-Aid-Station Horizon",
                if (vi) "Tập trung vào CP phía trước giúp giảm cảm giác quá tải khi chạy Ultra."
                else
                    "Never run 100 kilometers in your head. Psychological overwhelm triggers early central governor fatigue. Anchor your mind solely to the immediate aid station ahead.",
                if (vi)
                    listOf(
                        "Chia race thành các mục tiêu nhỏ 8–12km.",
                        "Nếu tụt tinh thần ở km 50–70, ăn 200 kcal rồi chờ 15 phút trước khi quyết định.",
                        "Tập trung vào Cadence, hơi thở và nhịp fueling.",
                    )
                else
                    listOf(
                        "Break the race into bite-sized 8-12km micro-goals.",
                        "When the dark low-point strikes between 50-70km, recognize that mood follows blood sugar: eat 200 kcal and wait 15 minutes before any decision.",
                        "Focus on process execution (cadence, breath, fueling rhythm) rather than elapsed time or field position.",
                    ),
                topic = "Mindset",
                sourceLabel = "Endure: Cameron Elson",
            ),
            KnowledgeCard(
                6,
                if (vi) "Chọn đế giày và Lug Depth" else "Outsole Compound & Lug Depth Selection",
                if (vi) "Độ bám phù hợp giúp giảm trượt chân và mệt cơ khi chạy Ultra."
                else
                    "Traction dictates braking muscle fatigue. Matching lug depth and rubber compound to course terrain saves thousands of micro-slips over an ultra.",
                if (vi)
                    listOf(
                        "Lug trên 5mm hợp bùn và đất sét ướt.",
                        "Vibram Megagrip và Contagrip hợp đá, rễ cây ẩm.",
                        "Đường khô dễ chạy hợp lug 3,5–4mm.",
                    )
                else
                    listOf(
                        "Deep 5.0mm+ lugs with wide channel spacing are essential for wet clay, mud, and loose tropical scree.",
                        "Vibram Megagrip and Contagrip wet-traction compounds excel on slick river rock and damp limestone roots.",
                        "For dry hardpack or runnable fire roads, 3.5-4.0mm lugs reduce ground-contact drag and foot fatigue.",
                    ),
                topic = "Gear",
                sourceLabel = "Uphill AI Gear Vault",
            ),
            KnowledgeCard(
                7,
                if (vi) "Muscular Endurance: dốc dài" else "Muscular Endurance: Vertical Intervals",
                if (vi) "ME giúp bắp chân, đùi và mông chịu tải lâu khi leo dốc."
                else
                    "Uphill running economy requires high mechanical power at low velocity. ME training develops fatigue-resistant slow-twitch motor units in the calves, quads, and glutes.",
                if (vi)
                    listOf(
                        "Hill Repeat liên tục ở dốc 15–25%, Zone 3, đi bộ xuống phục hồi.",
                        "Tập leo Treadmill hoặc cầu thang với tải nhẹ mỗi tuần trong Base Block.",
                        "Giữ thân cao, nghiêng từ cổ chân khi leo.",
                    )
                else
                    listOf(
                        "Perform continuous steep hill repeats (15-25% gradient) at Zone 3 effort with easy walk-down recovery.",
                        "Incorporate weighted uphill treadmill or stair climbs (10-15% body weight vest) once weekly in the base block.",
                        "Preserve structural form: tall posture, forward chest lean from ankles rather than bending at the waist.",
                    ),
                topic = "Training",
                sourceLabel = "Training for the Uphill Athlete",
            ),
            KnowledgeCard(
                8,
                if (vi) "Sodium và hạ natri máu"
                else "Sodium Balance & Exercise-Associated Hyponatremia",
                if (vi)
                    "Uống quá nhiều nước không có Sodium làm loãng natri máu. Duy trì 500–800mg Sodium mỗi lít nước trong race nóng."
                else
                    "Over-drinking plain water without sodium dilutes blood plasma osmolality. Maintain 500-800mg sodium per liter of fluid consumed during hot mountain races.",
                if (vi)
                    listOf(
                        "Sodium trong mồ hôi khác nhau giữa mỗi người; thử đo khi tập trời nóng.",
                        "Mang viên muối cho đoạn nóng ẩm giữa ngày.",
                        "Khó tập trung, ngón tay sưng và buồn nôn có thể liên quan mất cân bằng Sodium.",
                    )
                else
                    listOf(
                        "Sweat sodium concentration varies widely (400mg to 1,800mg per liter): test your sweat rate in warm training runs.",
                        "Carry chewable salt caps for hot humid mid-day sections.",
                        "Signs of sodium deficit include brain fog, swollen fingers, and nausea despite feeling thirsty.",
                    ),
                topic = "Nutrition",
                sourceLabel = "Tim Noakes: Waterlogged",
            ),
        )
    }
}
