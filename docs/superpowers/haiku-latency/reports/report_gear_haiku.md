# Golden report — gear


## gear_fixture_budget_beginner

- Gemini+KB latency: **16.5s** (baseline: 6.7s)
- Catalog membership: ✅ all recommendations exist in the distilled catalog

<details><summary>Gemini+KB output</summary>

```json
{
  "recommendations": [
    {
      "model": "Ride 19",
      "brand": "Saucony",
      "foam_material": "High-energy daily foam (not specified)",
      "outsole_compound": "XT-900 high-traction rubber",
      "lug_depth": "0.0 mm",
      "drop": "8.0 mm",
      "stack": "Heel 38.7 mm / Forefoot 30.2 mm",
      "weight": "9 oz / 255 g",
      "price": "$145 (best price $117)",
      "pros": "A classic, dependable daily trainer with a wide, stable landing platform and high energy return. Its medium fit and balanced cushioning suit a first running shoe.",
      "cons": "It is heavier than its predecessor and has limited outsole rubber coverage. Its price is above the $90 budget."
    },
    {
      "model": "Pegasus 42",
      "brand": "Nike",
      "foam_material": "ReactX daily foam (not specified)",
      "outsole_compound": "High-longevity road rubber",
      "lug_depth": "0 mm",
      "drop": "10.0 mm",
      "stack": "Heel 37.0 mm / Forefoot 27.0 mm",
      "weight": "10.5 oz / 297 g",
      "price": "$145",
      "pros": "A stable, traditional daily cruiser with moderate cushioning and a medium fit, aimed at beginners. Its outsole is durable for everyday mileage.",
      "cons": "It feels heavy and lacks energetic rebound, and its 10 mm drop is steep. Its price is above the $90 budget."
    },
    {
      "model": "Velocity Nitro 5",
      "brand": "Puma",
      "foam_material": "Dual-layer A-TPU Nitro foam (A-TPU)",
      "outsole_compound": "Pumagrip",
      "lug_depth": "Not specified",
      "drop": "8 mm",
      "stack": "Heel 35 mm / Forefoot 27 mm",
      "weight": "8.6 oz / 244 g",
      "price": "$140",
      "pros": "A balanced, responsive daily trainer with excellent wet and dry traction and a secure lockdown. It offers strong value for a beginner's first shoe.",
      "cons": "It is slightly heavier and less bouncy than the v4, and its toebox is narrow and snug in standard width. Its price is above the $90 budget."
    },
    {
      "model": "Adizero Boston 13",
      "brand": "adidas",
      "foam_material": "Lightstrike Pro (TPE) & Lightstrike (EVA)",
      "outsole_compound": "Continental rubber in forefoot & LightTraxion lateral rubber",
      "lug_depth": "0.0 mm",
      "drop": "6 mm",
      "stack": "Heel 36 mm / Forefoot 30 mm",
      "weight": "9 oz / 255 g",
      "price": "$160",
      "pros": "A versatile, durable trainer with a standard fit and moderate cushioning that handles most paces. It has a comfortable step-in feel.",
      "cons": "It is frustratingly difficult to dial in the laces, and it is better suited to narrow-footed runners. Its price is well above the $90 budget."
    },
    {
      "model": "Novablast 5",
      "brand": "Asics",
      "foam_material": "FF Blast MAX (supercritical)",
      "outsole_compound": "High-traction road rubber (0 mm)",
      "lug_depth": "0 mm",
      "drop": "7.4 mm",
      "stack": "Heel 40.9 mm / Forefoot 33.5 mm",
      "weight": "9 oz / 255 g",
      "price": "$150",
      "pros": "A bouncy, lightweight daily trainer with a medium fit that is friendly to wider feet. Its cushioning feels lively for everyday runs.",
      "cons": "Its toebox mesh durability is subpar and it can run warm in heat. Its price is well above the $90 budget."
    }
  ],
  "tips": [
    "No knowledge base shoe is priced at or near the $90 budget, so the lowest-priced options here are around $140; consider watching for sales, as Saucony Ride 19 has a best price of $117.",
    "For your 3 runs per week and 10 km per week, a well-cushioned, medium-fit shoe with a 6 to 8 mm drop is a comfortable starting point, so try shoes on and choose the one that feels smoothest."
  ],
  "matched_race": null,
  "feedback_token": "f7853dc47cfb0b303a61197432d14232.gear_finder.34a7849fd87e58eb4c096ac3c58b530b"
}
```
</details>
<details><summary>Captured baseline</summary>

```json
{
  "recommendations": [
    {
      "model": "Pegasus 42",
      "brand": "Nike",
      "foam_material": "ReactX daily foam (EVA)",
      "outsole_compound": "High-longevity road rubber",
      "lug_depth": "0 mm",
      "drop": "10.0 mm",
      "stack": "37.0/27.0 mm",
      "weight": "10.5 oz / 297 g",
      "price": "$145",
      "pros": "A classic everyday cruiser that offers a stable platform and outstanding outsole durability. Extremely comfortable mesh upper suited for beginner mileage.",
      "cons": "Lacks high-energy rebound and features a steep drop that may feel firm in the forefoot."
    },
    {
      "model": "Aero Blaze 4",
      "brand": "Salomon",
      "foam_material": "Optifoam2 (eTPU)",
      "outsole_compound": "Road ContaGrip",
      "lug_depth": "None",
      "drop": "8 mm",
      "stack": "36 mm heel / 28 mm forefoot",
      "weight": "8.0 oz / 226 g",
      "price": "$140",
      "pros": "Lightweight and agile everyday road trainer with balanced cushioning. Provides a responsive and snappy eTPU ride for daily runs.",
      "cons": "The fit runs snug through the midfoot and lacks added structural support."
    },
    {
      "model": "Velocity Nitro 4",
      "brand": "Puma",
      "foam_material": "Reformulated Nitrofoam (TPU)",
      "outsole_compound": "Pumagrip",
      "lug_depth": "0.0 mm",
      "drop": "10 mm",
      "stack": "36/26 mm",
      "weight": "Not available",
      "price": "$140",
      "pros": "Delivers outstanding wet and dry traction with high outsole durability. Balanced cushioning provides a bouncy, versatile daily platform.",
      "cons": "Fit runs quite narrow in the toe box and the 10 mm drop may feel steep."
    },
    {
      "model": "Ride 19",
      "brand": "Saucony",
      "foam_material": "High-energy daily foam (EVA)",
      "outsole_compound": "XT-900 high-traction rubber",
      "lug_depth": "0.0 mm",
      "drop": "8.0 mm",
      "stack": "Heel 38.7 mm / Forefoot 30.2 mm",
      "weight": "9 oz / 255 g",
      "price": "$145 (best price $117)",
      "pros": "A highly dependable neutral trainer with a wide, stable landing platform. Offers breathable comfort and balanced daily protection.",
      "cons": "Slightly heavier than previous versions and features zoned outsole rubber coverage."
    },
    {
      "model": "Torin 8",
      "brand": "Altra",
      "foam_material": "Standard daily training foam (EVA)",
      "outsole_compound": "High-traction road rubber",
      "lug_depth": "0.0 mm",
      "drop": "0 mm",
      "stack": "27.6 mm heel / 27.7 mm forefoot",
      "weight": "10.1 oz / 287 g",
      "price": "$150 - $160",
      "pros": "Features a balanced cushion profile and a standard foot-shaped fit that encourages natural toe splay. Reliable lockdown for easy daily runs and walking.",
      "cons": "The zero-drop platform requires an adjustment period for new runners, and the foam lacks superfoam bounce."
    }
  ],
  "tips": [
    "Note that no options in the catalog strictly meet a $90 retail budget, though several models like the Saucony Ride 19 frequently see price drops near $117.",
    "As a new runner starting at 10 km per week, focus on consistent, comfortable mileage in a balanced, unplated trainer before exploring fast day or racing models."
  ],
  "matched_race": null
}
```
</details>

## gear_fixture_low_drop_transition

- Gemini+KB latency: **19.8s** (baseline: 6.6s)
- Catalog membership: ✅ all recommendations exist in the distilled catalog

<details><summary>Gemini+KB output</summary>

```json
{
  "recommendations": [
    {
      "model": "SuperComp Rebel V1",
      "brand": "New Balance",
      "foam_material": "Infinion Aliphatic TPU (A-TPU)",
      "outsole_compound": "Targeted lightweight rubber",
      "lug_depth": "0 mm",
      "drop": "4 mm",
      "stack": "40 mm heel / 36 mm forefoot",
      "weight": "7.7 oz / 218 g",
      "price": "$200",
      "pros": "Lightweight, bouncy plated trainer that suits tempo and interval sessions. Its 4 mm drop fits your low-drop goal, and its 40 mm stack gives max-cushion protection, a bit firmer than your medium target.",
      "cons": "Costs more than standard trainers and is less aggressive than pure racers. Its max-level cushioning is above your medium preference."
    },
    {
      "model": "Cloudboom Strike",
      "brand": "On",
      "foam_material": "Helion HF (Pebax)",
      "outsole_compound": "Mission Grip",
      "lug_depth": "0 mm",
      "drop": "4 mm",
      "stack": "38.1 mm heel / 34.9 mm forefoot",
      "weight": "7.4 oz / 210 g",
      "price": "$280",
      "pros": "Very bouncy, lightweight carbon-plated racer that excels at fast tempo and interval work. Its 4 mm drop matches your low-drop requirement.",
      "cons": "Heel security is polarizing and the catalog lists it as not suitable for heel strikers. It is also expensive and runs on the maximal side of cushioning."
    },
    {
      "model": "Adizero Adios Pro 5",
      "brand": "adidas",
      "foam_material": "A-TPU base with softer PEBA-based top layer (Lightstrike Pro)",
      "outsole_compound": "Lighttraxion PU with small Continental forefoot patch",
      "lug_depth": "0 mm",
      "drop": "4 mm",
      "stack": "39 mm heel / 35 mm forefoot",
      "weight": "6.2 oz / 177 g",
      "price": "$275",
      "pros": "Light, responsive road super shoe with strong forefoot energy return that suits interval and tempo efforts. Its listed 4 mm drop is in your range.",
      "cons": "The catalog lists a narrow toe box and a small fit, so check sizing for standard width. Outsole durability is a concern, and the lab drop is 5.6 mm."
    },
    {
      "model": "Torin 8",
      "brand": "Altra",
      "foam_material": "Standard daily training foam",
      "outsole_compound": "High-traction road rubber",
      "lug_depth": "0 mm",
      "drop": "0 mm",
      "stack": "27.6 mm heel / 27.7 mm forefoot",
      "weight": "10.1 oz / 287 g",
      "price": "$150 - $160",
      "pros": "True zero-drop road shoe with balanced cushioning and a roomy, standard-fitting toe box. It is a comfortable, dependable choice for a gradual drop transition.",
      "cons": "It is aimed at daily running and walking rather than tempo and intervals, and it is heavy for fast work. The catalog says it is not for heavy heel strikers."
    },
    {
      "model": "Paradigm 8",
      "brand": "Altra",
      "foam_material": "EGO MAX (soft/responsive)",
      "outsole_compound": "Extra-thick road rubber",
      "lug_depth": "0 mm",
      "drop": "2.1 mm",
      "stack": "29.4 mm heel / 27.3 mm forefoot",
      "weight": "9.8 oz / 278 g",
      "price": "$170",
      "pros": "Low 2.1 mm drop with soft, protective cushioning and a roomy toe box. It suits an easy transition from 10 mm shoes.",
      "cons": "Its stability design and heavy layout make it a weak fit for speed work. The catalog notes it lacks high energy return."
    }
  ],
  "tips": [
    "Transition from 10 mm to low-drop shoes gradually, starting with a few easy runs per week in the new shoe, since calf and Achilles loading increases with lower drop.",
    "Your tempo and interval sessions will benefit most from the lighter, more responsive options, so use a faster shoe for those days and keep a softer low-drop shoe for easy runs."
  ],
  "matched_race": null,
  "feedback_token": "c233f2e6a974dd572a93ef4c2a0ecc1b.gear_finder.e58098f9ed95dcf1a26436bf7981b258"
}
```
</details>
<details><summary>Captured baseline</summary>

