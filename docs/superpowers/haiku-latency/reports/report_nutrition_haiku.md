# Golden report — nutrition


## nutrition_fixture_caffeine_sensitive

- Gemini+KB latency: **13.4s** (baseline: 5.8s)
- Catalog membership: ✅ all recommendations exist in the distilled catalog

<details><summary>Gemini+KB output</summary>

```json
{
  "products": [
    {
      "brand": "Precision Fuel & Hydration",
      "name": "Carb Only Drink Mix",
      "total_quantity": 4,
      "carbs_per_unit": 120,
      "sodium_per_unit": 0,
      "protein_per_unit": 0,
      "tech_notes": "Non-caffeinated 2:1 glucose-to-fructose mix with zero sodium. Use half a unit per hour in about 500ml of water to deliver 60g/h. Four units cover the 8-hour target of 480g total carbs."
    },
    {
      "brand": "Precision Fuel & Hydration",
      "name": "500",
      "total_quantity": 8,
      "carbs_per_unit": 0,
      "sodium_per_unit": 500,
      "protein_per_unit": 0,
      "tech_notes": "Low-strength electrolyte tablet or powder. Take one per hour to deliver 500mg sodium/h, matching the target and keeping sodium separate from carb math. Caffeine-free."
    }
  ],
  "hourly_plan": [
    {
      "hour": 1,
      "action": "Mix half a Carb Only unit in about 500ml water and sip steadily; take one 500 electrolyte serving",
      "carbs": 60,
      "sodium": 500
    },
    {
      "hour": 2,
      "action": "Mix half a Carb Only unit in about 500ml water and sip steadily; take one 500 electrolyte serving",
      "carbs": 60,
      "sodium": 500
    },
    {
      "hour": 3,
      "action": "Mix half a Carb Only unit in about 500ml water and sip steadily; take one 500 electrolyte serving",
      "carbs": 60,
      "sodium": 500
    },
    {
      "hour": 4,
      "action": "Mix half a Carb Only unit in about 500ml water and sip steadily; take one 500 electrolyte serving",
      "carbs": 60,
      "sodium": 500
    },
    {
      "hour": 5,
      "action": "Mix half a Carb Only unit in about 500ml water and sip steadily; take one 500 electrolyte serving",
      "carbs": 60,
      "sodium": 500
    },
    {
      "hour": 6,
      "action": "Mix half a Carb Only unit in about 500ml water and sip steadily; take one 500 electrolyte serving",
      "carbs": 60,
      "sodium": 500
    },
    {
      "hour": 7,
      "action": "Mix half a Carb Only unit in about 500ml water and sip steadily; take one 500 electrolyte serving",
      "carbs": 60,
      "sodium": 500
    },
    {
      "hour": 8,
      "action": "Mix half a Carb Only unit in about 500ml water and sip steadily; take one 500 electrolyte serving",
      "carbs": 60,
      "sodium": 500
    }
  ],
  "tips": [
    "Caffeine-sensitive athlete: all selected products are caffeine-free, so avoid caffeinated gels such as Hammer Espresso and Tropical, Maurten Caf 100 products, and Tailwind Caffeinated.",
    "Drink plain water between mixes, about 300 to 600ml per hour, and practise this exact mix and volume in training so the gut adapts before race day.",
    "Build tolerance over 6 to 8 weeks by raising intake about 10g/h every 1 to 2 weeks, and test the 500mg sodium per hour on hot or hilly long runs."
  ],
  "feedback_token": "5ed5b156040b6a7e4eed3624c5de11ab.nutrition_lab.b40022bcb4005b9d53ff9d4222c8cd12"
}
```
</details>
<details><summary>Captured baseline</summary>

```json
{
  "products": [
    {
      "brand": "Precision Fuel & Hydration",
      "name": "30 Energy Gel",
      "total_quantity": 16,
      "carbs_per_unit": 30.0,
      "sodium_per_unit": 0.0,
      "protein_per_unit": 0.0,
      "tech_notes": "Employs a 2:1 glucose-to-fructose ratio for fast-acting and highly efficient carbohydrate absorption. It is designed with a mild, neutral \"Original\" flavor profile to actively minimize the sweet taste overload and palate fatigue common during long efforts. The gel's texture is specifically engineered to reduce stickiness in the mouth, allowing it to be easily swallowed without requiring an immediate wash-down of plain water. Certified by Informed Sport."
    },
    {
      "brand": "Precision Fuel & Hydration",
      "name": "Electrolyte Capsules",
      "total_quantity": 16,
      "carbs_per_unit": 0.0,
      "sodium_per_unit": 250.0,
      "protein_per_unit": 0.0,
      "tech_notes": "Blister-packed swallowable capsules containing highly concentrated sodium. Designed to give athletes the ultimate flexibility to decouple their hydration/electrolyte intake from their carbohydrate fueling. This allows athletes to consume plain water or customized drink mixes from aid stations and separately ingest capsules to precisely match their genetically determined sweat sodium losses without altering their carbohydrate math or causing stomach upset."
    }
  ],
  "hourly_plan": [
    {
      "hour": 1,
      "action": "Consume two PF 30 Energy Gels (one at 20 min, one at 40 min) and swallow two Electrolyte Capsules with plain water.",
      "carbs": 60.0,
      "sodium": 500.0
    },
    {
      "hour": 2,
      "action": "Consume two PF 30 Energy Gels (one at 20 min, one at 40 min) and swallow two Electrolyte Capsules with plain water.",
      "carbs": 60.0,
      "sodium": 500.0
    },
    {
      "hour": 3,
      "action": "Consume two PF 30 Energy Gels (one at 20 min, one at 40 min) and swallow two Electrolyte Capsules with plain water.",
      "carbs": 60.0,
      "sodium": 500.0
    },
    {
      "hour": 4,
      "action": "Consume two PF 30 Energy Gels (one at 20 min, one at 40 min) and swallow two Electrolyte Capsules with plain water.",
      "carbs": 60.0,
      "sodium": 500.0
    },
    {
      "hour": 5,
      "action": "Consume two PF 30 Energy Gels (one at 20 min, one at 40 min) and swallow two Electrolyte Capsules with plain water.",
      "carbs": 60.0,
      "sodium": 500.0
    },
    {
      "hour": 6,
      "action": "Consume two PF 30 Energy Gels (one at 20 min, one at 40 min) and swallow two Electrolyte Capsules with plain water.",
      "carbs": 60.0,
      "sodium": 500.0
    },
    {
      "hour": 7,
      "action": "Consume two PF 30 Energy Gels (one at 20 min, one at 40 min) and swallow two Electrolyte Capsules with plain water.",
      "carbs": 60.0,
      "sodium": 500.0
    },
    {
      "hour": 8,
      "action": "Consume two PF 30 Energy Gels (one at 20 min, one at 40 min) and swallow two Electrolyte Capsules with plain water.",
      "carbs": 60.0,
      "sodium": 500.0
    }
  ],
  "tips": [
    "Always consume 300ml to 600ml of plain water per hour alongside your gels and electrolyte capsules to support gastric emptying and prevent dehydration-induced gastrointestinal shutdown.",
    "Decoupling your sodium intake through electrolyte capsules allows you to adjust fluid and electrolyte levels dynamically according to temperature and terrain without affecting your carbohydrate delivery.",
    "Space carbohydrate intake into smaller doses taken every 20 to 30 minutes to facilitate consistent intestinal transport, preventing blood sugar spikes and reducing gut distress over long mountain ascents."
  ]
}
```
</details>

## nutrition_fixture_cold_alpine

- Gemini+KB latency: **9.2s** (baseline: 6.2s)
- Catalog membership: ✅ all recommendations exist in the distilled catalog

<details><summary>Gemini+KB output</summary>

```json
{
  "products": [
    {
      "brand": "Maurten",
      "name": "Gel 100",
      "total_quantity": 8,
      "carbs_per_unit": 25,
      "sodium_per_unit": 0,
      "protein_per_unit": 0,
      "tech_notes": "Hydrogel gel with 0.8:1 fructose-to-glucose ratio; firm texture needs no water wash-down, useful in cold conditions. Sodium not listed in knowledge base, so supplement with electrolyte product."
    },
    {
      "brand": "Precision Fuel & Hydration",
      "name": "Electrolyte Capsules",
      "total_quantity": 8,
      "carbs_per_unit": 0,
      "sodium_per_unit": 250,
      "protein_per_unit": 0,
      "tech_notes": "Decoupled sodium source to hit ~500 mg/h without altering carbohydrate math; swallow with water."
    },
    {
      "brand": "Precision Fuel & Hydration",
      "name": "500",
      "total_quantity": 1,
      "carbs_per_unit": 0,
      "sodium_per_unit": 500,
      "protein_per_unit": 0,
      "tech_notes": "Low-strength electrolyte tablet/powder for cold, low-sweat conditions; alternative to capsules for drinking with water."
    }
  ],
  "hourly_plan": [
    {
      "hour": 1,
      "action": "Consume 1 Gel 100 (25g) plus 1 Electrolyte Capsule (250mg) with 300-400ml water; start 15-20 min into effort",
      "carbs": 25,
      "sodium": 250
    },
    {
      "hour": 2,
      "action": "Consume 1 Gel 100 (25g) plus 1 Electrolyte Capsule (250mg) with 300-400ml water",
      "carbs": 25,
      "sodium": 250
    },
    {
      "hour": 3,
      "action": "Consume 2 Gel 100 (50g) plus 1 Electrolyte Capsule (250mg) with 300-400ml water",
      "carbs": 50,
      "sodium": 250
    },
    {
      "hour": 4,
      "action": "Consume 2 Gel 100 (50g) plus 1 Electrolyte Capsule (250mg) with 300-400ml water",
      "carbs": 50,
      "sodium": 250
    },
    {
      "hour": 5,
      "action": "Consume 2 Gel 100 (50g) plus 1 Electrolyte Capsule (250mg) with 300-400ml water",
      "carbs": 50,
      "sodium": 250
    },
    {
      "hour": 6,
      "action": "Consume 2 Gel 100 (50g) plus 1 Electrolyte Capsule (250mg) with 300-400ml water",
      "carbs": 50,
      "sodium": 250
    },
    {
      "hour": 7,
      "action": "Consume 1 Gel 100 (25g) plus 1 Electrolyte Capsule (250mg) with 300-400ml water; finish strong and hydrate",
      "carbs": 25,
      "sodium": 250
    }
  ],
  "tips": [
    "Cold air at 3000m raises fluid loss through breathing and increases sweat evaporation issues, so keep sipping plain water steadily even when not thirsty to avoid dehydration.",
    "Gel 100 is firm and needs no wash-down, which helps in freezing conditions where thick liquids become hard to manage; keep spares warm inside your jacket.",
    "The target of 60g/h is a solid, stomach-friendly intake for a 7-hour effort; practise this exact product and timing in training with a 20% overload before race day."
  ],
  "feedback_token": "133eebfdfb9e8f993eb647e0339a12f2.nutrition_lab.6ce772a7e9471c4cd61554d77254c6d8"
}
```
</details>
<details><summary>Captured baseline</summary>

```json
{
  "products": [
    {
      "brand": "Precision Fuel & Hydration",
      "name": "Carb & Electrolyte Drink Mix",
      "total_quantity": 3,
      "carbs_per_unit": 60,
      "sodium_per_unit": 1000,
      "protein_per_unit": 0,
      "tech_notes": "Formulated with a scientifically backed 2:1 glucose-to-fructose ratio to maximize carbohydrate absorption. It is designed to deliver a steady stream of rapidly digestible energy during high-intensity efforts lasting several hours, helping to replace fluid and sweat losses simultaneously. It is engineered with a very mild, neutral taste to minimize palate fatigue and stomach issues during hard efforts, making it highly palatable even when breathing hard. Certified by Informed Sport and uses 100% recyclable packaging."
    },
    {
      "brand": "Bix",
      "name": "Bix 30 Energy Gel – Salted Strawberry",
      "total_quantity": 4,
      "carbs_per_unit": 30,
      "sodium_per_unit": 300,
      "protein_per_unit": 0,
      "tech_notes": "Formulated with a 1:0.8 glucose-to-fructose ratio, this gel is vegan, uses natural flavors and colors, and is Informed Sport batch tested. It is designed specifically for longer efforts, hotter conditions, or heavy sweat to maintain an ideal balance between quick energy and robust electrolyte replenishment. Its natural strawberry flavor with a slightly salty finish is smooth, light, and engineered to prevent palate fatigue during long sessions."
    },
    {
      "brand": "Precision Fuel & Hydration",
      "name": "30 Energy Chew",
      "total_quantity": 4,
      "carbs_per_unit": 30,
      "sodium_per_unit": 0,
      "protein_per_unit": 0,
      "tech_notes": "Features an exceptionally high carbohydrate-to-weight ratio, making it a great choice when traveling light is essential. Chews provide a solid, satisfying bite that can feel more gratifying than liquid gels during lower-intensity sections or longer races, actively helping to break up flavor fatigue. Available in Original (mild, neutral flavor), Watermelon, and Mint & Lemon. Independently batch-tested for WADA-prohibited substances."
    },
    {
      "brand": "Precision Fuel & Hydration",
      "name": "Electrolyte Capsules",
      "total_quantity": 4,
      "carbs_per_unit": 0,
      "sodium_per_unit": 250,
      "protein_per_unit": 0,
      "tech_notes": "Blister-packed swallowable capsules containing highly concentrated sodium. Designed to give athletes the ultimate flexibility to decouple their hydration/electrolyte intake from their carbohydrate fueling. This allows athletes to consume plain water or customized drink mixes from aid stations and separately ingest capsules to precisely match their genetically determined sweat sodium losses without altering their carbohydrate math or causing stomach upset."
    }
  ],
  "hourly_plan": [
    {
      "hour": 1,
      "action": "Sip 0.5 packet of Carb & Electrolyte Drink Mix dissolved in water across the hour (30g carbs, 500mg sodium) plus 1 Bix 30 Energy Gel - Salted Strawberry (30g carbs, 300mg sodium).",
      "carbs": 60,
      "sodium": 800
    },
    {
      "hour": 2,
      "action": "Consume 1 packet of 30 Energy Chew (30g carbs, 0mg sodium) and 1 Bix 30 Energy Gel - Salted Strawberry (30g carbs, 300mg sodium) with plain water, plus 1 Electrolyte Capsule (250mg sodium).",
      "carbs": 60,
      "sodium": 550
    },
    {
      "hour": 3,
      "action": "Sip 0.5 packet of Carb & Electrolyte Drink Mix in water (30g carbs, 500mg sodium) and consume 1 packet of 30 Energy Chew (30g carbs, 0mg sodium).",
      "carbs": 60,
      "sodium": 500
    },
    {
      "hour": 4,
      "action": "Sip 0.5 packet of Carb & Electrolyte Drink Mix in water (30g carbs, 500mg sodium) plus 1 Bix 30 Energy Gel - Salted Strawberry (30g carbs, 300mg sodium).",
      "carbs": 60,
      "sodium": 800
    },
    {
      "hour": 5,
      "action": "Consume 1 packet of 30 Energy Chew (30g carbs, 0mg sodium) and 1 Bix 30 Energy Gel - Salted Strawberry (30g carbs, 300mg sodium) with plain water, plus 1 Electrolyte Capsule (250mg sodium).",
      "carbs": 60,
      "sodium": 550
    },
    {
      "hour": 6,
      "action": "Sip 0.5 packet of Carb & Electrolyte Drink Mix in water (30g carbs, 500mg sodium) and consume 1 packet of 30 Energy Chew (30g carbs, 0mg sodium).",
      "carbs": 60,
      "sodium": 500
    },
    {
      "hour": 7,
      "action": "Sip 1.0 packet of Carb & Electrolyte Drink Mix in water over the final hour to easily meet your energy and electrolyte goals.",
      "carbs": 60,
      "sodium": 1000
    }
  ],
  "tips": [
    "Cold temperatures and high altitude reduce the sensation of thirst while respiratory water loss increases; drink proactively on a strict timer rather than relying on thirst cues.",
    "Always wash down solid chews and gels with plain water to optimize gastric emptying and prevent gastrointestinal distress on steep mountain climbs.",
    "Keep energy chews and gels in an internal jacket pocket close to body heat so they do not freeze or become difficult to chew in sub-freezing mountain conditions."
  ]
}
```
</details>

## nutrition_fixture_cool_road_marathon

- Gemini+KB latency: **12.6s** (baseline: 4.8s)
- Catalog membership: ✅ all recommendations exist in the distilled catalog

<details><summary>Gemini+KB output</summary>

```json
{
  "products": [
    {
      "brand": "Tailwind Nutrition",
      "name": "Tailwind Endurance Fuel",
      "total_quantity": 3,
      "carbs_per_unit": 25.0,
      "sodium_per_unit": 310,
      "protein_per_unit": 0.0,
      "tech_notes": "Dual-carbohydrate formula of dextrose and sucrose with sodium, potassium, magnesium, and calcium. Serves as the hydration and carb base for the bottle, with about 310 mg sodium per serving."
    },
    {
      "brand": "Precision Fuel & Hydration",
      "name": "30 Energy Gel",
      "total_quantity": 3,
      "carbs_per_unit": 30,
      "sodium_per_unit": 0,
      "protein_per_unit": 0,
      "tech_notes": "2:1 glucose-to-fructose ratio with a mild, neutral Original flavor and a texture that is easy to swallow without a water wash-down. Provides the solid-carb hourly dose with no sodium, so it is paired with capsules."
    },
    {
      "brand": "Precision Fuel & Hydration",
      "name": "Electrolyte Capsules",
      "total_quantity": 3,
      "carbs_per_unit": 0,
      "sodium_per_unit": 250,
      "protein_per_unit": 0,
      "tech_notes": "Swallowable capsules with concentrated sodium. Taken separately from carbohydrate intake so sodium can be adjusted to sweat rate without changing the carb math."
    }
  ],
  "hourly_plan": [
    {
      "hour": 1,
      "action": "Start at 15-20 min in. Take 1 Tailwind Endurance Fuel serving in bottle, 1 PF 30 Energy Gel, 1 Electrolyte Capsule, and 300-600 ml total fluid including plain water alongside the gel.",
      "carbs": 55,
      "sodium": 560
    },
    {
      "hour": 2,
      "action": "Repeat: 1 Tailwind Endurance Fuel serving in bottle, 1 PF 30 Energy Gel, 1 Electrolyte Capsule, plus plain water to keep fluid at 300-600 ml per hour.",
      "carbs": 55,
      "sodium": 560
    },
    {
      "hour": 3,
      "action": "Repeat the hourly dose. Stop the gel about 15 minutes before the finish to avoid unnecessary fuel, and keep sipping water.",
      "carbs": 55,
      "sodium": 560
    }
  ],
  "tips": [
    "Start carbohydrate intake 15-20 minutes into the race and take small doses every 15-20 minutes rather than large boluses, since cool conditions still allow the gut to handle steady intake.",
    "Always drink plain water with the gel and keep fluid at roughly 300-600 ml per hour so the concentrated Tailwind mix does not raise gut osmolality and slow absorption.",
    "Practise this exact combination of Tailwind, PF 30 Gel, and capsules in training at least 2 times per week for 6-8 weeks, and increase carbs by about 10 g/h every 1-2 weeks to reach the 60 g/h target comfortably."
  ],
  "feedback_token": "e77a66d9286ed4dd4bef2ffceeb71129.nutrition_lab.78b616322494664f8c814d39f8fabcd6"
}
```
</details>
<details><summary>Captured baseline</summary>

```json
{
  "products": [
    {
      "brand": "Precision Fuel & Hydration",
      "name": "30 Energy Gel",
      "total_quantity": 4,
      "carbs_per_unit": 30.0,
      "sodium_per_unit": 0.0,
      "protein_per_unit": 0.0,
      "tech_notes": "Employs a 2:1 glucose-to-fructose ratio for fast-acting and highly efficient carbohydrate absorption. It is designed with a mild, neutral \"Original\" flavor profile to actively minimize the sweet taste overload and palate fatigue common during long efforts. The gel's texture is specifically engineered to reduce stickiness in the mouth, allowing it to be easily swallowed without requiring an immediate wash-down of plain water. Certified by Informed Sport."
    },
    {
      "brand": "Precision Fuel & Hydration",
      "name": "30 Caffeine Gel",
      "total_quantity": 3,
      "carbs_per_unit": 30.0,
      "sodium_per_unit": 0.0,
      "protein_per_unit": 0.0,
      "tech_notes": "Blends 30g of carbohydrates in a 2:1 glucose-to-fructose ratio with a powerful 100mg caffeine kick to stave off physical and mental fatigue, increase alertness, and lower perceived exertion during races. Designed to taste significantly better than typical caffeinated gels, offering a smooth, palatable consistency that goes down easily under race stress. Certified by Informed Sport."
    },
    {
      "brand": "Precision Fuel & Hydration",
      "name": "Electrolyte Capsules",
      "total_quantity": 7,
      "carbs_per_unit": 0.0,
      "sodium_per_unit": 250.0,
      "protein_per_unit": 0.0,
      "tech_notes": "Blister-packed swallowable capsules containing highly concentrated sodium. Designed to give athletes the ultimate flexibility to decouple their hydration/electrolyte intake from their carbohydrate fueling. This allows athletes to consume plain water or customized drink mixes from aid stations and separately ingest capsules to precisely match their genetically determined sweat sodium losses without altering their carbohydrate math or causing stomach upset."
    }
  ],
  "hourly_plan": [
    {
      "hour": 1,
      "action": "Consume 1 Precision Fuel 30 Energy Gel at minute 20 and 1 Precision Fuel 30 Energy Gel at minute 40. Ingest 2 Precision Fuel Electrolyte Capsules with 400-500ml of plain water across the hour.",
      "carbs": 60.0,
      "sodium": 500.0
    },
    {
      "hour": 2,
      "action": "Consume 1 Precision Fuel 30 Energy Gel at minute 20 and 1 Precision Fuel 30 Caffeine Gel at minute 40 for a mental boost. Ingest 2 Precision Fuel Electrolyte Capsules with 400-500ml of plain water.",
      "carbs": 60.0,
      "sodium": 500.0
    },
    {
      "hour": 3,
      "action": "Consume 1 Precision Fuel 30 Energy Gel at minute 20 and 1 Precision Fuel 30 Caffeine Gel at minute 40. Ingest 2 Precision Fuel Electrolyte Capsules with 400-500ml of plain water.",
      "carbs": 60.0,
      "sodium": 500.0
    },
    {
      "hour": 4,
      "action": "For the remaining 30 minutes of racing, consume 1 Precision Fuel 30 Caffeine Gel at minute 15. Ingest 1 Precision Fuel Electrolyte Capsule with 200-250ml of plain water.",
      "carbs": 30.0,
      "sodium": 250.0
    }
  ],
  "tips": [
    "Decouple hydration from fueling by taking electrolyte capsules alongside plain water to hit precise sodium targets without altering carbohydrate intake.",
    "Take gels in split doses every 20 to 30 minutes with water to optimize gastric emptying and prevent gut distress in cool conditions.",
    "Utilize caffeine strategically in the second half of the marathon to reduce perceived exertion and sustain focus through the final miles."
  ]
}
```
</details>

## nutrition_fixture_high_carb_trained_gut

- Gemini+KB latency: **14.5s** (baseline: 6.1s)
- Catalog membership: ✅ all recommendations exist in the distilled catalog

<details><summary>Gemini+KB output</summary>

```json
{
  "products": [
    {
      "brand": "Precision Fuel & Hydration",
      "name": "Carb & Electrolyte Drink Mix",
      "total_quantity": 12,
      "carbs_per_unit": 60,
      "sodium_per_unit": 1000,
      "protein_per_unit": 0,
      "tech_notes": "2:1 glucose-to-fructose drink mix providing 60g carbs and 1000mg sodium per serving. Primary hourly fuel, one serving per hour in bottles."
    },
    {
      "brand": "Maurten",
      "name": "Gel 160",
      "total_quantity": 12,
      "carbs_per_unit": 40,
      "sodium_per_unit": 0,
      "protein_per_unit": 0,
      "tech_notes": "Hydrogel firm gel with 40g carbs in a 0.8:1 fructose-to-glucose ratio, one unit per hour. Sodium not listed in the knowledge base, so the 1000mg sodium comes entirely from the drink mix. Carry plain water with it."
    }
  ],
  "hourly_plan": [
    {
      "hour": 1,
      "action": "Start fueling 15-20 minutes in: 1 serving Carb & Electrolyte Drink Mix in bottle plus 1 Gel 160 with water",
      "carbs": 100,
      "sodium": 1000
    },
    {
      "hour": 2,
      "action": "1 serving Carb & Electrolyte Drink Mix plus 1 Gel 160 with water",
      "carbs": 100,
      "sodium": 1000
    },
    {
      "hour": 3,
      "action": "1 serving Carb & Electrolyte Drink Mix plus 1 Gel 160 with water; check fluid intake of roughly 500ml",
      "carbs": 100,
      "sodium": 1000
    },
    {
      "hour": 4,
      "action": "1 serving Carb & Electrolyte Drink Mix plus 1 Gel 160 with water; resupply at aid station",
      "carbs": 100,
      "sodium": 1000
    },
    {
      "hour": 5,
      "action": "1 serving Carb & Electrolyte Drink Mix plus 1 Gel 160 with water",
      "carbs": 100,
      "sodium": 1000
    },
    {
      "hour": 6,
      "action": "1 serving Carb & Electrolyte Drink Mix plus 1 Gel 160 with water; reassess body mass and cramping",
      "carbs": 100,
      "sodium": 1000
    },
    {
      "hour": 7,
      "action": "1 serving Carb & Electrolyte Drink Mix plus 1 Gel 160 with water",
      "carbs": 100,
      "sodium": 1000
    },
    {
      "hour": 8,
      "action": "1 serving Carb & Electrolyte Drink Mix plus 1 Gel 160 with water; resupply at aid station",
      "carbs": 100,
      "sodium": 1000
    },
    {
      "hour": 9,
      "action": "1 serving Carb & Electrolyte Drink Mix plus 1 Gel 160 with water",
      "carbs": 100,
      "sodium": 1000
    },
    {
      "hour": 10,
      "action": "1 serving Carb & Electrolyte Drink Mix plus 1 Gel 160 with water; prepare for final push",
      "carbs": 100,
      "sodium": 1000
    },
    {
      "hour": 11,
      "action": "1 serving Carb & Electrolyte Drink Mix plus 1 Gel 160 with water to finish",
      "carbs": 100,
      "sodium": 1000
    }
  ],
  "tips": [
    "Practise this exact combination of Carb & Electrolyte Drink Mix and Gel 160 in training so the gut is adapted before race day, and drink plain water alongside the gel to support absorption.",
    "The 1000mg sodium per hour slightly exceeds the 800mg target, so monitor for excess thirst and reduce drink concentration or mix extra water if you feel bloated or overly salty.",
    "Carry at least one spare Gel 160 and drink mix serving beyond the planned quantity, and check aid station resupply timing so no hourly fueling is missed."
  ],
  "feedback_token": "6d41bd493b324a568e74a97ac83f80d0.nutrition_lab.f598c02d5e405f0e98cf461ba8f2afdf"
}
```
</details>
<details><summary>Captured baseline</summary>