```json
{
  "recommendations": [
    {
      "model": "SuperComp Rebel V1",
      "brand": "New Balance",
      "foam_material": "Infinion Aliphatic TPU (A-TPU)",
      "outsole_compound": "Targeted lightweight rubber",
      "lug_depth": "None (road)",
      "drop": "4 mm",
      "stack": "40 mm heel / 36 mm forefoot",
      "weight": "7.7 oz / 218 g",
      "price": "$200",
      "pros": "Built for tempo runs, intervals, and versatile road racing with an energetic carbon-infused plate. Delivers lightweight bounce at an airy weight while providing protective cushioning.",
      "cons": "Pricier than non-plated trainers, and slightly less aggressive than pure marathon racing flats."
    },
    {
      "model": "Cloudboom Strike",
      "brand": "On",
      "foam_material": "Helion HF (Pebax)",
      "outsole_compound": "Mission Grip",
      "lug_depth": "0.0 mm",
      "drop": "4 mm",
      "stack": "38.1/34.9 mm",
      "weight": "7.4 oz / 210 g",
      "price": "$280",
      "pros": "Delivers outstanding 72.1% energy return with a propulsive carbon Speedboard for high-speed intervals. Extremely light on foot with fantastic forward turnover.",
      "cons": "Expensive and not suitable for heel strikers due to limited landing stability and polarizing heel security."
    },
    {
      "model": "Mach 7",
      "brand": "Hoka",
      "foam_material": "Balanced daily EVA-blend (EVA)",
      "outsole_compound": "Segmented road rubber",
      "lug_depth": "0.0 mm lugs",
      "drop": "5 mm",
      "stack": "Heel 35.6 mm / Forefoot 26.2 mm",
      "weight": "8.5 oz / 241 g",
      "price": "$145",
      "pros": "Features moderate, balanced cushioning that excels during tempo workouts and agile intervals. Very lightweight with elite-level upper breathability and a smooth rolling rocker.",
      "cons": "Drop is slightly above the 0-4 mm range at 5 mm, and narrow fit can pinch wide toes."
    },
    {
      "model": "Mach X 3",
      "brand": "Hoka",
      "foam_material": "Dual-density PEBA & EVA dual foam",
      "outsole_compound": "Durable road rubber",
      "lug_depth": "0.0 mm lugs",
      "drop": "5 mm",
      "stack": "Heel 42.9 mm / Forefoot 33.4 mm",
      "weight": "8.9 oz / 252 g",
      "price": "$190",
      "pros": "Designed specifically for fast tempo workouts and daily mileage with bouncy forefoot propulsion. Full-length plate and rocker provide snappy transitions to keep legs fresh.",
      "cons": "At 5 mm drop it sits just above the 4 mm cutoff, and the layout runs slightly heavy with a non-gusseted tongue."
    },
    {
      "model": "Torin 8",
      "brand": "Altra",
      "foam_material": "Standard daily training foam",
      "outsole_compound": "High-traction road rubber",
      "lug_depth": "Road (0.0 mm)",
      "drop": "0 mm",
      "stack": "27.6 mm heel / 27.7 mm forefoot",
      "weight": "10.1 oz / 287 g",
      "price": "$150 - $160",
      "pros": "True zero-drop geometry with balanced, medium-level cushioning for a natural foot strike. Features improved heel lockdown and comfortable toe splay for neutral running.",
      "cons": "Lacks the snappy supercritical bounce ideal for aggressive speedwork, and feels heavy for pure interval sessions."
    }
  ],
  "tips": [
    "Transitioning from a 10 mm drop directly down to low-drop or zero-drop shoes places significantly increased strain on your calves and Achilles tendons; alternate with your current pair and introduce the lower-drop shoe gradually.",
    "For faster tempo workouts and interval sessions, a shoe with 4-5 mm drop and an energetic foam or plate will provide responsiveness while smoothing your transition down from 10 mm."
  ],
  "matched_race": null
}
```
</details>

## gear_fixture_no_preferences

- Gemini+KB latency: **13.0s** (baseline: 6.0s)
- Catalog membership: ✅ all recommendations exist in the distilled catalog

<details><summary>Gemini+KB output</summary>

```json
{
  "recommendations": [
    {
      "model": "Speedgoat 7",
      "brand": "Hoka",
      "foam_material": "Supercritical EVA (EVA)",
      "outsole_compound": "Vibram Megagrip",
      "lug_depth": "5.0 mm",
      "drop": "5.0 mm",
      "stack": "37.0 mm heel / 32.0 mm forefoot",
      "weight": "9.55 oz / 271 g",
      "price": "$165",
      "pros": "A cushioned, responsive all-around trail trainer with a secure woven fit and strong Vibram wet and dry traction. It suits rugged trails, rocks, roots, and high-mileage days.",
      "cons": "The tall stack can feel clunky on technical trails, and it runs slightly short, so many runners should size up half a size."
    },
    {
      "model": "Tecton X 4",
      "brand": "Hoka",
      "foam_material": "Dual-density PEBA (PEBA)",
      "outsole_compound": "Vibram Megagrip Litebase with Traction Lug",
      "lug_depth": "4.0 mm",
      "drop": "5 mm",
      "stack": "40 mm heel / 35 mm forefoot",
      "weight": "9.2 oz / 261 g",
      "price": "$275",
      "pros": "A carbon-plated trail super shoe with highly responsive dual PEBA foam and a secure Matryx upper. It is well suited to race days and long trail ultras on technical trails and fast singletrack.",
      "cons": "The premium price and the dual plate setup can feel stiff on extreme off-camber terrain."
    },
    {
      "model": "Genesis 2",
      "brand": "Salomon",
      "foam_material": "OptiFoam (EVA / Olefin block copolymer)",
      "outsole_compound": "All-Terrain ContaGrip",
      "lug_depth": "4.5 mm",
      "drop": "8 mm",
      "stack": "34 mm heel / 26 mm forefoot",
      "weight": "9.6 oz / 264 g",
      "price": "$150",
      "pros": "A durable, stable technical mountain trainer with a Matryx upper and strong grip on mud and wet rock. It offers good value for rugged trail training and ultra terrain.",
      "cons": "It is not as bouncy as PEBA super shoes, and the Quicklace garage can feel snug."
    },
    {
      "model": "001A",
      "brand": "Norda",
      "foam_material": "Arnitel TPEE (TPEE)",
      "outsole_compound": "Vibram Megagrip Litebase",
      "lug_depth": "5.0 mm",
      "drop": "5 mm",
      "stack": "26 mm heel / 21 mm forefoot",
      "weight": "9.4 oz / 268 g",
      "price": "$295",
      "pros": "A durable all-around trail shoe with a virtually indestructible Dyneema upper and a softer, more energetic TPEE midsole. It suits everything from daily miles to 50K and 50-mile efforts.",
      "cons": "The ankle collar and heel counter can rub, and the fit calls for sizing up at least a half size."
    }
  ],
  "tips": [
    "Try shoes on in the afternoon or after a run, since feet swell and you should confirm the toe box and heel lock feel secure at standard width.",
    "Match the outsole to your local terrain: Vibram Megagrip and Megagrip Litebase models offer the most versatile wet and dry grip for mixed trails."
  ],
  "matched_race": null,
  "feedback_token": "fec5c7c5757ac060b684e0f230150e31.gear_finder.4225f12a6a814aafb4a6db54ebadbf33"
}
```
</details>
<details><summary>Captured baseline</summary>

```json
{
  "recommendations": [
    {
      "model": "Speedgoat 7",
      "brand": "Hoka",
      "foam_material": "Supercritical EVA (EVA)",
      "outsole_compound": "Vibram Megagrip",
      "lug_depth": "5.0 mm",
      "drop": "5.0 mm",
      "stack": "37.0/32.0 mm",
      "weight": "9.55 oz / 271 g",
      "price": "$165",
      "pros": "A dependable, highly cushioned mountain workhorse offering a livelier supercritical midsole. Features exceptional Vibram traction and a secure fit for rugged miles.",
      "cons": "The high stack can feel disconnected on technical terrain, and it tends to run slightly short."
    },
    {
      "model": "Genesis 2",
      "brand": "Salomon",
      "foam_material": "OptiFoam (EVA / Olefin block copolymer)",
      "outsole_compound": "All-Terrain ContaGrip",
      "lug_depth": "4.5 mm",
      "drop": "8 mm",
      "stack": "34 mm heel / 26 mm forefoot",
      "weight": "9.6 oz / 264 g",
      "price": "$150",
      "pros": "Built with an indestructible Matryx upper and Active Chassis stability. Provides forgiving moderate cushioning and reliable grip over varied terrain.",
      "cons": "It lacks the high energy return of PEBA-based super-shoes, and the Quicklace pocket can feel snug."
    },
    {
      "model": "Tecton X 4",
      "brand": "Hoka",
      "foam_material": "Dual-density PEBA (PEBA)",
      "outsole_compound": "Vibram Megagrip Litebase with Traction Lug",
      "lug_depth": "4.0 mm",
      "drop": "5 mm",
      "stack": "40 mm heel / 35 mm forefoot",
      "weight": "9.2 oz / 261 g",
      "price": "$275",
      "pros": "Flagship trail racer featuring ultra-bouncy dual PEBA foam and parallel carbon plates for maximum propulsion. The durable Matryx upper locks down securely on rolling trails.",
      "cons": "Carries a premium $275 price tag, and the dual plate design can feel rigid on severe off-camber terrain."
    },
    {
      "model": "M1",
      "brand": "Mount to Coast",
      "foam_material": "JetCell Aliphatic TPU (A-TPU)",
      "outsole_compound": "Vibram MegaGrip Litebase",
      "lug_depth": "4.0 mm",
      "drop": "4 mm",
      "stack": "38 mm heel / 34 mm forefoot",
      "weight": "9.7 oz / 274 g",
      "price": "$195",
      "pros": "Engineered for technical ultras with ultra-resilient A-TPU JetCell foam for fatigue resistance. Includes a customizable two-zone lacing system and top-tier Vibram grip.",
      "cons": "The brand is relatively new to the trail scene, and the forefoot taper may feel snug for broader feet."
    },
    {
      "model": "Terrex Agravic Speed Ultra 2",
      "brand": "adidas",
      "foam_material": "Lightstrike Pro (TPE)",
      "outsole_compound": "Continental Rubber",
      "lug_depth": "4 mm",
      "drop": "8 mm",
      "stack": "44 mm heel / 36 mm forefoot",
      "weight": "9.35 oz / 265 g",
      "price": "$225",
      "pros": "A maximal-stack, highly propulsive off-road racer featuring Lightstrike Pro and TPE Energy Rods. Excellent for maintaining leg freshness on fast trail and ultra distances.",
      "cons": "The towering 44 mm stack can feel unstable on highly technical, uneven surfaces."
    }
  ],
  "tips": [
    "When selecting a trail shoe, pair lug depth with your typical terrain: 3.5–4.5 mm lugs offer great all-around versatility on hardpack and rock, whereas 5 mm or deeper lugs excel in mud and loose grit.",
    "Consider whether you prefer a plated trail racer for dynamic propulsion on runnable courses or an unplated daily workhorse for better ground feel and control on technical singletrack."
  ],
  "matched_race": null
}
```
</details>