```json
{
  "products": [
    {
      "brand": "Precision Fuel & Hydration",
      "name": "Carb & Electrolyte Drink Mix",
      "total_quantity": 11,
      "carbs_per_unit": 60,
      "sodium_per_unit": 1000,
      "protein_per_unit": 0,
      "tech_notes": "Formulated with a scientifically backed 2:1 glucose-to-fructose ratio to maximize carbohydrate absorption. It is designed to deliver a steady stream of rapidly digestible energy during high-intensity efforts lasting several hours, helping to replace fluid and sweat losses simultaneously. It is engineered with a very mild, neutral taste to minimize palate fatigue and stomach issues during hard efforts, making it highly palatable even when breathing hard. Certified by Informed Sport and uses 100% recyclable packaging."
    },
    {
      "brand": "Maurten",
      "name": "Gel 160",
      "total_quantity": 11,
      "carbs_per_unit": 40,
      "sodium_per_unit": 0,
      "protein_per_unit": 0,
      "tech_notes": "Developed as a larger hydrogel option for endurance athletes who want to meet higher hourly carbohydrate targets with less packaging to carry and less trail waste to carry out. It utilizes Hydrogel Technology to carry 40 grams of carbohydrates cleanly through the stomach in an optimal 0.8:1 fructose-to-glucose ratio. Features a firm, Jell-O-like consistency that is only slightly sweet and goes down smoothly. Formulated with only 6 natural ingredients, is suitable for vegetarians and vegans, and contains no artificial colors, preservatives, or flavors."
    }
  ],
  "hourly_plan": [
    {
      "hour": 1,
      "action": "Sip 1 serving of Precision Fuel & Hydration Carb & Electrolyte Drink Mix diluted in 500-750ml water across the hour; take 1 Maurten Gel 160 at minute 30.",
      "carbs": 100,
      "sodium": 1000
    },
    {
      "hour": 2,
      "action": "Sip 1 serving of Precision Fuel & Hydration Carb & Electrolyte Drink Mix diluted in 500-750ml water across the hour; take 1 Maurten Gel 160 at minute 30.",
      "carbs": 100,
      "sodium": 1000
    },
    {
      "hour": 3,
      "action": "Sip 1 serving of Precision Fuel & Hydration Carb & Electrolyte Drink Mix diluted in 500-750ml water across the hour; take 1 Maurten Gel 160 at minute 30.",
      "carbs": 100,
      "sodium": 1000
    },
    {
      "hour": 4,
      "action": "Sip 1 serving of Precision Fuel & Hydration Carb & Electrolyte Drink Mix diluted in 500-750ml water across the hour; take 1 Maurten Gel 160 at minute 30.",
      "carbs": 100,
      "sodium": 1000
    },
    {
      "hour": 5,
      "action": "Sip 1 serving of Precision Fuel & Hydration Carb & Electrolyte Drink Mix diluted in 500-750ml water across the hour; take 1 Maurten Gel 160 at minute 30.",
      "carbs": 100,
      "sodium": 1000
    },
    {
      "hour": 6,
      "action": "Sip 1 serving of Precision Fuel & Hydration Carb & Electrolyte Drink Mix diluted in 500-750ml water across the hour; take 1 Maurten Gel 160 at minute 30.",
      "carbs": 100,
      "sodium": 1000
    },
    {
      "hour": 7,
      "action": "Sip 1 serving of Precision Fuel & Hydration Carb & Electrolyte Drink Mix diluted in 500-750ml water across the hour; take 1 Maurten Gel 160 at minute 30.",
      "carbs": 100,
      "sodium": 1000
    },
    {
      "hour": 8,
      "action": "Sip 1 serving of Precision Fuel & Hydration Carb & Electrolyte Drink Mix diluted in 500-750ml water across the hour; take 1 Maurten Gel 160 at minute 30.",
      "carbs": 100,
      "sodium": 1000
    },
    {
      "hour": 9,
      "action": "Sip 1 serving of Precision Fuel & Hydration Carb & Electrolyte Drink Mix diluted in 500-750ml water across the hour; take 1 Maurten Gel 160 at minute 30.",
      "carbs": 100,
      "sodium": 1000
    },
    {
      "hour": 10,
      "action": "Sip 1 serving of Precision Fuel & Hydration Carb & Electrolyte Drink Mix diluted in 500-750ml water across the hour; take 1 Maurten Gel 160 at minute 30.",
      "carbs": 100,
      "sodium": 1000
    },
    {
      "hour": 11,
      "action": "Sip 1 serving of Precision Fuel & Hydration Carb & Electrolyte Drink Mix diluted in 500-750ml water across the hour; take 1 Maurten Gel 160 at minute 30.",
      "carbs": 100,
      "sodium": 1000
    }
  ],
  "tips": [
    "Execute gut training during long workouts 6 to 8 weeks out to adapt intestinal transporters to the 100g/h carbohydrate intake.",
    "Preload with a high-sodium electrolyte drink the night before and 90 minutes before the race start to expand blood plasma volume.",
    "Consume plain water alongside concentrated hydrogels to maintain gastric emptying rates and prevent gastrointestinal distress."
  ]
}
```
</details>

## nutrition_fixture_hot_50k

- Gemini+KB latency: **15.0s** (baseline: 6.2s)
- Catalog membership: ✅ all recommendations exist in the distilled catalog

<details><summary>Gemini+KB output</summary>

```json
{
  "products": [
    {
      "brand": "Maurten",
      "name": "Drink Mix 160",
      "total_quantity": 8,
      "carbs_per_unit": 40,
      "sodium_per_unit": 0,
      "protein_per_unit": 0,
      "tech_notes": "Hydrogel drink mix, 40g carbs per unit. Sodium not listed in the knowledge base, so the 1000 mg/h target cannot be confirmed from this product. Use one unit per hour in roughly 500 ml of water."
    },
    {
      "brand": "Maurten",
      "name": "Gel 160",
      "total_quantity": 4,
      "carbs_per_unit": 40,
      "sodium_per_unit": 0,
      "protein_per_unit": 0,
      "tech_notes": "Large-format firm hydrogel gel, 40g carbs per unit at a 0.8:1 fructose-to-glucose ratio. Sodium not listed in the knowledge base. Take half a unit (20g) per hour, in small doses every 15 to 20 minutes, with plain water."
    }
  ],
  "hourly_plan": [
    {
      "hour": 1,
      "action": "Start fueling 15 to 20 minutes in: 1 Drink Mix 160 (40g) in 500 ml water, plus half a Gel 160 (20g) in small doses; target 500 to 600 ml fluid per hour",
      "carbs": 60,
      "sodium": 0
    },
    {
      "hour": 2,
      "action": "1 Drink Mix 160 (40g) in water plus half a Gel 160 (20g) in small doses; sip plain water between doses",
      "carbs": 60,
      "sodium": 0
    },
    {
      "hour": 3,
      "action": "1 Drink Mix 160 (40g) in water plus half a Gel 160 (20g) in small doses; monitor for heat stress and fluid loss",
      "carbs": 60,
      "sodium": 0
    },
    {
      "hour": 4,
      "action": "1 Drink Mix 160 (40g) in water plus half a Gel 160 (20g) in small doses; reassess sweat losses and fluid intake",
      "carbs": 60,
      "sodium": 0
    },
    {
      "hour": 5,
      "action": "1 Drink Mix 160 (40g) in water plus half a Gel 160 (20g) in small doses; keep fluid volume steady in the heat",
      "carbs": 60,
      "sodium": 0
    },
    {
      "hour": 6,
      "action": "1 Drink Mix 160 (40g) in water plus half a Gel 160 (20g) in small doses; prioritize plain water if the gut feels full",
      "carbs": 60,
      "sodium": 0
    },
    {
      "hour": 7,
      "action": "1 Drink Mix 160 (40g) in water plus half a Gel 160 (20g) in small doses; continue steady intake through the final climbs",
      "carbs": 60,
      "sodium": 0
    },
    {
      "hour": 8,
      "action": "1 Drink Mix 160 (40g) in water plus half a Gel 160 (20g) in small doses; finish with plain water and no fueling gaps",
      "carbs": 60,
      "sodium": 0
    }
  ],
  "tips": [
    "The Maurten products in the knowledge base do not list sodium, so the 1000 mg/h sodium target cannot be verified from the catalog. Confirm sodium content with Maurten before race day and plan a sodium source accordingly.",
    "At 30C, use 500 to 600 ml of fluid per hour and avoid over-drinking plain water; watch for body mass loss above 2%, which degrades performance.",
    "Practice this exact plan in training at 20% above target carbs (about 72g/h), using the same Maurten products, to confirm gut tolerance before race day."
  ],
  "feedback_token": "9aacc299a9d735c3de9222abc8146da5.nutrition_lab.3d1dc977a0cc747e1a89ed3feb0e2a85"
}
```
</details>
<details><summary>Captured baseline</summary>

```json
{
  "products": [
    {
      "brand": "Maurten",
      "name": "Drink Mix 160",
      "total_quantity": 8,
      "carbs_per_unit": 40.0,
      "sodium_per_unit": 0.0,
      "protein_per_unit": 0.0,
      "tech_notes": "Based on patented Hydrogel Technology. Unlike other sports drinks, the liquid instantly converts into a hydrogel upon coming into contact with the acidity of stomach acid. This encapsulates the carbohydrates, carrying them through the stomach safely to reduce gastrointestinal distress and minimize the sensation of liquid sloshing in the gut. Designed for longer, lower-intensity training and racing. It dissolves quickly and has a very basic, neutral taste with no excessive sugars or artificial flavorings."
    },
    {
      "brand": "Maurten",
      "name": "Gel 100",
      "total_quantity": 7,
      "carbs_per_unit": 25.0,
      "sodium_per_unit": 0.0,
      "protein_per_unit": 0.0,
      "tech_notes": "Uses patented Hydrogel Technology to encapsulate carbohydrates, allowing them to safely pass through the stomach acid to be absorbed directly in the intestine, which prevents the gastrointestinal distress common with simple sugars. Unlike traditional syrupy gels, it has a firm, Jell-O-like texture that is easy to swallow during high-intensity efforts and does not require water to wash it down. Built with only 6 natural ingredients in an optimal 0.8:1 ratio of fructose to glucose. Contains no added colors, preservatives, or flavorings."
    },
    {
      "brand": "Maurten",
      "name": "Gel 100 Caf 100",
      "total_quantity": 1,
      "carbs_per_unit": 25.0,
      "sodium_per_unit": 0.0,
      "protein_per_unit": 0.0,
      "tech_notes": "Features the same patented Hydrogel Technology and firm, non-syrupy consistency as Gel 100. It encapsulates both the carbohydrates and the caffeine to carry them safely through the stomach to reduce gastrointestinal distress and remove any bitter caffeine aftertaste. Built with only 7 natural ingredients in a 0.8:1 ratio of fructose to glucose. Contains no added colors, preservatives, or flavorings."
    }
  ],
  "hourly_plan": [
    {
      "hour": 1,
      "action": "Sip 1 serving of Maurten Drink Mix 160 mixed in 500ml water across the hour, and consume 1 Maurten Gel 100 at minute 30.",
      "carbs": 65.0,
      "sodium": 0.0
    },
    {
      "hour": 2,
      "action": "Sip 1 serving of Maurten Drink Mix 160 mixed in 500ml water across the hour, and consume 1 Maurten Gel 100 at minute 30.",
      "carbs": 65.0,
      "sodium": 0.0
    },
    {
      "hour": 3,
      "action": "Sip 1 serving of Maurten Drink Mix 160 mixed in 500ml water across the hour, and consume 1 Maurten Gel 100 at minute 30.",
      "carbs": 65.0,
      "sodium": 0.0
    },
    {
      "hour": 4,
      "action": "Sip 1 serving of Maurten Drink Mix 160 mixed in 500ml water across the hour, and consume 1 Maurten Gel 100 Caf 100 at minute 30 for a mid-race mental boost.",
      "carbs": 65.0,
      "sodium": 0.0
    },
    {
      "hour": 5,
      "action": "Sip 1 serving of Maurten Drink Mix 160 mixed in 500ml water across the hour, and consume 1 Maurten Gel 100 at minute 30.",
      "carbs": 65.0,
      "sodium": 0.0
    },
    {
      "hour": 6,
      "action": "Sip 1 serving of Maurten Drink Mix 160 mixed in 500ml water across the hour, and consume 1 Maurten Gel 100 at minute 30.",
      "carbs": 65.0,
      "sodium": 0.0
    },
    {
      "hour": 7,
      "action": "Sip 1 serving of Maurten Drink Mix 160 mixed in 500ml water across the hour, and consume 1 Maurten Gel 100 at minute 30.",
      "carbs": 65.0,
      "sodium": 0.0
    },
    {
      "hour": 8,
      "action": "Sip 1 serving of Maurten Drink Mix 160 mixed in 500ml water across the hour, and consume 1 Maurten Gel 100 at minute 30 to power the final climb and finish.",
      "carbs": 65.0,
      "sodium": 0.0
    }
  ],
  "tips": [
    "The Maurten catalog in the knowledge base does not include standalone sodium or electrolyte products; to meet your 1000mg/hour sodium goal in 30C heat, you must decouple hydration and integrate a dedicated electrolyte supplement like Precision Fuel & Hydration Electrolyte Capsules or 1000 drink mix.",
    "Maurten products rely on Hydrogel Technology to safely pass carbohydrates through the stomach into the intestine without gastrointestinal distress, so ensure drink mixes are mixed strictly to instructions and not over-diluted.",
    "In 30C hot conditions with high elevation gain, consume consistent fluid amounts (around 500-750ml per hour) and use proactive cooling techniques like dousing with cold water to maintain plasma volume and core temperature."
  ]
}
```
</details>

## nutrition_fixture_humid_vietnam_70k

- Gemini+KB latency: **14.0s** (baseline: 5.5s)
- Catalog membership: ✅ all recommendations exist in the distilled catalog

<details><summary>Gemini+KB output</summary>

```json
{
  "products": [
    {
      "brand": "Precision Fuel & Hydration",
      "name": "Carb & Electrolyte Drink Mix",
      "total_quantity": 14,
      "carbs_per_unit": 60,
      "sodium_per_unit": 1000,
      "protein_per_unit": 0,
      "tech_notes": "Uses a 2:1 glucose-to-fructose ratio with 1000 mg sodium per serving, matching the 60 g/h carb and 1000 mg/h sodium targets with one serving per hour. Total for 14 h: 840 g carbs and 14,000 mg sodium. Mild neutral taste limits palate fatigue. Sip alongside plain water."
    }
  ],
  "hourly_plan": [
    {
      "hour": 1,
      "action": "Start first serving 15-20 min into the race, mixed per label; sip 300-600 ml total fluid this hour",
      "carbs": 60,
      "sodium": 1000
    },
    {
      "hour": 2,
      "action": "One serving of drink mix; sip plain water between bottles",
      "carbs": 60,
      "sodium": 1000
    },
    {
      "hour": 3,
      "action": "One serving of drink mix; check urine color and fluid intake",
      "carbs": 60,
      "sodium": 1000
    },
    {
      "hour": 4,
      "action": "One serving of drink mix; refill with plain water at aid station if needed",
      "carbs": 60,
      "sodium": 1000
    },
    {
      "hour": 5,
      "action": "One serving of drink mix; keep sipping steadily, avoid large gulps",
      "carbs": 60,
      "sodium": 1000
    },
    {
      "hour": 6,
      "action": "One serving of drink mix; reassess heat and sweat loss, adjust fluid volume",
      "carbs": 60,
      "sodium": 1000
    },
    {
      "hour": 7,
      "action": "One serving of drink mix; mid-race body weight check if possible",
      "carbs": 60,
      "sodium": 1000
    },
    {
      "hour": 8,
      "action": "One serving of drink mix; continue steady intake through climbing sections",
      "carbs": 60,
      "sodium": 1000
    },
    {
      "hour": 9,
      "action": "One serving of drink mix; keep fluid and carb intake consistent despite fatigue",
      "carbs": 60,
      "sodium": 1000
    },
    {
      "hour": 10,
      "action": "One serving of drink mix; monitor for cramping and GI symptoms",
      "carbs": 60,
      "sodium": 1000
    },
    {
      "hour": 11,
      "action": "One serving of drink mix; maintain plain water alongside",
      "carbs": 60,
      "sodium": 1000
    },
    {
      "hour": 12,
      "action": "One serving of drink mix; verify remaining supply for final hours",
      "carbs": 60,
      "sodium": 1000
    },
    {
      "hour": 13,
      "action": "One serving of drink mix; continue steady sipping to the finish",
      "carbs": 60,
      "sodium": 1000
    },
    {
      "hour": 14,
      "action": "Final serving if still racing; finish with plain water for recovery",
      "carbs": 60,
      "sodium": 1000
    }
  ],
  "tips": [
    "Preload about 500 ml of the Carb & Electrolyte Drink Mix the night before and another 500 ml on race morning, finishing 45-60 minutes before the start.",
    "Pair every serving with 300-600 ml of plain water per hour and keep body mass loss under 2%, since dehydration causes gut shutdown and cramping in heavy salty sweaters.",
    "Hold at 60 g/h rather than pushing higher; if GI distress appears, reduce carb concentration first and keep sodium steady, using Electrolyte Capsules to adjust salt separately if cramping starts."
  ],
  "feedback_token": "d53009e71368ea24a4b3b0aeaa6add94.nutrition_lab.bbc1f7bc5c35012f557f37fd42c65083"
}
```
</details>
<details><summary>Captured baseline</summary>

```json
{
  "products": [
    {
      "brand": "Precision Fuel & Hydration",
      "name": "Carb & Electrolyte Drink Mix",
      "total_quantity": 14,
      "carbs_per_unit": 60,
      "sodium_per_unit": 1000,
      "protein_per_unit": 0,
      "tech_notes": "Formulated with a scientifically backed 2:1 glucose-to-fructose ratio to maximize carbohydrate absorption. It is designed to deliver a steady stream of rapidly digestible energy during high-intensity efforts lasting several hours, helping to replace fluid and sweat losses simultaneously. It is engineered with a very mild, neutral taste to minimize palate fatigue and stomach issues during hard efforts, making it highly palatable even when breathing hard. Certified by Informed Sport and uses 100% recyclable packaging."
    }
  ],
  "hourly_plan": [
    {
      "hour": 1,
      "action": "Consume 1 serving of Carb & Electrolyte Drink Mix mixed in 500-750ml water, sipping consistently throughout the hour.",
      "carbs": 60,
      "sodium": 1000
    },
    {
      "hour": 2,
      "action": "Consume 1 serving of Carb & Electrolyte Drink Mix mixed in 500-750ml water, sipping consistently throughout the hour.",
      "carbs": 60,
      "sodium": 1000
    },
    {
      "hour": 3,
      "action": "Consume 1 serving of Carb & Electrolyte Drink Mix mixed in 500-750ml water, sipping consistently throughout the hour.",
      "carbs": 60,
      "sodium": 1000
    },
    {
      "hour": 4,
      "action": "Consume 1 serving of Carb & Electrolyte Drink Mix mixed in 500-750ml water, sipping consistently throughout the hour.",
      "carbs": 60,
      "sodium": 1000
    },
    {
      "hour": 5,
      "action": "Consume 1 serving of Carb & Electrolyte Drink Mix mixed in 500-750ml water, sipping consistently throughout the hour.",
      "carbs": 60,
      "sodium": 1000
    },
    {
      "hour": 6,
      "action": "Consume 1 serving of Carb & Electrolyte Drink Mix mixed in 500-750ml water, sipping consistently throughout the hour.",
      "carbs": 60,
      "sodium": 1000
    },
    {
      "hour": 7,
      "action": "Consume 1 serving of Carb & Electrolyte Drink Mix mixed in 500-750ml water, sipping consistently throughout the hour.",
      "carbs": 60,
      "sodium": 1000
    },
    {
      "hour": 8,
      "action": "Consume 1 serving of Carb & Electrolyte Drink Mix mixed in 500-750ml water, sipping consistently throughout the hour.",
      "carbs": 60,
      "sodium": 1000
    },
    {
      "hour": 9,
      "action": "Consume 1 serving of Carb & Electrolyte Drink Mix mixed in 500-750ml water, sipping consistently throughout the hour.",
      "carbs": 60,
      "sodium": 1000
    },
    {
      "hour": 10,
      "action": "Consume 1 serving of Carb & Electrolyte Drink Mix mixed in 500-750ml water, sipping consistently throughout the hour.",
      "carbs": 60,
      "sodium": 1000
    },
    {
      "hour": 11,
      "action": "Consume 1 serving of Carb & Electrolyte Drink Mix mixed in 500-750ml water, sipping consistently throughout the hour.",
      "carbs": 60,
      "sodium": 1000
    },
    {
      "hour": 12,
      "action": "Consume 1 serving of Carb & Electrolyte Drink Mix mixed in 500-750ml water, sipping consistently throughout the hour.",
      "carbs": 60,
      "sodium": 1000
    },
    {
      "hour": 13,
      "action": "Consume 1 serving of Carb & Electrolyte Drink Mix mixed in 500-750ml water, sipping consistently throughout the hour.",
      "carbs": 60,
      "sodium": 1000
    },
    {
      "hour": 14,
      "action": "Consume 1 serving of Carb & Electrolyte Drink Mix mixed in 500-750ml water, sipping consistently throughout the hour.",
      "carbs": 60,
      "sodium": 1000
    }
  ],
  "tips": [
    "Manage extreme heat and humidity (32C, 85% RH) by dissolving each serving of drink mix into at least 500-750ml of water to keep beverage osmolality low, assist gastric emptying, and match high sweat fluid losses.",
    "Execute a preloading protocol by drinking 500ml of a high-sodium electrolyte solution the evening before and another 500ml on race morning, finishing 45-60 minutes before the start to expand blood plasma volume.",
    "Proactively cool your body using external methods like ice bandanas or pouring cold water over your head and neck at aid stations to mitigate thermal strain and reduce sweat sodium losses."
  ]
}
```
</details>

## nutrition_fixture_hundred_mile

- Gemini+KB latency: **20.2s** (baseline: 10.2s)
- Catalog membership: ✅ all recommendations exist in the distilled catalog

<details><summary>Gemini+KB output</summary>

```json
{
  "products": [
    {
      "brand": "Precision Fuel & Hydration",
      "name": "30 Energy Gel",
      "total_quantity": 60,
      "carbs_per_unit": 30,
      "sodium_per_unit": 0,
      "protein_per_unit": 0,
      "tech_notes": "Employs a 2:1 glucose-to-fructose ratio for fast-acting and highly efficient carbohydrate absorption. Designed with a mild, neutral Original flavor profile to minimize palate fatigue during long efforts. Texture is engineered to reduce stickiness and can be swallowed without an immediate wash-down. Certified by Informed Sport."
    },
    {
      "brand": "Precision Fuel & Hydration",
      "name": "Electrolyte Capsules",
      "total_quantity": 60,
      "carbs_per_unit": 0,
      "sodium_per_unit": 250,
      "protein_per_unit": 0,
      "tech_notes": "Blister-packed swallowable capsules containing highly concentrated sodium. Decouples electrolyte intake from carbohydrate fueling so sodium can be matched to sweat losses without altering carbohydrate math."
    }
  ],
  "hourly_plan": [
    {
      "hour": 1,
      "action": "2 x 30 Energy Gel with 2 Electrolyte Capsules and 300-500 ml water",
      "carbs": 60,
      "sodium": 500
    },
    {
      "hour": 2,
      "action": "2 x 30 Energy Gel with 2 Electrolyte Capsules and 300-500 ml water",
      "carbs": 60,
      "sodium": 500
    },
    {
      "hour": 3,
      "action": "2 x 30 Energy Gel with 2 Electrolyte Capsules and 300-500 ml water",
      "carbs": 60,
      "sodium": 500
    },
    {
      "hour": 4,
      "action": "2 x 30 Energy Gel with 2 Electrolyte Capsules and 300-500 ml water",
      "carbs": 60,
      "sodium": 500
    },
    {
      "hour": 5,
      "action": "2 x 30 Energy Gel with 2 Electrolyte Capsules and 300-500 ml water",
      "carbs": 60,
      "sodium": 500
    },
    {
      "hour": 6,
      "action": "2 x 30 Energy Gel with 2 Electrolyte Capsules and 300-500 ml water",
      "carbs": 60,
      "sodium": 500
    },
    {
      "hour": 7,
      "action": "2 x 30 Energy Gel with 2 Electrolyte Capsules and 300-500 ml water",
      "carbs": 60,
      "sodium": 500
    },
    {
      "hour": 8,
      "action": "2 x 30 Energy Gel with 2 Electrolyte Capsules and 300-500 ml water",
      "carbs": 60,
      "sodium": 500
    },
    {
      "hour": 9,
      "action": "2 x 30 Energy Gel with 2 Electrolyte Capsules and 300-500 ml water",
      "carbs": 60,
      "sodium": 500
    },
    {
      "hour": 10,
      "action": "2 x 30 Energy Gel with 2 Electrolyte Capsules and 300-500 ml water",
      "carbs": 60,
      "sodium": 500
    },
    {
      "hour": 11,
      "action": "2 x 30 Energy Gel with 2 Electrolyte Capsules and 300-500 ml water",
      "carbs": 60,
      "sodium": 500
    },
    {
      "hour": 12,
      "action": "2 x 30 Energy Gel with 2 Electrolyte Capsules and 300-500 ml water",
      "carbs": 60,
      "sodium": 500
    },
    {
      "hour": 13,
      "action": "2 x 30 Energy Gel with 2 Electrolyte Capsules and 300-500 ml water",
      "carbs": 60,
      "sodium": 500
    },
    {
      "hour": 14,
      "action": "2 x 30 Energy Gel with 2 Electrolyte Capsules and 300-500 ml water",
      "carbs": 60,
      "sodium": 500
    },
    {
      "hour": 15,
      "action": "2 x 30 Energy Gel with 2 Electrolyte Capsules and 300-500 ml water",
      "carbs": 60,
      "sodium": 500
    },
    {
      "hour": 16,
      "action": "2 x 30 Energy Gel with 2 Electrolyte Capsules and 300-500 ml water",
      "carbs": 60,
      "sodium": 500
    },
    {
      "hour": 17,
      "action": "2 x 30 Energy Gel with 2 Electrolyte Capsules and 300-500 ml water",
      "carbs": 60,
      "sodium": 500
    },
    {
      "hour": 18,
      "action": "2 x 30 Energy Gel with 2 Electrolyte Capsules and 300-500 ml water",
      "carbs": 60,
      "sodium": 500
    },
    {
      "hour": 19,
      "action": "2 x 30 Energy Gel with 2 Electrolyte Capsules and 300-500 ml water",
      "carbs": 60,
      "sodium": 500
    },
    {
      "hour": 20,
      "action": "2 x 30 Energy Gel with 2 Electrolyte Capsules and 300-500 ml water",
      "carbs": 60,
      "sodium": 500
    },
    {
      "hour": 21,
      "action": "2 x 30 Energy Gel with 2 Electrolyte Capsules and 300-500 ml water",
      "carbs": 60,
      "sodium": 500
    },
    {
      "hour": 22,
      "action": "2 x 30 Energy Gel with 2 Electrolyte Capsules and 300-500 ml water",
      "carbs": 60,
      "sodium": 500
    },
    {
      "hour": 23,
      "action": "2 x 30 Energy Gel with 2 Electrolyte Capsules and 300-500 ml water",
      "carbs": 60,
      "sodium": 500
    },
    {
      "hour": 24,
      "action": "2 x 30 Energy Gel with 2 Electrolyte Capsules and 300-500 ml water",
      "carbs": 60,
      "sodium": 500
    },
    {
      "hour": 25,
      "action": "2 x 30 Energy Gel with 2 Electrolyte Capsules and 300-500 ml water",
      "carbs": 60,
      "sodium": 500
    },
    {
      "hour": 26,
      "action": "2 x 30 Energy Gel with 2 Electrolyte Capsules and 300-500 ml water",
      "carbs": 60,
      "sodium": 500
    },
    {
      "hour": 27,
      "action": "2 x 30 Energy Gel with 2 Electrolyte Capsules and 300-500 ml water",
      "carbs": 60,
      "sodium": 500
    },
    {
      "hour": 28,
      "action": "2 x 30 Energy Gel with 2 Electrolyte Capsules and 300-500 ml water",
      "carbs": 60,
      "sodium": 500
    },
    {
      "hour": 29,
      "action": "2 x 30 Energy Gel with 2 Electrolyte Capsules and 300-500 ml water",
      "carbs": 60,
      "sodium": 500
    },
    {
      "hour": 30,
      "action": "2 x 30 Energy Gel with 2 Electrolyte Capsules and 300-500 ml water",
      "carbs": 60,
      "sodium": 500
    }
  ],
  "tips": [
    "Gut train 6 to 8 weeks out with 2 long sessions per week, progressing about 10 g/h every 1 to 2 weeks toward 72 g/h (20% above the 60 g/h target) using only these exact gels and capsules.",
    "Pair every gel with plain water and keep fluids near 300 to 500 ml/h, reducing volume on the cold night (5C) to avoid overhydration and hyponatremia, and monitor body mass to stay under 2% loss.",
    "Carry a spare gel supply in multiple pockets and verify aid station stocks ahead of time, since missed or dropped gels cause energy dips; keep the athlete fueled at the 60 g/h target across all 30 hours."
  ],
  "feedback_token": "e5e2355abd4ac738b2ba533536184b35.nutrition_lab.1fe33e13887ae1f39b6768b5124952b9"
}
```
</details>
<details><summary>Captured baseline</summary>