## gear_fixture_road_carbon_racer

- Gemini+KB latency: **12.5s** (baseline: 5.7s)
- Catalog membership: ✅ all recommendations exist in the distilled catalog

<details><summary>Gemini+KB output</summary>

```json
{
  "recommendations": [
    {
      "model": "Vaporfly 4",
      "brand": "Nike",
      "foam_material": "ZoomX (PEBA)",
      "outsole_compound": "Fast Shot rubber",
      "lug_depth": "Road (0 mm)",
      "drop": "6.0 mm",
      "stack": "35.0/29.0 mm",
      "weight": "6.5 oz / 184 g",
      "price": "$260",
      "pros": "Offers an incredibly bouncy, spring-loaded ride with a carbon Flyplate for race-day speed. Its extremely lightweight build and breathable upper suit marathon efforts well.",
      "cons": "It is a narrow fit, so it does not match the standard width requirement, and it is less ideal for full marathon racing than predecessors. Its outsole durability is poor."
    },
    {
      "model": "Zoom Fly 6",
      "brand": "Nike",
      "foam_material": "ZoomX (PEBA) & SR-02 (EVA) dual-density midsole",
      "outsole_compound": "High-durability road rubber",
      "lug_depth": "Road (0 mm)",
      "drop": "8.0 mm",
      "stack": "40.0/32.0 mm",
      "weight": "8.6 oz / 244 g",
      "price": "$170",
      "pros": "Provides max cushioning with a carbon Flyplate and a durable outsole, making it a versatile, plated option for marathon training and race paces. It is the most budget-friendly plated option in this comparison.",
      "cons": "It has a narrow fit and restrictive toebox, so it does not fully match the standard width requirement. The SR-02 foam lacks energetic bounce and can feel unstable on uneven surfaces."
    },
    {
      "model": "Adizero Adios Pro 4",
      "brand": "adidas",
      "foam_material": "Soft Lightstrike Pro (TPE)",
      "outsole_compound": "High-traction road rubber",
      "lug_depth": "0.0 mm",
      "drop": "6 mm",
      "stack": "39/33 mm",
      "weight": "7.1 oz / 200 g",
      "price": "$250",
      "pros": "Delivers exceptional energy return with a highly rockered, featherlight design built for race-day propulsion up to a marathon. Its Evo Pro EnergyRods and Lightlock band add plated support.",
      "cons": "The narrow, small fit requires sizing up and does not match the standard width requirement. It also rips up heel skin due to its empty pocket design and causes severe big toe discomfort in a narrow toe box."
    },
    {
      "model": "Adizero Boston 13",
      "brand": "adidas",
      "foam_material": "Lightstrike Pro (TPE) & Lightstrike (EVA)",
      "outsole_compound": "Continental rubber in forefoot & LightTraxion lateral rubber",
      "lug_depth": "0.0 mm",
      "drop": "6 mm",
      "stack": "36/30 mm",
      "weight": "9 oz / 255 g",
      "price": "$160",
      "pros": "Its standard fit matches the width requirement, and it has a carbon fiber EnergyRods plate for budget-friendly race day use. It is highly durable and offers a great step-in feel with padding.",
      "cons": "It is heavier than the other options and has only moderate cushioning rather than max cushioning. It is also frustratingly difficult to dial in and tie the laces."
    }
  ],
  "tips": [
    "Only four knowledge base shoes meet the plate, standard-width, and $280 budget criteria, so the list has four entries; the Nike Alphafly 3 ($285) is just over budget and the Adios Pro Evo 3 ($500) is well over, so both were excluded.",
    "For high cushioning with a standard fit, prioritize the Adizero Boston 13, then test the narrow-fitting Vaporfly 4 or Zoom Fly 6 with a wider-fit check before buying, since their toeboxes run narrow."
  ],
  "matched_race": null,
  "feedback_token": "d6e4cf3785a3af20e7b3beb05d7076d8.gear_finder.83b05916c366fd36413232988a4fef51"
}
```
</details>
<details><summary>Captured baseline</summary>

```json
{
  "recommendations": [
    {
      "model": "Alphafly 3",
      "brand": "Nike",
      "foam_material": "ZoomX (PEBA) paired with Air Pods",
      "outsole_compound": "Fast Shot outsole with high-abrasion rubber",
      "lug_depth": "0 mm",
      "drop": "8.0 mm",
      "stack": "40.0/32.0 mm",
      "weight": "7 oz / 198 g",
      "price": "$285",
      "pros": "Exceptionally lightweight, best-in-class breathability, and massive underfoot energy return. Smooth forward-rolling efficiency built specifically for elite marathon racing.",
      "cons": "Glued-down non-removable insole and potential outsole durability issues for heavy heel strikers."
    },
    {
      "model": "Adizero Adios Pro 4",
      "brand": "adidas",
      "foam_material": "Soft Lightstrike Pro (TPE)",
      "outsole_compound": "High-traction road rubber",
      "lug_depth": "0.0 mm",
      "drop": "6 mm",
      "stack": "39/33 mm",
      "weight": "7.1 oz / 200 g",
      "price": "$250",
      "pros": "Exceptional energy return and an invisible on-foot feel. Highly rockered geometry maximizing propulsion across marathon distances.",
      "cons": "Narrow toe box may cause discomfort and the heel pocket design can cause friction or blisters."
    },
    {
      "model": "Vaporfly 4",
      "brand": "Nike",
      "foam_material": "ZoomX (PEBA)",
      "outsole_compound": "Fast Shot rubber",
      "lug_depth": "0 mm",
      "drop": "6.0 mm",
      "stack": "35.0/29.0 mm",
      "weight": "6.5 oz / 184 g",
      "price": "$260",
      "pros": "Incredibly bouncy ride with an extremely lightweight build. Spring-loaded feel that excels at high-speed efforts and tempo intervals.",
      "cons": "Narrow heel and midfoot limit landing stability, and outsole durability is relatively low."
    },
    {
      "model": "Adizero Boston 13",
      "brand": "adidas",
      "foam_material": "Lightstrike Pro (TPE) & Lightstrike (EVA)",
      "outsole_compound": "Continental rubber in forefoot & LightTraxion lateral rubber",
      "lug_depth": "0.0 mm",
      "drop": "6 mm",
      "stack": "36/30 mm",
      "weight": "9 oz / 255 g",
      "price": "$160",
      "pros": "Great step-in feel with durable performance lasting hundreds of miles. Carbon fiber EnergyRods offer snappy propulsion at a budget-friendly race price.",
      "cons": "Laces can be frustratingly difficult to dial in and tie securely."
    },
    {
      "model": "Zoom Fly 6",
      "brand": "Nike",
      "foam_material": "ZoomX (PEBA) & SR-02 (EVA) dual-density midsole",
      "outsole_compound": "High-durability road rubber",
      "lug_depth": "0 mm",
      "drop": "8.0 mm",
      "stack": "40.0/32.0 mm",
      "weight": "8.6 oz / 244 g",
      "price": "$170",
      "pros": "Versatile performance that bridges marathon training with race day speed. Outstanding outsole durability with a full carbon Flyplate propulsion.",
      "cons": "Narrow fit with a restrictive toe box that may feel unstable on uneven road camber."
    }
  ],
  "tips": [
    "Be sure to complete at least one marathon-pace long run in your chosen carbon-plated shoe to adapt to its aggressive rocker and stiff plate geometry.",
    "Since racing super-shoes often feature snug upper profiles, test your race-day socks during training to avoid midfoot or heel blisters on race morning."
  ],
  "matched_race": null
}
```
</details>

## gear_fixture_road_daily_trainer

- Gemini+KB latency: **15.4s** (baseline: 7.0s)
- Catalog membership: ✅ all recommendations exist in the distilled catalog

<details><summary>Gemini+KB output</summary>

```json
{
  "recommendations": [
    {
      "model": "Saucony Ride 19",
      "brand": "Saucony",
      "foam_material": "High-energy daily foam (not specified)",
      "outsole_compound": "XT-900 high-traction rubber",
      "lug_depth": "0.0 mm",
      "drop": "8.0 mm",
      "stack": "38.7 mm heel / 30.2 mm forefoot",
      "weight": "9 oz / 255 g",
      "price": "$145",
      "pros": "A classic, dependable daily trainer with balanced max/medium cushioning, a wide stable landing platform, and excellent upper breathability. Well suited to standard-width feet doing everyday road miles and half marathon training.",
      "cons": "Heavier than its predecessor and has limited outsole rubber coverage. Less energetic than plated or supercritical foam options."
    },
    {
      "model": "Nike Pegasus 42",
      "brand": "Nike",
      "foam_material": "ReactX daily foam (not specified)",
      "outsole_compound": "High-longevity road rubber",
      "lug_depth": "0 mm",
      "drop": "10.0 mm",
      "stack": "37.0 mm heel / 27.0 mm forefoot",
      "weight": "10.5 oz / 297 g",
      "price": "$145",
      "pros": "A traditional daily cruiser with moderate cushioning, a medium fit, and outstanding outsole longevity. Its stable platform suits steady daily training and easy-to-moderate half marathon build-up runs.",
      "cons": "Feels heavy and lacks energetic rebound, with a steep 10 mm drop. Not ideal for runners wanting a responsive, bouncy ride."
    },
    {
      "model": "New Balance FuelCell Rebel v5",
      "brand": "New Balance",
      "foam_material": "PEBA-blended FuelCell (PEBA-blended)",
      "outsole_compound": "High-traction road rubber",
      "lug_depth": "0.0 mm",
      "drop": "6.3 mm",
      "stack": "33.0 mm heel / 26.7 mm forefoot",
      "weight": "7.9 oz / 225 g",
      "price": "$140",
      "pros": "Very lightweight and flexible with a bouncy supercritical-style feel and a secure Fantomfit upper. Great value for daily tempo work and half marathon-pace sessions.",
      "cons": "Weak toebox durability, and the foam may flatten quickly for heavier runners. Softer cushioning than a true medium-cushion ride."
    },
    {
      "model": "Asics Novablast 5",
      "brand": "Asics",
      "foam_material": "FF Blast MAX (supercritical)",
      "outsole_compound": "High-traction road rubber (0 mm)",
      "lug_depth": "0 mm",
      "drop": "7.4 mm",
      "stack": "40.9 mm heel / 33.5 mm forefoot",
      "weight": "9 oz / 255 g",
      "price": "$150",
      "pros": "A bouncy, energetic daily trainer with a medium fit that is friendly to wider feet and a flexible, dynamic ride. Handles daily runs and half marathon tempo blocks well.",
      "cons": "Toebox mesh durability is subpar and breathability can run warm in heat. Cushioning is maximal rather than medium."
    },
    {
      "model": "Hoka Arahi 8",
      "brand": "Hoka",
      "foam_material": "Traditional daily stability foam (not supercritical)",
      "outsole_compound": "Durable road rubber",
      "lug_depth": "0.0 mm lugs",
      "drop": "8 mm",
      "stack": "39.4 mm heel / 28.1 mm forefoot",
      "weight": "9 oz / 256 g",
      "price": "$150",
      "pros": "A lightweight, comfort-first daily trainer with balanced cushioning and a standard medium fit. Its H-Frame stability and smooth rocker suit easy daily training miles.",
      "cons": "Midsole lacks supercritical bounce and upper breathability is poor (2/5). Not recommended for hot-climate runners."
    }
  ],
  "tips": [
    "Test the fit in the afternoon, since feet swell over longer runs and a standard fit should leave room in the toebox.",
    "Rotate two daily trainers and reserve the most energetic option for tempo and half marathon-pace sessions to extend overall shoe life."
  ],
  "matched_race": null,
  "feedback_token": "5b0970617024839f3cf8dc390d891605.gear_finder.40264ca9bf6322a91d222c6c73053d60"
}
```
</details>
<details><summary>Captured baseline</summary>