```json
{
  "products": [
    {
      "brand": "Precision Fuel & Hydration",
      "name": "Carb & Electrolyte Drink Mix",
      "total_quantity": 10,
      "carbs_per_unit": 60,
      "sodium_per_unit": 1000,
      "protein_per_unit": 0,
      "tech_notes": "Formulated with a scientifically backed 2:1 glucose-to-fructose ratio to maximize carbohydrate absorption. It is designed to deliver a steady stream of rapidly digestible energy during high-intensity efforts lasting several hours, helping to replace fluid and sweat losses simultaneously. It is engineered with a very mild, neutral taste to minimize palate fatigue and stomach issues during hard efforts, making it highly palatable even when breathing hard. Certified by Informed Sport and uses 100% recyclable packaging."
    },
    {
      "brand": "Bix",
      "name": "The Big 40 Energy Gel",
      "total_quantity": 10,
      "carbs_per_unit": 40,
      "sodium_per_unit": 200,
      "protein_per_unit": 0,
      "tech_notes": "This gel features an optimal 1:0.8 glucose-to-fructose ratio to maximize absorption, increase carbohydrate utilization, and decrease stomach distress. It is vegan, uses natural flavors and colors, is manufactured in a UK GMP-certified facility, and is Informed Sport batch tested. Engineered to deliver double the carbs and sodium of typical market gels, it simplifies fueling logistics for endurance athletes. Its light, fluid consistency reduces stickiness and makes it easy to ingest, while its 'stay-on' tab packaging keeps the torn tip attached to prevent trail litter. The caffeinated variant is noted for being highly effective while remaining remarkably gentle on the stomach."
    },
    {
      "brand": "Näak",
      "name": "Näak Ultra Energy™ Puree | Sweet Potatoes Butternut Squash",
      "total_quantity": 10,
      "carbs_per_unit": 26,
      "sodium_per_unit": 0,
      "protein_per_unit": 5,
      "tech_notes": "Developed as a savory food option for ultra-endurance athletes to provide 200 calories while actively breaking up sweet flavor fatigue during long training days or races. Constructed with a low glycemic index to deliver a slow, highly stable, and long-lasting stream of energy. Blends natural simple sugars (maple syrup) with complex carbohydrates (hydrolyzed oat flour). Utilizes highly digestible soy and pea proteins. Made using sustainable, upcycled, and organic ingredients, including sustainably grown Oregon sweet potatoes and malting barley protein upcycled from beer by-products."
    },
    {
      "brand": "Precision Fuel & Hydration",
      "name": "30 Energy Gel",
      "total_quantity": 10,
      "carbs_per_unit": 30,
      "sodium_per_unit": 0,
      "protein_per_unit": 0,
      "tech_notes": "Employs a 2:1 glucose-to-fructose ratio for fast-acting and highly efficient carbohydrate absorption. It is designed with a mild, neutral 'Original' flavor profile to actively minimize the sweet taste overload and palate fatigue common during long efforts. The gel's texture is specifically engineered to reduce stickiness in the mouth, allowing it to be easily swallowed without requiring an immediate wash-down of plain water. Certified by Informed Sport."
    },
    {
      "brand": "Precision Fuel & Hydration",
      "name": "Electrolyte Capsules",
      "total_quantity": 25,
      "carbs_per_unit": 0,
      "sodium_per_unit": 250,
      "protein_per_unit": 0,
      "tech_notes": "Blister-packed swallowable capsules containing highly concentrated sodium. Designed to give athletes the ultimate flexibility to decouple their hydration/electrolyte intake from their carbohydrate fueling. This allows athletes to consume plain water or customized drink mixes from aid stations and separately ingest capsules to precisely match their genetically determined sweat sodium losses without altering their carbohydrate math or causing stomach upset."
    }
  ],
  "hourly_plan": [
    {
      "hour": 1,
      "action": "Sip 1 serving of PF&H Carb & Electrolyte Drink Mix diluted across the hour with plain water.",
      "carbs": 60,
      "sodium": 1000
    },
    {
      "hour": 2,
      "action": "Consume 1 Bix The Big 40 Energy Gel at 20 min, 1 PF&H Electrolyte Capsule at 40 min, and wash down with plain water.",
      "carbs": 40,
      "sodium": 450
    },
    {
      "hour": 3,
      "action": "Eat 1 Näak Ultra Energy Puree and 1 PF&H 30 Energy Gel with 2 PF&H Electrolyte Capsules and water.",
      "carbs": 56,
      "sodium": 500
    },
    {
      "hour": 4,
      "action": "Sip 1 serving of PF&H Carb & Electrolyte Drink Mix diluted across the hour with plain water.",
      "carbs": 60,
      "sodium": 1000
    },
    {
      "hour": 5,
      "action": "Consume 1 Bix The Big 40 Energy Gel at 20 min, 1 PF&H Electrolyte Capsule at 40 min, and wash down with plain water.",
      "carbs": 40,
      "sodium": 450
    },
    {
      "hour": 6,
      "action": "Eat 1 Näak Ultra Energy Puree and 1 PF&H 30 Energy Gel with 2 PF&H Electrolyte Capsules and water.",
      "carbs": 56,
      "sodium": 500
    },
    {
      "hour": 7,
      "action": "Sip 1 serving of PF&H Carb & Electrolyte Drink Mix diluted across the hour with plain water.",
      "carbs": 60,
      "sodium": 1000
    },
    {
      "hour": 8,
      "action": "Consume 1 Bix The Big 40 Energy Gel at 20 min, 1 PF&H Electrolyte Capsule at 40 min, and wash down with plain water.",
      "carbs": 40,
      "sodium": 450
    },
    {
      "hour": 9,
      "action": "Eat 1 Näak Ultra Energy Puree and 1 PF&H 30 Energy Gel with 2 PF&H Electrolyte Capsules and water.",
      "carbs": 56,
      "sodium": 500
    },
    {
      "hour": 10,
      "action": "Sip 1 serving of PF&H Carb & Electrolyte Drink Mix diluted across the hour with plain water.",
      "carbs": 60,
      "sodium": 1000
    },
    {
      "hour": 11,
      "action": "Consume 1 Bix The Big 40 Energy Gel at 20 min, 1 PF&H Electrolyte Capsule at 40 min, and wash down with plain water.",
      "carbs": 40,
      "sodium": 450
    },
    {
      "hour": 12,
      "action": "Eat 1 Näak Ultra Energy Puree and 1 PF&H 30 Energy Gel with 2 PF&H Electrolyte Capsules and water.",
      "carbs": 56,
      "sodium": 500
    },
    {
      "hour": 13,
      "action": "Sip 1 serving of PF&H Carb & Electrolyte Drink Mix diluted across the hour with plain water.",
      "carbs": 60,
      "sodium": 1000
    },
    {
      "hour": 14,
      "action": "Consume 1 Bix The Big 40 Energy Gel at 20 min, 1 PF&H Electrolyte Capsule at 40 min, and wash down with plain water.",
      "carbs": 40,
      "sodium": 450
    },
    {
      "hour": 15,
      "action": "Eat 1 Näak Ultra Energy Puree and 1 PF&H 30 Energy Gel with 2 PF&H Electrolyte Capsules and water.",
      "carbs": 56,
      "sodium": 500
    },
    {
      "hour": 16,
      "action": "Sip 1 serving of PF&H Carb & Electrolyte Drink Mix diluted across the hour with plain water.",
      "carbs": 60,
      "sodium": 1000
    },
    {
      "hour": 17,
      "action": "Consume 1 Bix The Big 40 Energy Gel at 20 min, 1 PF&H Electrolyte Capsule at 40 min, and wash down with plain water.",
      "carbs": 40,
      "sodium": 450
    },
    {
      "hour": 18,
      "action": "Eat 1 Näak Ultra Energy Puree and 1 PF&H 30 Energy Gel with 2 PF&H Electrolyte Capsules and water.",
      "carbs": 56,
      "sodium": 500
    },
    {
      "hour": 19,
      "action": "Sip 1 serving of PF&H Carb & Electrolyte Drink Mix diluted across the hour with plain water.",
      "carbs": 60,
      "sodium": 1000
    },
    {
      "hour": 20,
      "action": "Consume 1 Bix The Big 40 Energy Gel at 20 min, 1 PF&H Electrolyte Capsule at 40 min, and wash down with plain water.",
      "carbs": 40,
      "sodium": 450
    },
    {
      "hour": 21,
      "action": "Eat 1 Näak Ultra Energy Puree and 1 PF&H 30 Energy Gel with 2 PF&H Electrolyte Capsules and water.",
      "carbs": 56,
      "sodium": 500
    },
    {
      "hour": 22,
      "action": "Sip 1 serving of PF&H Carb & Electrolyte Drink Mix diluted across the hour with plain water.",
      "carbs": 60,
      "sodium": 1000
    },
    {
      "hour": 23,
      "action": "Consume 1 Bix The Big 40 Energy Gel at 20 min, 1 PF&H Electrolyte Capsule at 40 min, and wash down with plain water.",
      "carbs": 40,
      "sodium": 450
    },
    {
      "hour": 24,
      "action": "Eat 1 Näak Ultra Energy Puree and 1 PF&H 30 Energy Gel with 2 PF&H Electrolyte Capsules and water.",
      "carbs": 56,
      "sodium": 500
    },
    {
      "hour": 25,
      "action": "Sip 1 serving of PF&H Carb & Electrolyte Drink Mix diluted across the hour with plain water.",
      "carbs": 60,
      "sodium": 1000
    },
    {
      "hour": 26,
      "action": "Consume 1 Bix The Big 40 Energy Gel at 20 min, 1 PF&H Electrolyte Capsule at 40 min, and wash down with plain water.",
      "carbs": 40,
      "sodium": 450
    },
    {
      "hour": 27,
      "action": "Eat 1 Näak Ultra Energy Puree and 1 PF&H 30 Energy Gel with 2 PF&H Electrolyte Capsules and water.",
      "carbs": 56,
      "sodium": 500
    },
    {
      "hour": 28,
      "action": "Sip 1 serving of PF&H Carb & Electrolyte Drink Mix diluted across the hour with plain water.",
      "carbs": 60,
      "sodium": 1000
    },
    {
      "hour": 29,
      "action": "Consume 1 Bix The Big 40 Energy Gel at 20 min, 1 PF&H Electrolyte Capsule at 40 min, and wash down with plain water.",
      "carbs": 40,
      "sodium": 450
    },
    {
      "hour": 30,
      "action": "Eat 1 Näak Ultra Energy Puree and 1 PF&H 30 Energy Gel with 2 PF&H Electrolyte Capsules and water.",
      "carbs": 56,
      "sodium": 500
    }
  ],
  "tips": [
    "Rotate formats every hour between drink mix, high-density gels, and savory purees to prevent flavor fatigue and gastrointestinal distress across 30 hours.",
    "Always consume plain water alongside concentrated gels and purees to maintain optimal gut osmolality and prevent dehydration-induced gut shutdown.",
    "Decouple hydration from electrolytes as temperatures drop during the night segment, using PF&H Electrolyte Capsules to match sodium targets independently of fluid intake."
  ]
}
```
</details>

## nutrition_fixture_liquid_only

- Gemini+KB latency: **13.9s** (baseline: 5.0s)
- Catalog membership: ✅ all recommendations exist in the distilled catalog

<details><summary>Gemini+KB output</summary>