```json
{
  "recommendations": [
    {
      "model": "Mach 7",
      "brand": "Hoka",
      "foam_material": "Balanced daily EVA-blend (EVA)",
      "outsole_compound": "Segmented road rubber",
      "lug_depth": "0.0 mm",
      "drop": "5 mm",
      "stack": "Heel 35.6 mm / Forefoot 26.2 mm",
      "weight": "8.5 oz / 241 g",
      "price": "$145",
      "pros": "Elite-level upper breathability and an exceptionally lightweight build. Provides an agile, forward-rolling rocker suitable for daily runs and tempos.",
      "cons": "The narrow fit may pinch wider toes, and the ride can feel firm to some."
    },
    {
      "model": "Aero Blaze 4",
      "brand": "Salomon",
      "foam_material": "Optifoam2 (eTPU)",
      "outsole_compound": "Road ContaGrip",
      "lug_depth": "None (road)",
      "drop": "8 mm",
      "stack": "36 mm heel / 28 mm forefoot",
      "weight": "8.0 oz / 226 g",
      "price": "$140",
      "pros": "Very lightweight with a snappy, bouncy eTPU midsole ride. Offers versatile performance for daily road miles and tempo paces at an approachable price.",
      "cons": "Narrow midfoot fit is not ideal for wider feet, and pure neutral geometry lacks inherent stability elements."
    },
    {
      "model": "Aero Blaze 3",
      "brand": "Salomon",
      "foam_material": "Optifoam2 (eTPU)",
      "outsole_compound": "Road rubber",
      "lug_depth": "Road (0.0 mm)",
      "drop": "8.0 mm",
      "stack": "35.0/27.0 mm",
      "weight": "7.9 oz / 223 g",
      "price": "$140",
      "pros": "Exceptionally lightweight build with soft and energetic bounce. Reverse camber geometry aids smooth transitions for daily miles and uptempo work.",
      "cons": "Lacks robust midfoot upper support, and heavier runners over 190-200 lbs may bottom out the foam."
    },
    {
      "model": "FuelCell Rebel v5",
      "brand": "New Balance",
      "foam_material": "PEBA-blended FuelCell (PEBA-blended)",
      "outsole_compound": "High-traction road rubber",
      "lug_depth": "0.0 mm",
      "drop": "6.3 mm",
      "stack": "33.0/26.7 mm",
      "weight": "7.9 oz / 225 g",
      "price": "$140",
      "pros": "Delivers an exceptionally lightweight and flexible ride powered by bouncy supercritical foam. Fantomfit upper locks down comfortably for daily miles and half-marathon pace work.",
      "cons": "Toebox durability is relatively weak, and the foam may compress too quickly under heavier runners."
    },
    {
      "model": "Pegasus 42",
      "brand": "Nike",
      "foam_material": "ReactX daily foam",
      "outsole_compound": "High-longevity road rubber",
      "lug_depth": "Road (0 mm)",
      "drop": "10.0 mm",
      "stack": "37.0/27.0 mm",
      "weight": "10.5 oz / 297 g",
      "price": "$145",
      "pros": "Dependable daily cruiser featuring a stable platform and outstanding outsole durability. Exceptionally soft and comfortable upper mesh built for daily wear.",
      "cons": "Feels relatively heavy and lacks energetic forefoot rebound."
    }
  ],
  "tips": [
    "For daily road training paired with half marathon prep, moderate-cushion trainers provide a sweet spot of impact protection without unnecessary bulk or mushiness.",
    "Be mindful of differing heel-to-toe drops; lower-drop options like 5-6 mm engage the calves and Achilles more, while 8-10 mm designs shift workload toward the knees and hips."
  ],
  "matched_race": null
}
```
</details>

## gear_fixture_road_to_trail_hybrid

- Gemini+KB latency: **14.0s** (baseline: 8.3s)
- Catalog membership: ✅ all recommendations exist in the distilled catalog

<details><summary>Gemini+KB output</summary>

```json
{
  "recommendations": [
    {
      "model": "Cascadia 19",
      "brand": "Brooks",
      "foam_material": "Nitrogen-infused EVA (EVA)",
      "outsole_compound": "TrailTack Green",
      "lug_depth": "4.0 mm",
      "drop": "6.0 mm",
      "stack": "35/29 mm",
      "weight": "10.7 oz / 303 g",
      "price": "$150",
      "pros": "A protective, predictable trainer for mixed gravel and hardpack routes, with a rock plate and a wide stable platform. Its medium-fit footprint suits standard width and door-to-trail transitions.",
      "cons": "It is heavy for daily road use and its wide base is overkill on smooth, flat surfaces."
    },
    {
      "model": "Peregrine 16",
      "brand": "Saucony",
      "foam_material": "Comfort trail foam with premium PWRRUN+ insole",
      "outsole_compound": "Vibram Megagrip",
      "lug_depth": "3.5 mm",
      "drop": "4.0 mm",
      "stack": "Heel 31.7 mm / Forefoot 26.9 mm",
      "weight": "9.6 oz / 271 g",
      "price": "$145",
      "pros": "Strong multi-terrain grip on gravel and hardpack with a secure lockdown and a stable base. It handles door-to-trail running well.",
      "cons": "Its narrow, tapered toebox may squeeze wide toes, so it is less ideal for standard-width feet that want more room."
    },
    {
      "model": "Ride 19",
      "brand": "Saucony",
      "foam_material": "High-energy daily foam",
      "outsole_compound": "XT-900 high-traction rubber",
      "lug_depth": "0.0 mm",
      "drop": "8.0 mm",
      "stack": "Heel 38.7 mm / Forefoot 30.2 mm",
      "weight": "9 oz / 255 g",
      "price": "$145",
      "pros": "A balanced, medium-cushioned daily trainer with a wide, stable landing platform and good breathability. It suits mixed road and packed-surface routes.",
      "cons": "It has limited outsole rubber coverage and no lugs, so it offers less grip on loose gravel."
    },
    {
      "model": "Endorphin Azura",
      "brand": "Saucony",
      "foam_material": "PWRRUN PB (PEBA)",
      "outsole_compound": "Exposed PWRRUN PB with XT-900 rubber patches",
      "lug_depth": "Not specified",
      "drop": "8 mm",
      "stack": "40/32 mm",
      "weight": "8.5 oz / 240 g",
      "price": "$150",
      "pros": "A lively, stable, lightweight cushioned trainer with a true-to-size fit and a normal-width option for men. It works well for mixed road and packed-surface runs.",
      "cons": "Its firm ride and outsole with exposed foam make it a less confident choice on loose gravel."
    },
    {
      "model": "Catamount 4",
      "brand": "Brooks",
      "foam_material": "Nitrogen-infused EVA (EVA)",
      "outsole_compound": "TrailTack Green",
      "lug_depth": "3.5 mm",
      "drop": "Not specified",
      "stack": "34 / 28 mm",
      "weight": "8.5 oz / 241 g",
      "price": "$170",
      "pros": "A light, locked-in trail shoe with versatile wet and dry traction that grips well on hardpack and gravel. It suits runners who want agile door-to-trail efforts.",
      "cons": "Its firm underfoot ride offers minimal plush comfort and may be fatiguing on long days, so it is less suited to medium cushioning preferences."
    }
  ],
  "tips": [
    "Try on shoes in the afternoon, when feet are slightly swollen, to confirm a standard-width fit before committing to a model.",
    "For door-to-trail runs, pair a grippier trail shoe like the Cascadia 19 or Peregrine 16 with a lighter road option like the Ride 19 to match each surface."
  ],
  "matched_race": null,
  "feedback_token": "0212f42cbc4b301dc66a1071cb39ea87.gear_finder.d236d05511e6c9d719eae2061291333c"
}
```
</details>
<details><summary>Captured baseline</summary>

```json
{
  "recommendations": [
    {
      "model": "Cascadia Elite",
      "brand": "Brooks",
      "foam_material": "PEBA foam",
      "outsole_compound": "Vibram Megagrip Elite",
      "lug_depth": "3.2 mm",
      "drop": "6.0 mm",
      "stack": "40/34 mm",
      "weight": "9.7 oz / 275 g",
      "price": "$275",
      "pros": "Pairs soft and responsive PEBA superfoam with protective plate technology. Ideal for gravel, hardpack, and road-to-trail hybrid transitions with elite wet/dry grip.",
      "cons": "Very expensive and features a narrower-fitting toebox with lower upper durability."
    },
    {
      "model": "Peregrine 16",
      "brand": "Saucony",
      "foam_material": "PWRRUN+ (EVA-blend)",
      "outsole_compound": "Vibram Megagrip",
      "lug_depth": "3.5 mm",
      "drop": "4.0 mm",
      "stack": "31.7 mm heel / 26.9 mm forefoot",
      "weight": "9.6 oz / 271 g",
      "price": "$145",
      "pros": "Delivers balanced, protective cushioning with versatile multi-terrain traction. Outstanding for hardpack, gravel paths, and light road transitions.",
      "cons": "The toe box tapers tightly up front, and it has gained slight weight over previous editions."
    },
    {
      "model": "Cascadia 19",
      "brand": "Brooks",
      "foam_material": "Nitrogen-infused EVA",
      "outsole_compound": "TrailTack Green",
      "lug_depth": "4.0 mm",
      "drop": "6.0 mm",
      "stack": "35/29 mm",
      "weight": "10.7 oz / 303 g",
      "price": "$150",
      "pros": "A predictable, stable workhorse offering moderate cushioning and excellent platform protection. Ideal for gravel and mixed surface cruising.",
      "cons": "Heavier overall build that can feel clunky if running extensive pavement miles."
    },
    {
      "model": "Catamount 4",
      "brand": "Brooks",
      "foam_material": "Nitrogen-infused EVA",
      "outsole_compound": "TrailTack Green",
      "lug_depth": "3.5 mm",
      "drop": "Not specified",
      "stack": "34 / 28 mm",
      "weight": "8.5 oz / 241 g",
      "price": "$170",
      "pros": "Lightweight, agile build designed for fast turnover on hardpack and light gravel trails. Features a dialed locked-in fit and dependable traction.",
      "cons": "Underfoot cushioning feels firmer and less plush on prolonged paved road stretches."
    },
    {
      "model": "Ride 19",
      "brand": "Saucony",
      "foam_material": "High-energy daily foam (EVA-blend)",
      "outsole_compound": "XT-900 high-traction rubber",
      "lug_depth": "0.0 mm",
      "drop": "8.0 mm",
      "stack": "38.7 mm heel / 30.2 mm forefoot",
      "weight": "9 oz / 255 g",
      "price": "$145",
      "pros": "Dependable road daily cruiser that comfortably handles smooth gravel and hardpack surfaces. Balanced cushioning provides a smooth, stable transition.",
      "cons": "Lacks trail lugs, making it unsuitable for loose dirt or muddy terrain."
    }
  ],
  "tips": [
    "When doing door-to-trail runs on gravel and hardpack, moderate lug depths between 3.0 mm and 3.5 mm provide the best balance of traction without causing instability on paved roads.",
    "If your route features mostly hard-packed crushed gravel, a protective daily road shoe with durable rubber can double as a capable door-to-trail hybrid."
  ],
  "matched_race": null
}
```
</details>

## gear_fixture_rock_plate_protection

- Gemini+KB latency: **15.8s** (baseline: 6.0s)
- Catalog membership: ✅ all recommendations exist in the distilled catalog

<details><summary>Gemini+KB output</summary>

```json
{
  "recommendations": [
    {
      "model": "Cascadia 19",
      "brand": "Brooks",
      "foam_material": "Nitrogen-infused (EVA)",
      "outsole_compound": "TrailTack Green",
      "lug_depth": "4.0 mm",
      "drop": "6.0 mm",
      "stack": "35/29 mm",
      "weight": "10.7 oz / 303 g",
      "price": "$150",
      "pros": "Protective rock plate and a wide, stable platform suit rocky and gravel terrain well. Its plush tongue and durable build make it a solid choice for protecting a bruised forefoot.",
      "cons": "It is very heavy and its wide base is overkill on smooth, flat trails."
    },
    {
      "model": "Mont Blanc Speed",
      "brand": "Altra",
      "foam_material": "Ego Pro core / Ego Max rim (EVA)",
      "outsole_compound": "Vibram Megagrip Litebase",
      "lug_depth": "3.0 mm",
      "drop": "0 mm",
      "stack": "29 mm heel & forefoot",
      "weight": "9.9 oz / 282 g",
      "price": "$185",
      "pros": "Lightweight TPU StoneGuard provides stone protection on fast trails. Its very soft midsole gives a comfortable ride.",
      "cons": "It has no true carbon plate and its upper and heel lock are insecure on steep, off-camber trails."
    },
    {
      "model": "S/Lab Genesis",
      "brand": "Salomon",
      "foam_material": "Energy Foam (EVA/OBC)",
      "outsole_compound": "Contagrip",
      "lug_depth": "4.3 mm",
      "drop": "7.8 mm",
      "stack": "31.9/24.1 mm",
      "weight": "9.1 oz / 258 g",
      "price": "$199",
      "pros": "Profeel rock plate and Kevlar-reinforced MATRYX upper suit technical rocky terrain and sharp rocks. Its secure custom lock and downhill control are strong for ultra racing.",
      "cons": "The foam lacks bounce and the shoe is expensive with upper wear concerns."
    },
    {
      "model": "Mount to Coast M1",
      "brand": "Mount to Coast",
      "foam_material": "JetCell Aliphatic TPU (A-TPU)",
      "outsole_compound": "Vibram MegaGrip Litebase",
      "lug_depth": "4.0 mm",
      "drop": "4 mm",
      "stack": "38/34 mm",
      "weight": "9.7 oz / 274 g",
      "price": "$195",
      "pros": "Flexible rock plate and high-energy JetCell foam suit long technical mountain ultras over rocky descents. Vibram grip and standard fit are well matched to a 50K.",
      "cons": "It is a newer brand to the trail market and its forefoot taper may feel snug for very wide feet."
    },
    {
      "model": "Terrex Agravic TT",
      "brand": "adidas",
      "foam_material": "Dual-layer Lightstrike Pro & Lightstrike (TPE/EVA)",
      "outsole_compound": "Continental Rubber",
      "lug_depth": "Aggressive lugs (depth not listed)",
      "drop": "8 mm",
      "stack": "39/31 mm",
      "weight": "10.2 oz / 290 g",
      "price": "$185",
      "pros": "Rock plate and stabilizing rod system give maximum protection on highly uneven, rocky trails. Max cushioning and plush heel support suit long distances.",
      "cons": "It is too bulky and bottom-heavy for runners who want agility."
    }
  ],
  "tips": [
    "Consider a rock plate plus a moderate-to-high stack to reduce forefoot bruising on sharp rocks, and test fit with the insole you plan to race in.",
    "For a 50K on rocky scree, pick the shoe with the most secure lockdown and consider a slight size up for swelling late in the race."
  ],
  "matched_race": null,
  "feedback_token": "4528a2ff0c50ebbe0f1111b696429489.gear_finder.5b61b0dadbb433b143f9d0974ece9f21"
}
```
</details>
<details><summary>Captured baseline</summary>

```json
{
  "recommendations": [
    {
      "model": "Cascadia 19",
      "brand": "Brooks",
      "foam_material": "Nitrogen-infused EVA",
      "outsole_compound": "TrailTack Green",
      "lug_depth": "4.0 mm",
      "drop": "6.0 mm",
      "stack": "35/29 mm",
      "weight": "10.7 oz / 303 g",
      "price": "$150",
      "pros": "Built specifically with a protective rock plate and an exceptionally stable platform for rocky, technical trails. Delivers predictable, durable protection for 50k and ultra-distance efforts.",
      "cons": "Heavy overall build and somewhat overkill for flat, smooth surfaces."
    },
    {
      "model": "Catamount 4",
      "brand": "Brooks",
      "foam_material": "Nitrogen-infused EVA",
      "outsole_compound": "TrailTack Green",
      "lug_depth": "3.5 mm",
      "drop": "Not specified",
      "stack": "34 / 28 mm",
      "weight": "8.5 oz / 241 g",
      "price": "$170",
      "pros": "Features a dedicated protective TPE plate to shield against sharp stones and scree. Offers locked-in agility and precise footing on steep, technical mountain terrain.",
      "cons": "Ride is firm with minimal plush padding, which can cause fatigue over ultra-long distances."
    },
    {
      "model": "Peregrine 16",
      "brand": "Saucony",
      "foam_material": "Comfort trail foam with premium PWRRUN+ insole",
      "outsole_compound": "Vibram Megagrip",
      "lug_depth": "3.5 mm",
      "drop": "4.0 mm",
      "stack": "31.7 mm heel / 26.9 mm forefoot",
      "weight": "9.6 oz / 271 g",
      "price": "$145",
      "pros": "Equipped with an integrated rock plate to deflect sharp rock bruising on technical courses. Delivers exceptional Vibram Megagrip traction and moderate, protective cushioning.",
      "cons": "Narrow tapered forefoot limits wide toe splay and the shoe has gained slight weight over past versions."
    },
    {
      "model": "Trabuco 14",
      "brand": "Asics",
      "foam_material": "FF Blast Max (supercritical)",
      "outsole_compound": "ASICSGRIP",
      "lug_depth": "3.7 mm",
      "drop": "8 mm",
      "stack": "32.1/25.8 mm",
      "weight": "9.9 oz / 281 g",
      "price": "$145",
      "pros": "Features a built-in rock plate to safeguard against aggressive stone strikes. Provides reliable, stable ASICSGRIP traction and balanced moderate cushioning for rugged trails.",
      "cons": "Runs slightly heavy and the low collar may allow trail scree to enter."
    },
    {
      "model": "S/Lab Genesis 2",
      "brand": "Salomon",
      "foam_material": "Dual-density OptiFoam2 (eTPU)",
      "outsole_compound": "All-Terrain Contagrip with revised wet-rock lug geometry",
      "lug_depth": "4.5 mm",
      "drop": "6 mm",
      "stack": "31 mm heel / 25 mm forefoot",
      "weight": "9.3 oz / 264 g",
      "price": "$200",
      "pros": "Incorporates a Profeel Film rock filter to absorb sharp stone impacts over rocky alpine descents. Provides precision handling, activeCHASSIS stability, and a bombproof Matryx upper.",
      "cons": "Premium price point and a low-to-moderate stack designed strictly for agile racing rather than plush cushioning."
    }
  ],
  "tips": [
    "To fully protect against bruised forefeet on sharp rocks and scree, ensure your chosen shoe incorporates an embedded rock plate or protective film filter beneath the ball of the foot.",
    "Pair your rock-plated shoes with gaiters or tall technical socks on scree-heavy 50ks to prevent small stones and debris from slipping past the ankle collar."
  ],
  "matched_race": null
}
```
</details>

## gear_fixture_technical_mud_skyrace

- Gemini+KB latency: **14.0s** (baseline: 7.1s)
- Catalog membership: ✅ all recommendations exist in the distilled catalog

<details><summary>Gemini+KB output</summary>

```json
{
  "recommendations": [
    {
      "model": "Genesis 2",
      "brand": "Salomon",
      "foam_material": "OptiFoam (EVA / Olefin block copolymer)",
      "outsole_compound": "All-Terrain ContaGrip",
      "lug_depth": "4.5 mm",
      "drop": "8 mm",
      "stack": "34 mm heel / 26 mm forefoot",
      "weight": "9.6 oz / 264 g",
      "price": "$150",
      "pros": "Strong grip on mud and wet rock with a bombproof Matryx upper suited to technical terrain. Its balanced, moderate cushioning and standard fit match your width and low-cushion preference for a 25k skyrace.",
      "cons": "Its 4.5 mm lugs are less aggressive than the Speedcross 6 for deep mud. It is not as bouncy as PEBA super-shoes."
    },
    {
      "model": "S/Lab Genesis",
      "brand": "Salomon",
      "foam_material": "Energy Foam (EVA/OBC)",
      "outsole_compound": "Contagrip",
      "lug_depth": "4.3 mm",
      "drop": "7.8 mm",
      "stack": "31.9/24.1 mm",
      "weight": "9.1 oz / 258 g",
      "price": "$199",
      "pros": "Lower-stack, moderate cushioning with a secure fit and strong downhill control on steep, technical mud. It is a good option for a fast skyrace with significant climbing and descent.",
      "cons": "Its foam lacks bounce and the upper can wear quickly. It is expensive and its fit leans toward a medium-secure rather than fully standard volume."
    },
    {
      "model": "S/Lab Genesis 2",
      "brand": "Salomon",
      "foam_material": "Dual-density OptiFoam2 (eTPU)",
      "outsole_compound": "All-Terrain Contagrip with revised wet-rock lug geometry",
      "lug_depth": "4.5 mm",
      "drop": "6 mm",
      "stack": "31 mm heel / 25 mm forefoot",
      "weight": "9.3 oz / 264 g",
      "price": "$200",
      "pros": "Low stack and precise ground feel with bouncy, longer-lasting foam for steep, technical racing. Its activeCHASSIS stability helps on off-camber terrain during a 25k with 2000m D+.",
      "cons": "Its snug S/Lab race fit is narrower than a standard fit. It is a premium price for a shoe with less cushioning than some alternatives."
    },
    {
      "model": "Speedcross 6",
      "brand": "Salomon",
      "foam_material": "EnergyCell+ (EVA)",
      "outsole_compound": "Mud Contagrip",
      "lug_depth": "5.8 mm",
      "drop": "14.1 mm",
      "stack": "36.5/22.4 mm",
      "weight": "10.5 oz / 298 g",
      "price": "$145",
      "pros": "The most aggressive lugs in the catalog, with excellent mud shedding and agile cornering on steep, muddy climbs. It is durable and a strong choice for rugged mud-focused racing.",
      "cons": "Its firm, concrete-like ride conflicts with a low-cushion preference and it is heavy. Breathability is poor, and it suits heel strikers rather than forefoot strikers."
    },
    {
      "model": "Genesis",
      "brand": "Salomon",
      "foam_material": "Energy Foam (EVA/OBC)",
      "outsole_compound": "Contagrip",
      "lug_depth": "4.0 mm",
      "drop": "9.0 mm",
      "stack": "33.5/24.5 mm",
      "weight": "9.7 oz / 275 g",
      "price": "$150",
      "pros": "Superb platform stability with a roomy, standard-feeling fit and flexible, moderate cushioning. It handles rocky technical ground and long climbs well.",
      "cons": "Its outsole wears down quickly and its lugs are shallower than the aggressive options. It has a high drop and lacks reflective elements."
    }
  ],
  "tips": [
    "Consider the Speedcross 6 for the mud and steep climbs, but test its firm midsole on a long run before race day.",
    "For a skyrace with 2000m D+, prioritize the Genesis 2 or S/Lab Genesis 2 for the best balance of grip, stability and low cushioning; no catalog shoe has lugs deeper than 5.8 mm, so the Speedcross 6 is the most aggressive option."
  ],
  "matched_race": null,
  "feedback_token": "28853a178e6bf1964413a67bce1b3564.gear_finder.7dfbcdc20f5d20b8bb2ccf9cd1cfc110"
}
```
</details>
<details><summary>Captured baseline</summary>