```json
{
  "products": [
    {
      "brand": "Tailwind Nutrition",
      "name": "Tailwind High Carb Fuel (Lemonade)",
      "total_quantity": 5,
      "carbs_per_unit": 90.0,
      "sodium_per_unit": 660.0,
      "protein_per_unit": 0.0,
      "tech_notes": "Optimized 2:1 glucose-to-fructose ratio, light taste, mixes easily. Use about two-thirds of a unit per hour to hit 60g carbs and about 440mg sodium, with plain water alongside. Avoids gels, which upset your stomach."
    }
  ],
  "hourly_plan": [
    {
      "hour": 1,
      "action": "Start drinking mixed Tailwind High Carb Fuel about 15-20 minutes in, with 300-600ml water per hour total; sip steadily",
      "carbs": 60.0,
      "sodium": 440.0
    },
    {
      "hour": 2,
      "action": "Continue steady sipping of mixed Tailwind; add small water refills at aid stations",
      "carbs": 60.0,
      "sodium": 440.0
    },
    {
      "hour": 3,
      "action": "Continue Tailwind sipping; monitor thirst and gut comfort, and adjust water intake for the heat",
      "carbs": 60.0,
      "sodium": 440.0
    },
    {
      "hour": 4,
      "action": "Continue Tailwind sipping during the climbing section; keep fluids steady rather than gulping",
      "carbs": 60.0,
      "sodium": 440.0
    },
    {
      "hour": 5,
      "action": "Continue Tailwind sipping; check urine color and body feel for dehydration signs",
      "carbs": 60.0,
      "sodium": 440.0
    },
    {
      "hour": 6,
      "action": "Continue Tailwind sipping; keep intake consistent even if appetite drops",
      "carbs": 60.0,
      "sodium": 440.0
    },
    {
      "hour": 7,
      "action": "Final hour: finish planned Tailwind intake and use remaining water for hydration as needed",
      "carbs": 60.0,
      "sodium": 440.0
    }
  ],
  "tips": [
    "Practice this exact Tailwind High Carb Fuel mix in training at 60g/h before race day, using the same concentration and water volume, to confirm gut tolerance in heat.",
    "Because the 25C heat and 2000m climb raise sweat losses, keep fluid intake at 300-600ml per hour and avoid over-drinking, which can overload the bladder and gut.",
    "Carry a spare mixed bottle or measured supply so no hourly dose is missed; your planned 5 units cover about 450g of carbs against a 420g target."
  ],
  "feedback_token": "504661d20c1003ff639c2ba5c1de9661.nutrition_lab.dbab8b2c6709f70135551eba34006480"
}
```
</details>
<details><summary>Captured baseline</summary>

```json
{
  "products": [
    {
      "brand": "Tailwind Nutrition",
      "name": "Tailwind Endurance Fuel",
      "total_quantity": 14,
      "carbs_per_unit": 25.0,
      "sodium_per_unit": 310,
      "protein_per_unit": 0.0,
      "tech_notes": "Employs a dual-carbohydrate formula of non-GMO dextrose (glucose) and non-GMO sucrose designed to match what the small intestine is built to absorb. This allows the carbohydrates to enter the bloodstream rapidly without causing digestive distress or \"gut bombs\". It provides complete calories, hydration, and electrolytes (sodium, potassium, magnesium, calcium) in a single mix, eliminating the need to supplement with other fuels like gels or salt pills. It contains no artificial dyes, preservatives, or complex chemical additives."
    },
    {
      "brand": "Tailwind Nutrition",
      "name": "Tailwind High Carb Fuel (Lemonade)",
      "total_quantity": 2,
      "carbs_per_unit": 90.0,
      "sodium_per_unit": 660,
      "protein_per_unit": 0.0,
      "tech_notes": "A power-packed drink mix engineered specifically for high-intensity efforts, delivering a higher carbohydrate concentration to maximize energy per sip. It utilizes an optimized 2:1 glucose-to-fructose ratio to increase carbohydrate absorption, lower perceived exertion, and accelerate recovery. It features a clean, refreshing, and light taste designed to mix easily and prevent sickliness or flavor fatigue even at high concentrations."
    }
  ],
  "hourly_plan": [
    {
      "hour": 1,
      "action": "Sip 2 servings (approx. 500-600ml) of Tailwind Endurance Fuel steadily across the hour",
      "carbs": 50.0,
      "sodium": 620
    },
    {
      "hour": 2,
      "action": "Sip 2 servings (approx. 500-600ml) of Tailwind Endurance Fuel steadily across the hour",
      "carbs": 50.0,
      "sodium": 620
    },
    {
      "hour": 3,
      "action": "Sip 2/3 packet (approx. 500-600ml) of Tailwind High Carb Fuel steadily across the hour",
      "carbs": 60.0,
      "sodium": 440
    },
    {
      "hour": 4,
      "action": "Sip 2 servings (approx. 500-600ml) of Tailwind Endurance Fuel steadily across the hour",
      "carbs": 50.0,
      "sodium": 620
    },
    {
      "hour": 5,
      "action": "Sip 2/3 packet (approx. 500-600ml) of Tailwind High Carb Fuel steadily across the hour",
      "carbs": 60.0,
      "sodium": 440
    },
    {
      "hour": 6,
      "action": "Sip 2 servings (approx. 500-600ml) of Tailwind Endurance Fuel steadily across the hour",
      "carbs": 50.0,
      "sodium": 620
    },
    {
      "hour": 7,
      "action": "Sip 2 servings (approx. 500-600ml) of Tailwind Endurance Fuel steadily across the hour",
      "carbs": 50.0,
      "sodium": 620
    }
  ],
  "tips": [
    "Sip fluid consistently every 10 to 15 minutes rather than drinking large volumes at aid stations to support rapid gastric emptying and avoid gut distension.",
    "In warm 25C conditions, monitor sweat rate and carry an extra flask of plain water to sip as needed if elevated thirst occurs alongside the electrolyte drink mix.",
    "Practice using your specific bottle concentrations in training long runs under race-intensity conditions to train gut tolerance and ensure complete digestive comfort."
  ]
}
```
</details>

## nutrition_fixture_no_preferences

- Gemini+KB latency: **10.4s** (baseline: 6.2s)
- Catalog membership: ✅ all recommendations exist in the distilled catalog

<details><summary>Gemini+KB output</summary>

```json
{
  "products": [
    {
      "brand": "Precision Fuel & Hydration",
      "name": "30 Energy Gel",
      "total_quantity": 16,
      "carbs_per_unit": 30,
      "sodium_per_unit": 0,
      "protein_per_unit": 0,
      "tech_notes": "Employs a 2:1 glucose-to-fructose ratio for fast-acting carbohydrate absorption with a mild, neutral Original flavor to limit palate fatigue. Texture reduces stickiness so it can be swallowed without a wash-down. Certified by Informed Sport."
    },
    {
      "brand": "Precision Fuel & Hydration",
      "name": "Electrolyte Capsules",
      "total_quantity": 16,
      "carbs_per_unit": 0,
      "sodium_per_unit": 250,
      "protein_per_unit": 0,
      "tech_notes": "Swallowable sodium capsules that decouple electrolyte intake from carbohydrate fueling. Two capsules per hour deliver the 500 mg/h sodium target while keeping carbohydrate math unchanged."
    }
  ],
  "hourly_plan": [
    {
      "hour": 1,
      "action": "Take 1 gel (30g) and 2 capsules (500mg sodium) with 300-600ml plain water; start fueling 15-20 minutes into the effort",
      "carbs": 60,
      "sodium": 500
    },
    {
      "hour": 2,
      "action": "Take 2 gels (60g total) and 2 capsules (500mg sodium) with 300-600ml plain water",
      "carbs": 60,
      "sodium": 500
    },
    {
      "hour": 3,
      "action": "Take 2 gels (60g total) and 2 capsules (500mg sodium) with 300-600ml plain water",
      "carbs": 60,
      "sodium": 500
    },
    {
      "hour": 4,
      "action": "Take 2 gels (60g total) and 2 capsules (500mg sodium) with 300-600ml plain water",
      "carbs": 60,
      "sodium": 500
    },
    {
      "hour": 5,
      "action": "Take 2 gels (60g total) and 2 capsules (500mg sodium) with 300-600ml plain water",
      "carbs": 60,
      "sodium": 500
    },
    {
      "hour": 6,
      "action": "Take 2 gels (60g total) and 2 capsules (500mg sodium) with 300-600ml plain water",
      "carbs": 60,
      "sodium": 500
    },
    {
      "hour": 7,
      "action": "Take 2 gels (60g total) and 2 capsules (500mg sodium) with 300-600ml plain water",
      "carbs": 60,
      "sodium": 500
    },
    {
      "hour": 8,
      "action": "Take 2 gels (60g total) and 2 capsules (500mg sodium) with 300-600ml plain water; finish the race fueled and hydrated",
      "carbs": 60,
      "sodium": 500
    }
  ],
  "tips": [
    "Rehearse this exact gel and capsule combination in training at 60g/h or higher, following a 2-week progressive loading protocol, so race day carries no GI surprises.",
    "Carry a spare gel beyond the plan and confirm aid station timing so no hourly dose is missed, since logistical slips are a common cause of energy dips.",
    "Drink plain water alongside each gel and adjust capsule count if weather is hot or you are a heavy sweater, while avoiding over-drinking that can dilute sodium and overload the bladder."
  ],
  "feedback_token": "9891e09a1274e72b43fa5a7045935cef.nutrition_lab.ddf0ed2bc1284bc80acc9131bda84473"
}
```
</details>
<details><summary>Captured baseline</summary>

```json
{
  "products": [
    {
      "brand": "Precision Fuel & Hydration",
      "name": "30 Energy Gel",
      "total_quantity": 8,
      "carbs_per_unit": 30.0,
      "sodium_per_unit": 0.0,
      "protein_per_unit": 0.0,
      "tech_notes": "Employs a 2:1 glucose-to-fructose ratio for fast-acting and highly efficient carbohydrate absorption. It is designed with a mild, neutral \"Original\" flavor profile to actively minimize the sweet taste overload and palate fatigue common during long efforts. The gel's texture is specifically engineered to reduce stickiness in the mouth, allowing it to be easily swallowed without requiring an immediate wash-down of plain water. Certified by Informed Sport."
    },
    {
      "brand": "Bix",
      "name": "Bix 30 Energy Gel – Salted Strawberry",
      "total_quantity": 8,
      "carbs_per_unit": 30.0,
      "sodium_per_unit": 300.0,
      "protein_per_unit": 0.0,
      "tech_notes": "Formulated with a 1:0.8 glucose-to-fructose ratio, this gel is vegan, uses natural flavors and colors, and is Informed Sport batch tested. It is designed specifically for longer efforts, hotter conditions, or heavy sweat to maintain an ideal balance between quick energy and robust electrolyte replenishment. Its natural strawberry flavor with a slightly salty finish is smooth, light, and engineered to prevent palate fatigue during long sessions."
    },
    {
      "brand": "Precision Fuel & Hydration",
      "name": "Electrolyte Capsules",
      "total_quantity": 8,
      "carbs_per_unit": 0.0,
      "sodium_per_unit": 250.0,
      "protein_per_unit": 0.0,
      "tech_notes": "Blister-packed swallowable capsules containing highly concentrated sodium. Designed to give athletes the ultimate flexibility to decouple their hydration/electrolyte intake from their carbohydrate fueling. This allows athletes to consume plain water or customized drink mixes from aid stations and separately ingest capsules to precisely match their genetically determined sweat sodium losses without altering their carbohydrate math or causing stomach upset."
    }
  ],
  "hourly_plan": [
    {
      "hour": 1,
      "action": "Take 1 Bix 30 Energy Gel – Salted Strawberry at minute 20, 1 PF 30 Energy Gel at minute 40, and 1 PF Electrolyte Capsule with water across the hour.",
      "carbs": 60.0,
      "sodium": 550.0
    },
    {
      "hour": 2,
      "action": "Take 1 Bix 30 Energy Gel – Salted Strawberry at minute 20, 1 PF 30 Energy Gel at minute 40, and 1 PF Electrolyte Capsule with water across the hour.",
      "carbs": 60.0,
      "sodium": 550.0
    },
    {
      "hour": 3,
      "action": "Take 1 Bix 30 Energy Gel – Salted Strawberry at minute 20, 1 PF 30 Energy Gel at minute 40, and 1 PF Electrolyte Capsule with water across the hour.",
      "carbs": 60.0,
      "sodium": 550.0
    },
    {
      "hour": 4,
      "action": "Take 1 Bix 30 Energy Gel – Salted Strawberry at minute 20, 1 PF 30 Energy Gel at minute 40, and 1 PF Electrolyte Capsule with water across the hour.",
      "carbs": 60.0,
      "sodium": 550.0
    },
    {
      "hour": 5,
      "action": "Take 1 Bix 30 Energy Gel – Salted Strawberry at minute 20, 1 PF 30 Energy Gel at minute 40, and 1 PF Electrolyte Capsule with water across the hour.",
      "carbs": 60.0,
      "sodium": 550.0
    },
    {
      "hour": 6,
      "action": "Take 1 Bix 30 Energy Gel – Salted Strawberry at minute 20, 1 PF 30 Energy Gel at minute 40, and 1 PF Electrolyte Capsule with water across the hour.",
      "carbs": 60.0,
      "sodium": 550.0
    },
    {
      "hour": 7,
      "action": "Take 1 Bix 30 Energy Gel – Salted Strawberry at minute 20, 1 PF 30 Energy Gel at minute 40, and 1 PF Electrolyte Capsule with water across the hour.",
      "carbs": 60.0,
      "sodium": 550.0
    },
    {
      "hour": 8,
      "action": "Take 1 Bix 30 Energy Gel – Salted Strawberry at minute 20, 1 PF 30 Energy Gel at minute 40, and 1 PF Electrolyte Capsule with water across the hour.",
      "carbs": 60.0,
      "sodium": 550.0
    }
  ],
  "tips": [
    "Always consume 300ml to 600ml of plain water per hour alongside gels to optimize gastric emptying and prevent hypertonic gut distress.",
    "Decoupling your sodium intake via electrolyte capsules allows dynamic electrolyte management without altering hourly carbohydrate math.",
    "Split carbohydrate intake into manageable 20 to 30 minute micro-doses instead of taking high single boluses to preserve GI comfort."
  ]
}
```
</details>