```json
{
  "recommendations": [
    {
      "model": "Speedcross 6",
      "brand": "Salomon",
      "foam_material": "EnergyCell+ (EVA)",
      "outsole_compound": "Mud Contagrip",
      "lug_depth": "5.8 mm",
      "drop": "14.1 mm",
      "stack": "36.5/22.4 mm",
      "weight": "10.5 oz / 298 g",
      "price": "$145",
      "pros": "Exceptional claw-like grip built specifically for steep mud and loose, technical conditions. Offers unrivaled mud shedding and supreme agility when carving through rugged alpine terrain.",
      "cons": "The ride is remarkably firm and concrete-like, and upper breathability is poor in warmer conditions."
    },
    {
      "model": "S/Lab Genesis 2",
      "brand": "Salomon",
      "foam_material": "Dual-density OptiFoam2 (eTPU)",
      "outsole_compound": "All-Terrain Contagrip with revised wet-rock lug geometry",
      "lug_depth": "4.5 mm",
      "drop": "6 mm",
      "stack": "31 mm heel / 25 mm forefoot",
      "weight": "9.3 oz / 264 g",
      "price": "$200",
      "pros": "Delivers outstanding low-stack ground feel and precise foot placement across technical mountain ridgelines. Built with reengineered activeCHASSIS stability and an indestructible Matryx upper.",
      "cons": "Low-to-moderate stack focuses heavily on ground feedback over soft cushion, and the precision race fit can feel narrow."
    },
    {
      "model": "S/Lab Genesis",
      "brand": "Salomon",
      "foam_material": "Energy Foam (EVA/OBC)",
      "outsole_compound": "Contagrip",
      "lug_depth": "4.3 mm",
      "drop": "7.8 mm",
      "stack": "31.9/24.1 mm",
      "weight": "9.1 oz / 258 g",
      "price": "$199",
      "pros": "Exceptionally lightweight with a secure lock tailored for rapid technical descents. Features low shock absorption and direct ground feel alongside protective Matryx durability.",
      "cons": "Midsole foam lacks energetic bounce, and outsole lugs can wear down quickly on abrasive rock."
    },
    {
      "model": "Genesis 2",
      "brand": "Salomon",
      "foam_material": "OptiFoam (EVA / Olefin block copolymer)",
      "outsole_compound": "All-Terrain ContaGrip",
      "lug_depth": "4.5 mm",
      "drop": "8 mm",
      "stack": "34 mm heel / 26 mm forefoot",
      "weight": "9.6 oz / 264 g",
      "price": "$150",
      "pros": "Great grip on mud and slick rock with deep 4.5 mm lugs. Provides confidence-inspiring Active Chassis stability combined with a tear-resistant Matryx upper.",
      "cons": "Lacks the springy pop of super-critical racing foams, and the Quicklace lace garage can be difficult to use."
    },
    {
      "model": "Genesis",
      "brand": "Salomon",
      "foam_material": "Energy Foam (EVA/OBC)",
      "outsole_compound": "Contagrip",
      "lug_depth": "4.0 mm",
      "drop": "9.0 mm",
      "stack": "33.5/24.5 mm",
      "weight": "9.7 oz / 275 g",
      "price": "$150",
      "pros": "Provides superb platform stability and rock protection for high-elevation, technical terrain. Highly breathable with a protective Kevlar-infused upper.",
      "cons": "The 9.0 mm drop is relatively steep for pure forefoot climbing, and outsole durability is slightly below average."
    }
  ],
  "tips": [
    "For a steep 2000m D+ skyrace with mud and loose scree, deeper lugs (such as the 5.8 mm chevrons on the Speedcross 6 or 4.5 mm on the S/Lab Genesis 2) will provide crucial bite on both steep climbs and precipitous descents.",
    "Choose a lower-stack, firm-to-balanced platform to maintain agile proprioception and avoid ankle roll on off-camber technical slopes."
  ],
  "matched_race": null
}
```
</details>

## gear_fixture_trail_hoka

- Gemini+KB latency: **12.3s** (baseline: 4.5s)
- Catalog membership: ✅ all recommendations exist in the distilled catalog

<details><summary>Gemini+KB output</summary>

```json
{
  "recommendations": [
    {
      "model": "Mafate 5",
      "brand": "Hoka",
      "foam_material": "Supercritical EVA (EVA)",
      "outsole_compound": "Vibram Megagrip with asymmetric chevrons",
      "lug_depth": "4.4 mm",
      "drop": "9.0 mm",
      "stack": "42.9/33.9 mm",
      "weight": "11.7 oz / 332 g",
      "price": "$185",
      "pros": "Max cushioning and a roomy, medium fit with superb joint protection suit long, muddy ultra days. Its tall, stable platform and durable build suit high-mileage technical efforts.",
      "cons": "Heavy and bulky, with a non-gusseted tongue and a stiff feel. It is the heaviest option here for a 50K race."
    },
    {
      "model": "Speedgoat 7",
      "brand": "Hoka",
      "foam_material": "Supercritical EVA (EVA)",
      "outsole_compound": "Vibram Megagrip",
      "lug_depth": "5.0 mm",
      "drop": "5.0 mm",
      "stack": "37.0/32.0 mm",
      "weight": "9.55 oz / 271 g",
      "price": "$165",
      "pros": "Max cushioning with a secure woven fit and deep 5.0 mm lugs gives strong wet and mud traction on rugged, technical trails. It is lighter than the Mafate 5 and well suited to 50K distances.",
      "cons": "Runs slightly short, so sizing up half a size is advised. Its tall stack can feel clunky on very technical terrain."
    },
    {
      "model": "Tecton X 4",
      "brand": "Hoka",
      "foam_material": "Dual-density PEBA",
      "outsole_compound": "Vibram Megagrip Litebase with Traction Lug",
      "lug_depth": "4.0 mm",
      "drop": "5 mm",
      "stack": "40 mm heel / 35 mm forefoot",
      "weight": "9.2 oz / 261 g",
      "price": "$275",
      "pros": "Max cushioning with dual PEBA foam, a standard fit, and a secure Matryx upper gives strong energy return for a 50K. It is the lightest Hoka option here.",
      "cons": "At $275 it exceeds the $200 budget. Its lighter lug depth provides less mud bite than the Speedgoat 7."
    },
    {
      "model": "Tecton X 3",
      "brand": "Hoka",
      "foam_material": "PEBA foam (PEBA)",
      "outsole_compound": "Vibram Megagrip Litebase with asymmetric chevrons",
      "lug_depth": "4.0 mm",
      "drop": "6.9 mm",
      "stack": "37.8/30.9 mm",
      "weight": "10.3 oz / 292 g",
      "price": "$275",
      "pros": "Max cushioning with PEBA foam, parallel carbon plates, and an integrated ankle gaiter that shields debris, useful for muddy courses.",
      "cons": "At $275 it exceeds the $200 budget. It has a narrow snug fit and is not suited to standard-width feet."
    }
  ],
  "tips": [
    "The catalog contains only four Hoka trail shoes, so this list includes all Hoka options; the Tecton X models exceed the $200 budget and the Speedgoat 7 is the best value match.",
    "For muddy, technical 50K courses, prioritize the Speedgoat 7's 5.0 mm lugs and Vibram Megagrip outsole, and size up a half size for comfort."
  ],
  "matched_race": null,
  "feedback_token": "30a13b2b114b1ee1ad4b7757aa3788e3.gear_finder.c85d4b37c5aef0d97520a40ceac20986"
}
```
</details>
<details><summary>Captured baseline</summary>

```json
{
  "recommendations": [
    {
      "model": "Speedgoat 7",
      "brand": "Hoka",
      "foam_material": "Supercritical EVA (EVA)",
      "outsole_compound": "Vibram Megagrip",
      "lug_depth": "5.0 mm with Traction Lug",
      "drop": "5.0 mm",
      "stack": "37.0/32.0 mm",
      "weight": "9.55 oz / 271 g",
      "price": "$165",
      "pros": "Responsive fresh-legs cushioning and outstanding Vibram wet/dry traction for rugged trails. The 5.0 mm Traction Lugs excel in mud, loose dirt, and technical roots.",
      "cons": "Tall stack can feel somewhat clunky on off-camber technical sections, and the fit runs slightly short."
    },
    {
      "model": "Mafate 5",
      "brand": "Hoka",
      "foam_material": "Supercritical EVA (EVA)",
      "outsole_compound": "Vibram Megagrip with asymmetric chevrons",
      "lug_depth": "4.4 mm",
      "drop": "9.0 mm",
      "stack": "42.9/33.9 mm",
      "weight": "11.7 oz / 332 g",
      "price": "$185",
      "pros": "A maximalist trail workhorse providing endless joint protection and high platform stability. Grippy 4.4 mm chevron lugs bite securely into mixed and muddy off-trail surfaces.",
      "cons": "Heavy and bulky underfoot compared to pure race shoes, and the non-gusseted tongue design may require adjustment."
    }
  ],
  "tips": [
    "Hoka's catalog contains only two trail models meeting your max cushion, technical trail, and under-$200 budget criteria: the Speedgoat 7 and Mafate 5.",
    "For technical 50K distances with mud, consider sizing up a half-size in the Speedgoat 7 to account for foot swelling and its slightly short fit."
  ],
  "matched_race": null
}
```
</details>

## gear_fixture_ultra_100mile

- Gemini+KB latency: **17.0s** (baseline: 6.5s)
- Catalog membership: ✅ all recommendations exist in the distilled catalog

<details><summary>Gemini+KB output</summary>

```json
{
  "recommendations": [
    {
      "model": "055",
      "brand": "Norda",
      "foam_material": "Arnitel TPEE (TPEE)",
      "outsole_compound": "Vibram Megagrip Elite",
      "lug_depth": "4.5 mm (knobs to 7 mm)",
      "drop": "7 mm",
      "stack": "38 mm heel / 31 mm forefoot",
      "weight": "11.6 oz / 330 g",
      "price": "$325",
      "pros": "Max cushioning with an accommodating forefoot that suits swelling feet, built for 100+ mile races and technical terrain. Its Vibram Megagrip Elite outsole grips well on mixed and hardpack surfaces.",
      "cons": "It is the heaviest option here and its midfoot lockdown can loosen on technical terrain. Heel rubbing on steep climbs has been reported."
    },
    {
      "model": "S/Lab Ultra Glide 2",
      "brand": "Salomon",
      "foam_material": "Dual-layer OptiFoam+ (top) and OptiFoam midsole (foam type not specified in catalog)",
      "outsole_compound": "All-Terrain ContaGrip",
      "lug_depth": "4.0 mm",
      "drop": "6 mm",
      "stack": "41 mm heel / 35 mm forefoot",
      "weight": "10.4 oz / 295 g",
      "price": "$250",
      "pros": "Max-cushion race-day shoe with a broad, generous forefoot that tapers through the midfoot and heel. It is built for long-distance trail racing on varied terrain and offers good stability for its stack height.",
      "cons": "It is still somewhat heavy for a race shoe and the QuickLace pocket can be awkward to use. Heel rubbing may occur before break-in."
    },
    {
      "model": "Cloudultra Pro",
      "brand": "On",
      "foam_material": "Helion HF (Pebax-based superfoam)",
      "outsole_compound": "Missiongrip",
      "lug_depth": "3.5 mm",
      "drop": "6 mm",
      "stack": "38.5 mm heel / 32.5 mm forefoot",
      "weight": "9.3 oz / 265 g",
      "price": "$260",
      "pros": "Lightest of the max-cushion picks, with a roomy, accommodating fit and strong energy return for 100-mile race day. Its debris-defending collar and bouncy ride suit long trail efforts.",
      "cons": "At $260 it is pricey, and lacing or heel security can be quirky. Lateral stability is reduced on extreme technical terrain."
    },
    {
      "model": "Fuga EX330",
      "brand": "Kailas",
      "foam_material": "Supercritical foam (EVA)",
      "outsole_compound": "Vibram Megagrip",
      "lug_depth": "6.0 mm (side) / 4.0 mm (center/rear)",
      "drop": "5 mm",
      "stack": "39 mm heel / 34 mm forefoot",
      "weight": "10.1 oz / 285 g",
      "price": "$200",
      "pros": "Max cushioning with a roomy toebox and a secure midfoot and heel hold, which helps with swelling over long days. It is a protective, well-priced option for technical ultras.",
      "cons": "It is relatively heavy and not suited to weight-conscious racers. The deep side lugs may feel aggressive on smoother hardpack."
    },
    {
      "model": "Cadi",
      "brand": "NNormal",
      "foam_material": "Supercritical foam midsole (foam type not specified in catalog)",
      "outsole_compound": "Vibram Megagrip, full underfoot coverage",
      "lug_depth": "3.5-4.0 mm",
      "drop": "6 mm",
      "stack": "35 mm heel / 29 mm forefoot",
      "weight": "10.1 oz / 286 g",
      "price": "$175",
      "pros": "NNormal's most cushioned shoe, with a generous, wider toe box and broad platform that suits swelling feet over 12-plus hours. It offers dependable comfort for ultra races on mixed and smooth trails.",
      "cons": "Its midsole lacks a springy, energetic feel and it runs heavier than expected. It is less suited to very rocky or technical courses."
    }
  ],
  "tips": [
    "Buy half to a full size up in race-day shoes, since feet swell after 12 hours and the toe box needs room to accommodate it.",
    "Test your race shoes on a long run or a simulated late-day run, and keep lacing loose on the forefoot to relieve pressure as your feet expand."
  ],
  "matched_race": null,
  "feedback_token": "350cf9d123ec93fe15d0e7762a36b004.gear_finder.89a331ad15a73171d60037edd85e7175"
}
```
</details>
<details><summary>Captured baseline</summary>

```json
{
  "recommendations": [
    {
      "model": "055",
      "brand": "Norda",
      "foam_material": "Arnitel TPEE",
      "outsole_compound": "Vibram Megagrip Elite",
      "lug_depth": "4.5 mm",
      "drop": "7 mm",
      "stack": "38 mm heel / 31 mm forefoot",
      "weight": "11.6 oz / 330 g",
      "price": "$325",
      "pros": "Delivers incredible maximal cushion and underfoot protection for 100+ mile races. The accommodating forefoot gives swelling toes ample room over long hours. Features top-tier Vibram Megagrip Elite traction paired with an indestructible Dyneema upper.",
      "cons": "Heavier than standard racing flats and can cause minor heel rubbing on steep ascents."
    },
    {
      "model": "Cadi",
      "brand": "NNormal",
      "foam_material": "Supercritical foam",
      "outsole_compound": "Vibram Megagrip",
      "lug_depth": "3.5-4.0 mm",
      "drop": "6 mm",
      "stack": "35 mm heel / 29 mm forefoot",
      "weight": "10.1 oz / 286 g",
      "price": "$175",
      "pros": "Built on a wider toe box inspired by the Kjerag to easily handle foot swelling. Offers all-day protective max/moderate cushioning designed specifically for long ultra races. Provides full Vibram Megagrip underfoot security across smooth and mixed hardpack trails.",
      "cons": "The supercritical midsole lacks a hyper-bouncy feel and runs slightly heavier than expected."
    },
    {
      "model": "M1",
      "brand": "Mount to Coast",
      "foam_material": "JetCell Aliphatic TPU (A-TPU)",
      "outsole_compound": "Vibram MegaGrip Litebase",
      "lug_depth": "4.0 mm",
      "drop": "4 mm",
      "stack": "38 mm heel / 34 mm forefoot",
      "weight": "9.7 oz / 274 g",
      "price": "$195",
      "pros": "Super high-energy return JetCell A-TPU foam resists long-haul fatigue during ultra distances. TunedFit dual-zone lacing allows easy mid-race adjustments when feet begin to swell. Excellent 38 mm stack provides deep impact absorption.",
      "cons": "Forefoot taper might feel snug for ultra-wide feet, and the brand is relatively new to the trail scene."
    },
    {
      "model": "Terrex Agravic Speed Ultra 2",
      "brand": "adidas",
      "foam_material": "Lightstrike Pro (TPE)",
      "outsole_compound": "Continental Rubber",
      "lug_depth": "4 mm",
      "drop": "8 mm",
      "stack": "44 mm heel / 36 mm forefoot",
      "weight": "9.35 oz / 265 g",
      "price": "$225",
      "pros": "Max-stack 44 mm platform designed for elite propulsion and fatigue resistance in 100-mile ultras. Dynamic TPE Energy Rods keep turnover efficient on runnable, mixed hardpack terrain. Continental rubber provides dependable traction across various surfaces.",
      "cons": "The rocker profile and high stack require strong ankle stability on off-camber sections."
    },
    {
      "model": "MetaFuji Trail 2",
      "brand": "Asics",
      "foam_material": "FF Leap (PEBA) & FF Blast Plus (EVA)",
      "outsole_compound": "ASICSGRIP",
      "lug_depth": "4.5 mm",
      "drop": "5 mm",
      "stack": "41.5 mm heel / 36.5 mm forefoot",
      "weight": "9.0 oz / 255 g",
      "price": "$280",
      "pros": "Features a towering 41.5 mm dual-superfoam stack that preserves leg freshness over 100 miles. Full-length carbon plate generates effortless propulsion on rolling, hardpack trails. Grippy ASICSGRIP outsole handles diverse terrain with ease.",
      "cons": "Priced at a steep $280 and can feel tippy on sharp technical descents."
    }
  ],
  "tips": [
    "Since your feet swell substantially after 12 hours, consider sizing up by a half size or swapping to thinner performance socks at a late-race drop bag.",
    "Utilize dual-zone lacing systems or loosen the lower eyelets midway through the race to ease forefoot pressure while keeping your heel locked in."
  ],
  "matched_race": null
}
```
</details>

## gear_fixture_vmm_vietnam_mountain

- Gemini+KB latency: **14.9s** (baseline: 6.3s)
- Catalog membership: ✅ all recommendations exist in the distilled catalog

<details><summary>Gemini+KB output</summary>

```json
{
  "recommendations": [
    {
      "model": "Speedgoat 7",
      "brand": "Hoka",
      "foam_material": "Supercritical EVA (EVA)",
      "outsole_compound": "Vibram Megagrip",
      "lug_depth": "5.0 mm",
      "drop": "5.0 mm",
      "stack": "37.0/32.0 mm",
      "weight": "9.55 oz / 271 g",
      "price": "$165",
      "pros": "Max cushioning with a responsive nitrogen-infused midsole and outstanding Vibram wet/dry traction for rocks and roots. The secure woven fit suits standard-width feet on rugged technical terrain.",
      "cons": "The tall stack can feel clunky on very technical ground, and the shoe runs slightly short, so sizing up half a size is advised."
    },
    {
      "model": "Timp 6",
      "brand": "Altra",
      "foam_material": "Ego Max (foam type not specified in catalog)",
      "outsole_compound": "Vibram Megagrip",
      "lug_depth": "3.5 mm",
      "drop": "0 mm",
      "stack": "30 mm",
      "weight": "11.45 oz / 324 g",
      "price": "$165",
      "pros": "High, protective cushioning with excellent drainage and outstanding wet/dry Vibram grip for mud, snow, and wet rock. Its standard FootShape roomy toe box fits standard-width feet well.",
      "cons": "It is heavy for its class, and the lower heel counter can allow heel slippage."
    },
    {
      "model": "Mount to Coast T1",
      "brand": "Mount to Coast",
      "foam_material": "Lightcell foam (foam type not specified in catalog)",
      "outsole_compound": "Vibram Megagrip Litebase",
      "lug_depth": "4.0 mm",
      "drop": "4 mm",
      "stack": "36/32 mm",
      "weight": "9.2 oz / 260 g",
      "price": "$180",
      "pros": "Soft, structured cushioning with excellent wet/dry Vibram grip, built for technical rocky singletrack and ultra distances like a 70k. Its standard fit with relaxed toe splay matches a standard-width request.",
      "cons": "The TunedFit pull-cord lacing can be finicky to dial in on changing terrain."
    },
    {
      "model": "Genesis 2",
      "brand": "Salomon",
      "foam_material": "OptiFoam (EVA / Olefin block copolymer)",
      "outsole_compound": "All-Terrain ContaGrip",
      "lug_depth": "4.5 mm",
      "drop": "8 mm",
      "stack": "34/26 mm",
      "weight": "9.6 oz / 264 g",
      "price": "$150",
      "pros": "A bombproof technical mountain trainer with aggressive grip on mud and wet rock and a balanced cushion suited to rugged ultra terrain. It is a strong value at $150 with a standard fit.",
      "cons": "It is less bouncy than PEBA super-shoes, and the Quicklace garage can feel snug."
    },
    {
      "model": "Catamount 4",
      "brand": "Brooks",
      "foam_material": "Nitrogen-infused EVA (EVA)",
      "outsole_compound": "TrailTack Green",
      "lug_depth": "3.5 mm",
      "drop": "Not listed in catalog",
      "stack": "34/28 mm",
      "weight": "8.5 oz / 241 g",
      "price": "$170",
      "pros": "Versatile wet/dry traction that grips wet leaves, snow, and ice, with a locked-in agile fit for steep, technical, rocky trails. It is the lightest option on this list.",
      "cons": "Its firm ride offers less plush cushioning than requested and can be fatiguing on ultra-long days."
    }
  ],
  "tips": [
    "For a 70k on muddy, technical, wet-rock terrain, prioritize outsoles like Vibram Megagrip or ContaGrip and consider a shoe with a secure heel lock to limit slippage on descents.",
    "Try shoes on with the socks and insoles you plan to race in, and size up a half size if you have wider feet or expect swelling on long efforts."
  ],
  "matched_race": null,
  "feedback_token": "6e86d2b8176104e2dd2dd2cb44dc5807.gear_finder.04f9a9c35455889bebaf98096aae4e5e"
}
```
</details>
<details><summary>Captured baseline</summary>