## nutrition_fixture_real_food_preference

- Gemini+KB latency: **19.9s** (baseline: 10.9s)
- Catalog membership: ✅ all recommendations exist in the distilled catalog

<details><summary>Gemini+KB output</summary>

```json
{
  "products": [
    {
      "brand": "Precision Fuel & Hydration",
      "name": "60 Energy Chew Bar",
      "total_quantity": 16,
      "carbs_per_unit": 60,
      "sodium_per_unit": 0,
      "protein_per_unit": 0,
      "tech_notes": "Solid chew format with high energy-to-weight ratio that helps break up flavor fatigue. Independently batch-tested and certified vegan. Use with plain water."
    },
    {
      "brand": "Precision Fuel & Hydration",
      "name": "30 Energy Chew",
      "total_quantity": 4,
      "carbs_per_unit": 30,
      "sodium_per_unit": 0,
      "protein_per_unit": 0,
      "tech_notes": "Original mild flavor chew, a satisfying solid bite that breaks up liquid-gel fatigue. Sodium not listed in catalog, so sodium is covered by electrolyte product."
    },
    {
      "brand": "Näak",
      "name": "Näak Ultra Energy™ Puree | Sweet Potatoes Butternut Squash",
      "total_quantity": 4,
      "carbs_per_unit": 26,
      "sodium_per_unit": 0,
      "protein_per_unit": 5,
      "tech_notes": "Savory real-food puree providing about 200 calories with a low glycemic index. Breaks up sweet flavor fatigue during long races. Sodium not listed in catalog, so sodium is covered by electrolyte product."
    },
    {
      "brand": "Precision Fuel & Hydration",
      "name": "500",
      "total_quantity": 20,
      "carbs_per_unit": 0,
      "sodium_per_unit": 500,
      "protein_per_unit": 0,
      "tech_notes": "Low-strength electrolyte supplement that delivers 500 mg sodium per serving to meet the hourly sodium target. Use with 300 to 600 ml of plain water each hour in warm conditions."
    }
  ],
  "hourly_plan": [
    {
      "hour": 1,
      "action": "Start chews 15 to 20 minutes into the run. Take 1 60 Energy Chew Bar with 500 mg sodium from 500 electrolyte and 400 to 500 ml water.",
      "carbs": 60,
      "sodium": 500
    },
    {
      "hour": 2,
      "action": "Take 1 60 Energy Chew Bar, 1 500 electrolyte, and 400 to 500 ml water.",
      "carbs": 60,
      "sodium": 500
    },
    {
      "hour": 3,
      "action": "Take 1 60 Energy Chew Bar, 1 500 electrolyte, and 400 to 500 ml water.",
      "carbs": 60,
      "sodium": 500
    },
    {
      "hour": 4,
      "action": "Take 1 60 Energy Chew Bar, 1 500 electrolyte, and 400 to 500 ml water.",
      "carbs": 60,
      "sodium": 500
    },
    {
      "hour": 5,
      "action": "Take 1 60 Energy Chew Bar, 1 500 electrolyte, and 400 to 500 ml water.",
      "carbs": 60,
      "sodium": 500
    },
    {
      "hour": 6,
      "action": "Take 1 60 Energy Chew Bar, 1 500 electrolyte, and 400 to 500 ml water.",
      "carbs": 60,
      "sodium": 500
    },
    {
      "hour": 7,
      "action": "Take 1 60 Energy Chew Bar, 1 500 electrolyte, and 400 to 500 ml water.",
      "carbs": 60,
      "sodium": 500
    },
    {
      "hour": 8,
      "action": "Take 1 60 Energy Chew Bar, 1 500 electrolyte, and 400 to 500 ml water.",
      "carbs": 60,
      "sodium": 500
    },
    {
      "hour": 9,
      "action": "Switch to real food: eat 1 Näak Ultra Energy Puree (26 g) plus 1 30 Energy Chew (30 g), with 1 500 electrolyte and 400 to 500 ml water.",
      "carbs": 56,
      "sodium": 500
    },
    {
      "hour": 10,
      "action": "Take 1 60 Energy Chew Bar, 1 500 electrolyte, and 400 to 500 ml water.",
      "carbs": 60,
      "sodium": 500
    },
    {
      "hour": 11,
      "action": "Take 1 60 Energy Chew Bar, 1 500 electrolyte, and 400 to 500 ml water.",
      "carbs": 60,
      "sodium": 500
    },
    {
      "hour": 12,
      "action": "Take 1 60 Energy Chew Bar, 1 500 electrolyte, and 400 to 500 ml water.",
      "carbs": 60,
      "sodium": 500
    },
    {
      "hour": 13,
      "action": "Eat 1 Näak Ultra Energy Puree plus 1 30 Energy Chew, with 1 500 electrolyte and 400 to 500 ml water. Expect climbing sections and slow down on steep terrain.",
      "carbs": 56,
      "sodium": 500
    },
    {
      "hour": 14,
      "action": "Take 1 60 Energy Chew Bar, 1 500 electrolyte, and 400 to 500 ml water.",
      "carbs": 60,
      "sodium": 500
    },
    {
      "hour": 15,
      "action": "Take 1 60 Energy Chew Bar, 1 500 electrolyte, and 400 to 500 ml water.",
      "carbs": 60,
      "sodium": 500
    },
    {
      "hour": 16,
      "action": "Take 1 60 Energy Chew Bar, 1 500 electrolyte, and 400 to 500 ml water.",
      "carbs": 60,
      "sodium": 500
    },
    {
      "hour": 17,
      "action": "Eat 1 Näak Ultra Energy Puree plus 1 30 Energy Chew, with 1 500 electrolyte and 400 to 500 ml water. Check for signs of dehydration or cramping.",
      "carbs": 56,
      "sodium": 500
    },
    {
      "hour": 18,
      "action": "Take 1 60 Energy Chew Bar, 1 500 electrolyte, and 400 to 500 ml water.",
      "carbs": 60,
      "sodium": 500
    },
    {
      "hour": 19,
      "action": "Take 1 60 Energy Chew Bar, 1 500 electrolyte, and 400 to 500 ml water.",
      "carbs": 60,
      "sodium": 500
    },
    {
      "hour": 20,
      "action": "Final push: eat 1 Näak Ultra Energy Puree plus 1 30 Energy Chew, with 1 500 electrolyte and 400 to 500 ml water. Finish strong.",
      "carbs": 56,
      "sodium": 500
    }
  ],
  "tips": [
    "Train this exact plan for 6 to 8 weeks, increasing carbs by about 10 g/h every 1 to 2 weeks toward 60 g/h and rehearsing the chew bars and puree at 20% above target intake.",
    "Drink 400 to 500 ml of plain water each hour at 28C and keep fluid and sodium balanced, avoiding over-drinking that can cause nausea or bladder issues.",
    "Carry spare chews and electrolytes, and use a 1000 or 1500 electrolyte-strength plan if you are a heavy sweater, adjusting sodium upward in heat and monitoring for cramping."
  ],
  "feedback_token": "22cbad2e823d9f3f257c41873e2fc1ef.nutrition_lab.723f263a4be4e486461dd211eed1bf2e"
}
```
</details>
<details><summary>Captured baseline</summary>

```json
{
  "products": [
    {
      "brand": "Precision Fuel & Hydration",
      "name": "60 Energy Chew Bar",
      "total_quantity": 10,
      "carbs_per_unit": 60.0,
      "sodium_per_unit": 0.0,
      "protein_per_unit": 0.0,
      "tech_notes": "Offers an outstanding energy-to-weight ratio, delivering 60g of carbohydrates for just 68g of weight. Provides a satisfying, solid chew format that helps prevent flavor fatigue and sits easily on sensitive stomachs during long training runs and ultra events. Available in Original (mild, neutral flavor), Mint & Lemon, and Combo Box formats. Certified vegan, uses no artificial ingredients, and is independently batch-tested."
    },
    {
      "brand": "Näak",
      "name": "Näak Ultra Energy™ Puree | Sweet Potatoes Butternut Squash",
      "total_quantity": 20,
      "carbs_per_unit": 26.0,
      "sodium_per_unit": 0.0,
      "protein_per_unit": 5.0,
      "tech_notes": "Developed as a savory food option for ultra-endurance athletes to provide 200 calories while actively breaking up sweet flavor fatigue during long training days or races. Constructed with a low glycemic index to deliver a slow, highly stable, and long-lasting stream of energy. Blends natural simple sugars (maple syrup) with complex carbohydrates (hydrolyzed oat flour). Utilizes highly digestible soy and pea proteins. Made using sustainable, upcycled, and organic ingredients, including sustainably grown Oregon sweet potatoes and malting barley protein upcycled from beer by-products."
    },
    {
      "brand": "Precision Fuel & Hydration",
      "name": "Electrolyte Capsules",
      "total_quantity": 40,
      "carbs_per_unit": 0.0,
      "sodium_per_unit": 250.0,
      "protein_per_unit": 0.0,
      "tech_notes": "Blister-packed swallowable capsules containing highly concentrated sodium. Designed to give athletes the ultimate flexibility to decouple their hydration/electrolyte intake from their carbohydrate fueling. This allows athletes to consume plain water or customized drink mixes from aid stations and separately ingest capsules to precisely match their genetically determined sweat sodium losses without altering their carbohydrate math or causing stomach upset."
    }
  ],
  "hourly_plan": [
    {
      "hour": 1,
      "action": "Consume 1 PF 60 Energy Chew Bar across the hour, paired with 2 PF Electrolyte Capsules and 500-750ml plain water.",
      "carbs": 60.0,
      "sodium": 500.0
    },
    {
      "hour": 2,
      "action": "Consume 2 pouches of Näak Ultra Energy Puree (approx. 52g carbs) along with 2 PF Electrolyte Capsules and fluid.",
      "carbs": 52.0,
      "sodium": 500.0
    },
    {
      "hour": 3,
      "action": "Consume 1 PF 60 Energy Chew Bar across the hour, paired with 2 PF Electrolyte Capsules and 500-750ml plain water.",
      "carbs": 60.0,
      "sodium": 500.0
    },
    {
      "hour": 4,
      "action": "Consume 2 pouches of Näak Ultra Energy Puree (approx. 52g carbs) along with 2 PF Electrolyte Capsules and fluid.",
      "carbs": 52.0,
      "sodium": 500.0
    },
    {
      "hour": 5,
      "action": "Consume 1 PF 60 Energy Chew Bar across the hour, paired with 2 PF Electrolyte Capsules and 500-750ml plain water.",
      "carbs": 60.0,
      "sodium": 500.0
    },
    {
      "hour": 6,
      "action": "Consume 2 pouches of Näak Ultra Energy Puree (approx. 52g carbs) along with 2 PF Electrolyte Capsules and fluid.",
      "carbs": 52.0,
      "sodium": 500.0
    },
    {
      "hour": 7,
      "action": "Consume 1 PF 60 Energy Chew Bar across the hour, paired with 2 PF Electrolyte Capsules and 500-750ml plain water.",
      "carbs": 60.0,
      "sodium": 500.0
    },
    {
      "hour": 8,
      "action": "Consume 2 pouches of Näak Ultra Energy Puree (approx. 52g carbs) along with 2 PF Electrolyte Capsules and fluid.",
      "carbs": 52.0,
      "sodium": 500.0
    },
    {
      "hour": 9,
      "action": "Consume 1 PF 60 Energy Chew Bar across the hour, paired with 2 PF Electrolyte Capsules and 500-750ml plain water.",
      "carbs": 60.0,
      "sodium": 500.0
    },
    {
      "hour": 10,
      "action": "Consume 2 pouches of Näak Ultra Energy Puree (approx. 52g carbs) along with 2 PF Electrolyte Capsules and fluid.",
      "carbs": 52.0,
      "sodium": 500.0
    },
    {
      "hour": 11,
      "action": "Consume 1 PF 60 Energy Chew Bar across the hour, paired with 2 PF Electrolyte Capsules and 500-750ml plain water.",
      "carbs": 60.0,
      "sodium": 500.0
    },
    {
      "hour": 12,
      "action": "Consume 2 pouches of Näak Ultra Energy Puree (approx. 52g carbs) along with 2 PF Electrolyte Capsules and fluid.",
      "carbs": 52.0,
      "sodium": 500.0
    },
    {
      "hour": 13,
      "action": "Consume 1 PF 60 Energy Chew Bar across the hour, paired with 2 PF Electrolyte Capsules and 500-750ml plain water.",
      "carbs": 60.0,
      "sodium": 500.0
    },
    {
      "hour": 14,
      "action": "Consume 2 pouches of Näak Ultra Energy Puree (approx. 52g carbs) along with 2 PF Electrolyte Capsules and fluid.",
      "carbs": 52.0,
      "sodium": 500.0
    },
    {
      "hour": 15,
      "action": "Consume 1 PF 60 Energy Chew Bar across the hour, paired with 2 PF Electrolyte Capsules and 500-750ml plain water.",
      "carbs": 60.0,
      "sodium": 500.0
    },
    {
      "hour": 16,
      "action": "Consume 2 pouches of Näak Ultra Energy Puree (approx. 52g carbs) along with 2 PF Electrolyte Capsules and fluid.",
      "carbs": 52.0,
      "sodium": 500.0
    },
    {
      "hour": 17,
      "action": "Consume 1 PF 60 Energy Chew Bar across the hour, paired with 2 PF Electrolyte Capsules and 500-750ml plain water.",
      "carbs": 60.0,
      "sodium": 500.0
    },
    {
      "hour": 18,
      "action": "Consume 2 pouches of Näak Ultra Energy Puree (approx. 52g carbs) along with 2 PF Electrolyte Capsules and fluid.",
      "carbs": 52.0,
      "sodium": 500.0
    },
    {
      "hour": 19,
      "action": "Consume 1 PF 60 Energy Chew Bar across the hour, paired with 2 PF Electrolyte Capsules and 500-750ml plain water.",
      "carbs": 60.0,
      "sodium": 500.0
    },
    {
      "hour": 20,
      "action": "Consume 2 pouches of Näak Ultra Energy Puree (approx. 52g carbs) along with 2 PF Electrolyte Capsules and fluid.",
      "carbs": 52.0,
      "sodium": 500.0
    }
  ],
  "tips": [
    "Manage heat-induced GI stress at 28C by decoupling carbohydrates from fluids; consume chews and purees in small nibbles every 15-20 minutes alongside plain water.",
    "Utilize 2 Precision Fuel Electrolyte Capsules per hour (500mg sodium) to hit your sodium target independently without altering food digestion or causing gut distress.",
    "Alternate between solid chews and savory vegetable purees across the 20 hours to prevent palate fatigue and avoid gastric slowdown from excessive sweetness."
  ]
}
```
</details>