```json
{
  "recommendations": [
    {
      "model": "Timp 6",
      "brand": "Altra",
      "foam_material": "Ego Max (EVA)",
      "outsole_compound": "Vibram Megagrip",
      "lug_depth": "3.5 mm",
      "drop": "0 mm",
      "stack": "30 mm",
      "weight": "11.45 oz / 324 g",
      "price": "$165",
      "pros": "Outstanding wet and dry Vibram traction that easily sheds mud, snow, and trail debris. Delivers nimble and high protective cushioning well-suited for ultra-distance races.",
      "cons": "The lower heel counter design can cause heel slippage inside the roomy toe box."
    },
    {
      "model": "Genesis 2",
      "brand": "Salomon",
      "foam_material": "OptiFoam (EVA / Olefin block copolymer)",
      "outsole_compound": "All-Terrain ContaGrip",
      "lug_depth": "4.5 mm",
      "drop": "8 mm",
      "stack": "34 mm heel / 26 mm forefoot",
      "weight": "9.6 oz / 264 g",
      "price": "$150",
      "pros": "Features aggressive 4.5 mm lugs that grip exceptionally well across mud, technical roots, and wet rocks. Bombproof Matryx upper and Active Chassis provide great stability over 70k ultra terrain.",
      "cons": "Lacks the springy energy return found in modern PEBA super-shoes."
    },
    {
      "model": "Speedgoat 7",
      "brand": "Hoka",
      "foam_material": "Supercritical EVA (EVA)",
      "outsole_compound": "Vibram Megagrip",
      "lug_depth": "5.0 mm with Traction Lug",
      "drop": "5.0 mm",
      "stack": "37.0/32.0 mm",
      "weight": "9.55 oz / 271 g",
      "price": "$165",
      "pros": "Deep 5.0 mm Vibram Traction Lugs provide dependable grip over technical, rugged, and muddy paths. Maximum supercritical cushioning keeps legs fresh across high-mileage mountain ultras.",
      "cons": "The towering stack can feel disconnected on tight technical sections, and the fit runs slightly short."
    },
    {
      "model": "Tomir 2.0",
      "brand": "NNormal",
      "foam_material": "EExpure supercritical foam",
      "outsole_compound": "Vibram Megagrip Litebase",
      "lug_depth": "5.0 mm",
      "drop": "8 mm",
      "stack": "Not specified",
      "weight": "9.9 oz / 280 g",
      "price": "$170",
      "pros": "Incredible traction and bite in slick conditions like mud, streams, and wet granite thanks to 5.0 mm Vibram lugs. Highly durable design built to withstand rugged ultra training and racing.",
      "cons": "The slim Ripstop TPE upper is not accommodating for wider feet and can run warm in humid weather."
    },
    {
      "model": "Trabuco 14",
      "brand": "Asics",
      "foam_material": "FF Blast Max (supercritical)",
      "outsole_compound": "ASICSGRIP",
      "lug_depth": "3.7 mm",
      "drop": "8 mm",
      "stack": "32.1/25.8 mm",
      "weight": "9.9 oz / 281 g",
      "price": "$145",
      "pros": "Aggressive chevrons and ASICSGRIP deliver elite wet and dry traction on slippery surfaces. Includes a protective rock plate and durable cushioning suited for rugged ultra distances.",
      "cons": "The shoe runs slightly heavy and the low collar can let in loose trail debris."
    }
  ],
  "tips": [
    "For a 70k race across mud and wet rock, prioritize deep lug patterning (4.0 mm to 5.0 mm) paired with proven sticky compounds like Vibram Megagrip or ASICSGRIP.",
    "Ensure your shoe selection allows slight forefoot swelling space while keeping the midfoot and heel securely locked down to avoid blisters on steep technical descents."
  ],
  "matched_race": null
}
```
</details>

## gear_fixture_wide_feet_trail

- Gemini+KB latency: **15.5s** (baseline: 6.5s)
- Catalog membership: ✅ all recommendations exist in the distilled catalog

<details><summary>Gemini+KB output</summary>

```json
{
  "recommendations": [
    {
      "model": "Trabuco 14",
      "brand": "Asics",
      "foam_material": "FF Blast Max (supercritical)",
      "outsole_compound": "ASICSGRIP",
      "lug_depth": "3.7 mm",
      "drop": "8 mm",
      "stack": "32.1/25.8 mm",
      "weight": "9.9 oz / 281 g",
      "price": "$145",
      "pros": "Wide fit with roomy toebox and superb rock splay, plus elite wet/dry grip for rocky and hardpack trails. Its rock plate and stable platform suit a 30k effort on varied terrain.",
      "cons": "Fairly heavy, with a low ankle collar that admits trail debris and hit-or-miss lacing. Not ideal for those wanting a lighter, faster shoe."
    },
    {
      "model": "Cascadia 19",
      "brand": "Brooks",
      "foam_material": "Nitrogen-infused EVA (EVA)",
      "outsole_compound": "TrailTack Green",
      "lug_depth": "4.0 mm",
      "drop": "6.0 mm",
      "stack": "35/29 mm",
      "weight": "10.7 oz / 303 g",
      "price": "$150",
      "pros": "Medium fit with a wide option, a protective rock plate, and a stable platform suited to rocky and gravel trails. Its moderate cushioning fits the medium cushioning request for a 30k.",
      "cons": "Very heavy, and the wide base is overkill for smooth, flat trails. Not a speedy choice for racing."
    },
    {
      "model": "Genesis",
      "brand": "Salomon",
      "foam_material": "Energy Foam (EVA/OBC)",
      "outsole_compound": "Contagrip",
      "lug_depth": "4.0 mm",
      "drop": "9.0 mm",
      "stack": "33.5/24.5 mm",
      "weight": "9.7 oz / 275 g",
      "price": "$150",
      "pros": "Roomy, accommodating fit with superb platform stability and a rocky technical capability. Balanced cushioning suits medium cushioning needs on rocky and hardpack terrain.",
      "cons": "Outsole wears down quickly and the drop is high. Not for heavy forefoot strikers."
    },
    {
      "model": "Mount to Coast T1",
      "brand": "Mount to Coast",
      "foam_material": "Lightcell foam",
      "outsole_compound": "Vibram Megagrip Litebase",
      "lug_depth": "4.0 mm",
      "drop": "4 mm",
      "stack": "36/32 mm",
      "weight": "9.2 oz / 260 g",
      "price": "$180",
      "pros": "Standard fit with roomy, relaxed toe splay and strong Vibram grip on rocky singletrack. Soft structured cushioning and durability suit a 30k on rocky and hardpack ground.",
      "cons": "TunedFit pull-cord lacing can be complicated to dial in on changing terrain. It is pricier than the other options."
    },
    {
      "model": "Experience Wild 3 & Experience Wild 3+",
      "brand": "Altra",
      "foam_material": "Ego P35",
      "outsole_compound": "MaxTrac (Wild 3) or Vibram Megagrip (Wild 3+)",
      "lug_depth": "4.0 mm",
      "drop": "4 mm",
      "stack": "33 mm heel / 29 mm forefoot",
      "weight": "9.9 oz / 281 g",
      "price": "$149",
      "pros": "Roomy front for natural toe splay, making it a good wide-foot option with light, efficient feel. The Wild 3+ has exceptional traction on hardpack and loose rock.",
      "cons": "Ride is firm and somewhat unexciting, and it is rated for light-duty trails, so it may be underbuilt for technical rock. It can also have some foot slippage."
    }
  ],
  "tips": [
    "The knowledge base contains no New Balance shoes, so no New Balance models are included; the closest wide-fit, rocky/hardpack alternatives from other brands are listed instead.",
    "For a 30k on rocky and hardpack trails, prioritize a wide toebox with a rock plate or protective midsole, and try shoes in the afternoon when feet are slightly swollen."
  ],
  "matched_race": null,
  "feedback_token": "227e9299baf677848a3fdf1745444ba6.gear_finder.ac28516c640b3af2a0970873867fb456"
}
```
</details>
<details><summary>Captured baseline</summary>

```json
{
  "recommendations": [
    {
      "model": "Cascadia 19",
      "brand": "Brooks",
      "foam_material": "Nitrogen-infused EVA (EVA)",
      "outsole_compound": "TrailTack Green",
      "lug_depth": "4.0 mm",
      "drop": "6.0 mm",
      "stack": "35/29 mm",
      "weight": "10.7 oz / 303 g",
      "price": "$150",
      "pros": "Outstanding platform stability and rock plate protection make it ideal for rocky trails. Available in wide sizing to accommodate wider feet comfortably.",
      "cons": "Heavy daily layout and overbuilt platform that feels slow on flatter paths."
    },
    {
      "model": "Trabuco 14",
      "brand": "Asics",
      "foam_material": "FF Blast Max (supercritical)",
      "outsole_compound": "ASICSGRIP",
      "lug_depth": "3.7 mm",
      "drop": "8 mm",
      "stack": "32.1/25.8 mm",
      "weight": "9.9 oz / 281 g",
      "price": "$145",
      "pros": "Inherently wide fit with a roomy toe box built for stable off-road traction. Provides great rock protection and moderate cushioning for 30k distances.",
      "cons": "Fairly heavy chassis and low ankle collar that can let in debris."
    },
    {
      "model": "Genesis",
      "brand": "Salomon",
      "foam_material": "Energy Foam (EVA/OBC)",
      "outsole_compound": "Contagrip",
      "lug_depth": "4.0 mm",
      "drop": "9.0 mm",
      "stack": "33.5/24.5 mm",
      "weight": "9.7 oz / 275 g",
      "price": "$150",
      "pros": "Accommodating, roomy foot shape with durable Matryx construction. Offers balanced cushioning and great platform stability on rocky terrain.",
      "cons": "Contagrip outsole wears down quickly over high pavement mileage, and high drop may not suit all."
    },
    {
      "model": "Olympus 275",
      "brand": "Altra",
      "foam_material": "CMEVA (EVA)",
      "outsole_compound": "Vibram Megagrip",
      "lug_depth": "3.5 mm",
      "drop": "0.3 mm",
      "stack": "30.8 mm heel / 30.5 mm forefoot",
      "weight": "10.8 oz / 305 g",
      "price": "$185",
      "pros": "Extremely wide footprint with an 81.0 mm toe splay area designed for wide-footed athletes. Balanced underfoot cushion with reliable Vibram Megagrip.",
      "cons": "Low-rebound CMEVA foam feels flat and lacks high energy return."
    },
    {
      "model": "ACG Zegama Trail",
      "brand": "Nike",
      "foam_material": "ZoomX (PEBA) & Cushlon 3.0 (EVA)",
      "outsole_compound": "Vibram Megagrip with Traction Lug",
      "lug_depth": "4.0 mm",
      "drop": "4 mm",
      "stack": "38 mm heel / 34 mm forefoot",
      "weight": "11.8 oz / 336 g",
      "price": "$180",
      "pros": "Generous wide fit with a very spacious toe box. Dual-density ZoomX cushioning protects joints on technical, rocky surfaces.",
      "cons": "Heavy and bulky build that feels slow on non-technical flats."
    }
  ],
  "tips": [
    "The catalog contains zero trail running shoes from your preferred brand (New Balance), so the closest trail models matching wide fit and medium/balanced cushioning from other brands are recommended.",
    "For rocky hardpack 30k races, prioritize shoes equipped with rock plates or firm dual-density midsoles to shield against sharp stone bruising."
  ],
  "matched_race": null
}
```
</details>