## nutrition_fixture_short_21k_trail

- Gemini+KB latency: **11.9s** (baseline: 4.5s)
- Catalog membership: ✅ all recommendations exist in the distilled catalog

<details><summary>Gemini+KB output</summary>

```json
{
  "products": [
    {
      "brand": "Precision Fuel & Hydration",
      "name": "30 Energy Gel",
      "total_quantity": 5,
      "carbs_per_unit": 30,
      "sodium_per_unit": 0,
      "protein_per_unit": 0,
      "tech_notes": "Employs a 2:1 glucose-to-fructose ratio for fast-acting and highly efficient carbohydrate absorption. Mild, neutral Original flavor minimizes palate fatigue. Reduced stickiness allows swallowing without an immediate wash-down. Certified by Informed Sport."
    },
    {
      "brand": "Precision Fuel & Hydration",
      "name": "Electrolyte Capsules",
      "total_quantity": 5,
      "carbs_per_unit": 0,
      "sodium_per_unit": 250,
      "protein_per_unit": 0,
      "tech_notes": "Blister-packed swallowable capsules containing highly concentrated sodium. Decouples electrolyte intake from carbohydrate fueling so sodium can be adjusted without changing carb math or causing stomach upset."
    }
  ],
  "hourly_plan": [
    {
      "hour": 0,
      "action": "Pre-race: take 1 Precision Fuel 30 Energy Gel with water in the final 15-20 minutes before the start for a 30g carbohydrate hit, plus 1 Electrolyte Capsule (250mg sodium).",
      "carbs": 30,
      "sodium": 250
    },
    {
      "hour": 1,
      "action": "Start fueling 15-20 minutes into the run. Take 1 Energy Gel (30g carbs) every 30 minutes, plus 1 Electrolyte Capsule (250mg sodium) per 30 minutes, with 300-600ml of plain water per hour.",
      "carbs": 60,
      "sodium": 500
    },
    {
      "hour": 2,
      "action": "Continue 1 Energy Gel (30g carbs) every 30 minutes and 1 Electrolyte Capsule (250mg sodium) per 30 minutes, with 300-600ml of plain water per hour. Final 30 minutes: finish the race with water only.",
      "carbs": 60,
      "sodium": 500
    }
  ],
  "tips": [
    "Start fueling 15-20 minutes into the run and never skip gels; the 60g/h target is delivered as two 30g gels per hour.",
    "Drink 300-600ml of plain water per hour alongside gels and capsules to support gastric emptying and prevent gut shutdown.",
    "Practice this exact gel and capsule combination in training for 6-8 weeks, increasing intake gradually, so nothing new is introduced on race day."
  ],
  "feedback_token": "77532801c91dd91494a3cb047df026a6.nutrition_lab.e519a7218f2241bb21496c76ad9586d1"
}
```
</details>
<details><summary>Captured baseline</summary>

```json
{
  "products": [
    {
      "brand": "Precision Fuel & Hydration",
      "name": "30 Energy Gel",
      "total_quantity": 4,
      "carbs_per_unit": 30.0,
      "sodium_per_unit": 0.0,
      "protein_per_unit": 0.0,
      "tech_notes": "Employs a 2:1 glucose-to-fructose ratio for fast-acting and highly efficient carbohydrate absorption. It is designed with a mild, neutral \"Original\" flavor profile to actively minimize the sweet taste overload and palate fatigue common during long efforts. The gel's texture is specifically engineered to reduce stickiness in the mouth, allowing it to be easily swallowed without requiring an immediate wash-down of plain water. Certified by Informed Sport."
    },
    {
      "brand": "Precision Fuel & Hydration",
      "name": "500",
      "total_quantity": 3,
      "carbs_per_unit": 0.0,
      "sodium_per_unit": 500.0,
      "protein_per_unit": 0.0,
      "tech_notes": "Designed to support standard hydration and electrolyte maintenance for athletes with low sweat sodium concentration or for shorter efforts in mild conditions."
    }
  ],
  "hourly_plan": [
    {
      "hour": 1,
      "action": "Take one Precision Fuel & Hydration 30 Energy Gel at minute 20 and another at minute 40. Sip 500ml of water mixed with one Precision Fuel & Hydration 500 tablet across the hour.",
      "carbs": 60.0,
      "sodium": 500.0
    },
    {
      "hour": 2,
      "action": "Take one Precision Fuel & Hydration 30 Energy Gel at minute 80 and another at minute 100. Sip 500ml of water mixed with one Precision Fuel & Hydration 500 tablet across the hour.",
      "carbs": 60.0,
      "sodium": 500.0
    },
    {
      "hour": 3,
      "action": "For the remaining 30 minutes, sip 250ml of water containing half a Precision Fuel & Hydration 500 tablet to maintain hydration through the finish.",
      "carbs": 0.0,
      "sodium": 250.0
    }
  ],
  "tips": [
    "Take gels in small, regular doses every 20 minutes with sips of fluid rather than consuming a full packet at once, which optimizes stomach emptying and prevents GI distress.",
    "Decoupling your sodium and fluids from your carbohydrate gels allows you to scale fluid intake based on temperature without disrupting your hourly carbohydrate math.",
    "Practice this exact fueling plan in training at least 6 to 8 weeks out during your longest sessions to train your gut to absorb 60g of carbohydrates per hour comfortably."
  ]
}
```
</details>

## nutrition_fixture_specified_targets_low

- Gemini+KB latency: **13.7s** (baseline: 5.7s)
- Catalog membership: ✅ all recommendations exist in the distilled catalog

<details><summary>Gemini+KB output</summary>

```json
{
  "products": [
    {
      "brand": "Precision Fuel & Hydration",
      "name": "30 Energy Gel",
      "total_quantity": 5,
      "carbs_per_unit": 30,
      "sodium_per_unit": 0,
      "protein_per_unit": 0,
      "tech_notes": "2:1 glucose-to-fructose ratio for fast, efficient carbohydrate absorption with a mild neutral flavor that limits palate fatigue. Low-stickiness texture can be swallowed without a wash-down. Informed Sport certified."
    },
    {
      "brand": "GU",
      "name": "Original Energy Gel",
      "total_quantity": 5,
      "carbs_per_unit": 22,
      "sodium_per_unit": 60,
      "protein_per_unit": 0,
      "tech_notes": "Dual-source maltodextrin and fructose blend with 450mg BCAAs and sodium to support fluid balance and carbohydrate absorption. Good tolerance for beginners at moderate hourly intake."
    },
    {
      "brand": "Precision Fuel & Hydration",
      "name": "Electrolyte Capsules",
      "total_quantity": 5,
      "carbs_per_unit": 0,
      "sodium_per_unit": 250,
      "protein_per_unit": 0,
      "tech_notes": "Swallowable sodium capsules that decouple electrolytes from carbohydrate fueling. Taken with water to top up the sodium target without changing carbohydrate math."
    }
  ],
  "hourly_plan": [
    {
      "hour": 1,
      "action": "Start fueling 15-20 minutes in: take 1 Precision Fuel 30 Energy Gel and 1 GU Original Energy Gel with about 300-400ml plain water, then take 1 Electrolyte Capsule with water",
      "carbs": 52,
      "sodium": 310
    },
    {
      "hour": 2,
      "action": "Take 1 Precision Fuel 30 Energy Gel and 1 GU Original Energy Gel with about 300-400ml water, then 1 Electrolyte Capsule with water",
      "carbs": 52,
      "sodium": 310
    },
    {
      "hour": 3,
      "action": "Take 1 Precision Fuel 30 Energy Gel and 1 GU Original Energy Gel with about 300-400ml water, then 1 Electrolyte Capsule with water",
      "carbs": 52,
      "sodium": 310
    },
    {
      "hour": 4,
      "action": "Take 1 Precision Fuel 30 Energy Gel and 1 GU Original Energy Gel with about 300-400ml water, then 1 Electrolyte Capsule with water",
      "carbs": 52,
      "sodium": 310
    },
    {
      "hour": 5,
      "action": "Final partial hour (about 30 minutes): take 1 Precision Fuel 30 Energy Gel with water and 1 Electrolyte Capsule if needed to finish the race",
      "carbs": 30,
      "sodium": 250
    }
  ],
  "tips": [
    "Train this exact gel and capsule combination 6-8 weeks before race day, increasing intake by about 10g/h every 1-2 weeks, so the gut is adapted before you race.",
    "Sip plain water steadily alongside gels (roughly 300-600ml per hour) and avoid over-drinking, which can cause bloating and an unplanned stop.",
    "Take gels in small doses every 15-20 minutes rather than large boluses, and carry spares so a missed or dropped gel does not cut your intake."
  ],
  "feedback_token": "6fb1ee033819ac57cd496d6a5051b524.nutrition_lab.ce0e6262f070e9af4b6d0da9978a3b71"
}
```
</details>
<details><summary>Captured baseline</summary>

```json
{
  "products": [
    {
      "brand": "Precision Fuel & Hydration",
      "name": "30 Energy Gel",
      "total_quantity": 5,
      "carbs_per_unit": 30.0,
      "sodium_per_unit": 0.0,
      "protein_per_unit": 0.0,
      "tech_notes": "Employs a 2:1 glucose-to-fructose ratio for fast-acting and highly efficient carbohydrate absorption. It is designed with a mild, neutral \"Original\" flavor profile to actively minimize the sweet taste overload and palate fatigue common during long efforts. The gel's texture is specifically engineered to reduce stickiness in the mouth, allowing it to be easily swallowed without requiring an immediate wash-down of plain water. Certified by Informed Sport."
    },
    {
      "brand": "GU",
      "name": "Original Energy Gel",
      "total_quantity": 4,
      "carbs_per_unit": 22.0,
      "sodium_per_unit": 60.0,
      "protein_per_unit": 0.0,
      "tech_notes": "Uses a dual-source carbohydrate blend of maltodextrin and fructose. The maltodextrin converts quickly to energy molecules within minutes, while the fructose absorbs more slowly to provide a steady stream of energy, preventing the insulin spikes and subsequent sugar crashes associated with simple sugars. Formulated with a BCAA blend (L-Leucine, L-Valine, and L-Isoleucine) to help protect working muscles from breakdown, aid in energy production, and prevent mental fatigue during exertion. Contains sodium to maintain fluid balance and aid carbohydrate absorption. Contains 450mg of branched-chain amino acids (BCAAs)."
    },
    {
      "brand": "Precision Fuel & Hydration",
      "name": "Electrolyte Capsules",
      "total_quantity": 5,
      "carbs_per_unit": 0.0,
      "sodium_per_unit": 250.0,
      "protein_per_unit": 0.0,
      "tech_notes": "Blister-packed swallowable capsules containing highly concentrated sodium. Designed to give athletes the ultimate flexibility to decouple their hydration/electrolyte intake from their carbohydrate fueling. This allows athletes to consume plain water or customized drink mixes from aid stations and separately ingest capsules to precisely match their genetically determined sweat sodium losses without altering their carbohydrate math or causing stomach upset."
    }
  ],
  "hourly_plan": [
    {
      "hour": 1,
      "action": "Consume 1 PF 30 Energy Gel at minute 20, 1 GU Original Energy Gel at minute 45, and take 1 PF Electrolyte Capsule with 400-500ml of plain water across the hour.",
      "carbs": 52.0,
      "sodium": 310.0
    },
    {
      "hour": 2,
      "action": "Consume 1 PF 30 Energy Gel at minute 20, 1 GU Original Energy Gel at minute 45, and take 1 PF Electrolyte Capsule with 400-500ml of plain water across the hour.",
      "carbs": 52.0,
      "sodium": 310.0
    },
    {
      "hour": 3,
      "action": "Consume 1 PF 30 Energy Gel at minute 20, 1 GU Original Energy Gel at minute 45, and take 1 PF Electrolyte Capsule with 400-500ml of plain water across the hour.",
      "carbs": 52.0,
      "sodium": 310.0
    },
    {
      "hour": 4,
      "action": "Consume 1 PF 30 Energy Gel at minute 20, 1 GU Original Energy Gel at minute 45, and take 1 PF Electrolyte Capsule with 400-500ml of plain water across the hour.",
      "carbs": 52.0,
      "sodium": 310.0
    },
    {
      "hour": 5,
      "action": "During the final 30 minutes, consume 1 PF 30 Energy Gel at minute 15 and take 1 PF Electrolyte Capsule with 200-250ml plain water.",
      "carbs": 30.0,
      "sodium": 250.0
    }
  ],
  "tips": [
    "Always ingest 300ml to 500ml of plain water per hour alongside gels and electrolyte capsules to maintain appropriate gut osmolality and prevent delayed gastric emptying or nausea.",
    "Split your hourly carbohydrate target into smaller, frequent doses every 20 to 25 minutes rather than taking all fuel in a single bolus, reducing gastrointestinal stress on climbs.",
    "Carry one extra gel and electrolyte capsule as emergency spares to accommodate pacing fluctuations or accidental drops on technical terrain."
  ]
}
```
</details>
