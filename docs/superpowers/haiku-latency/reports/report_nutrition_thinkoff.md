# Golden report — nutrition


## nutrition_fixture_caffeine_sensitive

- Gemini+KB latency: **12.2s** (baseline: 5.8s)
- Catalog membership: ✅ all recommendations exist in the distilled catalog

<details><summary>Gemini+KB output</summary>

```json
{
  "products": [
    {
      "brand": "GU",
      "name": "Original Energy Gel",
      "total_quantity": 8,
      "carbs_per_unit": 22,
      "sodium_per_unit": 60,
      "protein_per_unit": 0,
      "tech_notes": "Dual-source maltodextrin and fructose, non-caffeinated, gentle on the stomach for steady hourly carbs."
    },
    {
      "brand": "Precision Fuel & Hydration",
      "name": "Carb & Electrolyte Drink Mix",
      "total_quantity": 8,
      "carbs_per_unit": 60,
      "sodium_per_unit": 1000,
      "protein_per_unit": 0,
      "tech_notes": "2:1 glucose-to-fructose drink mix, non-caffeinated; provides carbs and sodium in one bottle, supplemented with plain water."
    },
    {
      "brand": "Precision Fuel & Hydration",
      "name": "Electrolyte Capsules",
      "total_quantity": 8,
      "carbs_per_unit": 0,
      "sodium_per_unit": 250,
      "protein_per_unit": 0,
      "tech_notes": "Swallowable sodium capsules to top up sodium independently of carbohydrate intake."
    }
  ],
  "hourly_plan": [
    {
      "hour": 1,
      "action": "Sip Carb & Electrolyte Drink Mix (about 500 ml) and take 1 Original Energy Gel at 15-20 minutes in; sip plain water with each gel.",
      "carbs": 60,
      "sodium": 500
    },
    {
      "hour": 2,
      "action": "Sip Carb & Electrolyte Drink Mix and take 1 Original Energy Gel with plain water; consider 1 Electrolyte Capsule if sweating heavily.",
      "carbs": 60,
      "sodium": 500
    },
    {
      "hour": 3,
      "action": "Sip Carb & Electrolyte Drink Mix and take 1 Original Energy Gel with plain water while climbing.",
      "carbs": 60,
      "sodium": 500
    },
    {
      "hour": 4,
      "action": "Sip Carb & Electrolyte Drink Mix and take 1 Original Energy Gel with plain water; reassess fluid and sodium needs.",
      "carbs": 60,
      "sodium": 500
    },
    {
      "hour": 5,
      "action": "Sip Carb & Electrolyte Drink Mix and take 1 Original Energy Gel with plain water; use Electrolyte Capsule if cramping risk rises.",
      "carbs": 60,
      "sodium": 500
    },
    {
      "hour": 6,
      "action": "Sip Carb & Electrolyte Drink Mix and take 1 Original Energy Gel with plain water to maintain steady intake.",
      "carbs": 60,
      "sodium": 500
    },
    {
      "hour": 7,
      "action": "Sip Carb & Electrolyte Drink Mix and take 1 Original Energy Gel with plain water in the final push.",
      "carbs": 60,
      "sodium": 500
    },
    {
      "hour": 8,
      "action": "Finish remaining fluid and any final gel as tolerated; avoid forcing intake if nauseous.",
      "carbs": 60,
      "sodium": 500
    }
  ],
  "tips": [
    "Practise this exact plan in training 6 to 8 weeks out, increasing carbs by about 10 g/h every 1 to 2 weeks to build gut tolerance.",
    "Pair every gel and drink with plain water (roughly 300 to 600 ml per hour) to support gastric emptying and absorption.",
    "Because you are caffeine sensitive, all recommended products are caffeine-free; avoid switching to caffeinated gels on race day."
  ],
  "feedback_token": "7fb8e1d8fef93c62413a7f268e6cf31f.nutrition_lab.a04593826635d3f36da203c399625193"
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

- Gemini+KB latency: **8.0s** (baseline: 6.2s)
- Catalog membership: ✅ all recommendations exist in the distilled catalog

<details><summary>Gemini+KB output</summary>

```json
{
  "products": [
    {
      "brand": "Hammer",
      "name": "Hammer Gel (Vanilla)",
      "total_quantity": 8,
      "carbs_per_unit": 21,
      "sodium_per_unit": 25,
      "protein_per_unit": 0,
      "tech_notes": "Mild, neutral flavor that can be blended with other flavors to reduce palate fatigue; suitable for long-duration efforts in cold conditions."
    },
    {
      "brand": "Precision Fuel & Hydration",
      "name": "Carb & Electrolyte Drink Mix",
      "total_quantity": 4,
      "carbs_per_unit": 60,
      "sodium_per_unit": 1000,
      "protein_per_unit": 0,
      "tech_notes": "2:1 glucose-to-fructose drink with 1000 mg sodium per serving; supplies both carbohydrate and sodium with a mild neutral taste, ideal for steady hourly delivery."
    },
    {
      "brand": "Precision Fuel & Hydration",
      "name": "Electrolyte Capsules",
      "total_quantity": 8,
      "carbs_per_unit": 0,
      "sodium_per_unit": 250,
      "protein_per_unit": 0,
      "tech_notes": "Decoupled sodium source for topping up sodium on demand without altering carbohydrate math; useful in cold conditions where sweat sodium may be lower than in heat."
    }
  ],
  "hourly_plan": [
    {
      "hour": 1,
      "action": "Start fueling 15-20 min in; 1 Hammer Gel (Vanilla) plus drink mix sipped with water, then continue steady intake",
      "carbs": 60,
      "sodium": 500
    },
    {
      "hour": 2,
      "action": "1 Hammer Gel (Vanilla) plus drink mix, 1 electrolyte capsule with water",
      "carbs": 60,
      "sodium": 500
    },
    {
      "hour": 3,
      "action": "1 Hammer Gel (Vanilla) plus drink mix, 1 electrolyte capsule with water",
      "carbs": 60,
      "sodium": 500
    },
    {
      "hour": 4,
      "action": "1 Hammer Gel (Vanilla) plus drink mix, 1 electrolyte capsule with water",
      "carbs": 60,
      "sodium": 500
    },
    {
      "hour": 5,
      "action": "1 Hammer Gel (Vanilla) plus drink mix, 1 electrolyte capsule with water",
      "carbs": 60,
      "sodium": 500
    },
    {
      "hour": 6,
      "action": "1 Hammer Gel (Vanilla) plus drink mix, 1 electrolyte capsule with water",
      "carbs": 60,
      "sodium": 500
    },
    {
      "hour": 7,
      "action": "Finish fueling with remaining gel and drink mix, sip water to finish",
      "carbs": 60,
      "sodium": 500
    }
  ],
  "tips": [
    "Use Hammer Gel (Vanilla) and Precision Fuel Carb & Electrolyte Drink Mix; no Hammer or Precision Fuel brand constraint conflicts exist, so these choices meet the requested format and brand mix.",
    "Keep fluids near 300-600 ml per hour in cold conditions, sipping plain water with gels to support gastric emptying, and avoid overdrinking at altitude.",
    "Start fueling 15-20 minutes into the run and take small, frequent doses every 15-20 minutes rather than large boluses, since cold and altitude can reduce gut blood flow and digestion."
  ],
  "feedback_token": "39554b67279bb37009399ac58b8bf1f1.nutrition_lab.1ff8f9bca62b6a49ca307ffc7c79c467"
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

- Gemini+KB latency: **8.4s** (baseline: 4.8s)
- Catalog membership: ✅ all recommendations exist in the distilled catalog

<details><summary>Gemini+KB output</summary>

```json
{
  "products": [
    {
      "brand": "Hammer",
      "name": "Hammer Gel (Vanilla)",
      "total_quantity": 4,
      "carbs_per_unit": 21,
      "sodium_per_unit": 25,
      "protein_per_unit": 0,
      "tech_notes": "Mild, widely tolerated flavor; mix with other flavors to reduce palate fatigue. Use as primary hourly carb source with water."
    },
    {
      "brand": "GU",
      "name": "Roctane Energy Gel",
      "total_quantity": 4,
      "carbs_per_unit": 21,
      "sodium_per_unit": 125,
      "protein_per_unit": 0,
      "tech_notes": "Higher sodium per packet to supplement hourly sodium target alongside carb gels."
    },
    {
      "brand": "Precision Fuel & Hydration",
      "name": "500",
      "total_quantity": 2,
      "carbs_per_unit": 0,
      "sodium_per_unit": 500,
      "protein_per_unit": 0,
      "tech_notes": "Low-strength electrolyte tablet/powder for cool conditions to support the 500 mg/h sodium target."
    }
  ],
  "hourly_plan": [
    {
      "hour": 1,
      "action": "Start first gel at 15-20 min; sip plain water with gel; take one Roctane gel with water at ~45 min",
      "carbs": 42,
      "sodium": 150
    },
    {
      "hour": 2,
      "action": "One Hammer Vanilla gel every 20 min plus electrolyte tablet dissolved in 500 ml water",
      "carbs": 63,
      "sodium": 250
    },
    {
      "hour": 3,
      "action": "Continue gel every 20 min with plain water; take one Roctane gel for sodium top-up",
      "carbs": 63,
      "sodium": 300
    }
  ],
  "tips": [
    "Start carbs 15-20 minutes into the run and keep intake near 60 g/h, spaced in small doses every 15-20 minutes.",
    "Drink 300-600 ml of fluid per hour; in 12C conditions aim toward the lower end and avoid overdrinking.",
    "Do not use untested products on race day; rehearse this exact gel and electrolyte combination in training first."
  ],
  "feedback_token": "45c4ab996369aad10fed27ed0fafa8aa.nutrition_lab.05f3d86257e4496e8f4e0f04744e02f8"
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

- Gemini+KB latency: **11.5s** (baseline: 6.1s)
- Catalog membership: ✅ all recommendations exist in the distilled catalog

<details><summary>Gemini+KB output</summary>

```json
{
  "products": [
    {
      "brand": "Maurten",
      "name": "Gel 100",
      "total_quantity": 12,
      "carbs_per_unit": 25,
      "sodium_per_unit": 0,
      "protein_per_unit": 0,
      "tech_notes": "Hydrogel firm gel, 0.8:1 fructose-to-glucose ratio, no water required; use as the bulk of hourly carbs, pairs well with intake every 15 minutes."
    },
    {
      "brand": "Maurten",
      "name": "Gel 160",
      "total_quantity": 6,
      "carbs_per_unit": 40,
      "sodium_per_unit": 0,
      "protein_per_unit": 0,
      "tech_notes": "Large-format hydrogel gel with 40g carbs per unit, useful for hitting higher hourly carb targets with fewer packets."
    },
    {
      "brand": "Maurten",
      "name": "Drink Mix 320",
      "total_quantity": 8,
      "carbs_per_unit": 80,
      "sodium_per_unit": 0,
      "protein_per_unit": 0,
      "tech_notes": "High-concentration hydrogel drink mix, 80g carbs per 500ml; primary hourly carb source for steady intake and fluid volume."
    },
    {
      "brand": "Precision Fuel & Hydration",
      "name": "Electrolyte Capsules",
      "total_quantity": 22,
      "carbs_per_unit": 0,
      "sodium_per_unit": 250,
      "protein_per_unit": 0,
      "tech_notes": "Swallowable sodium capsules decoupled from carbs; take roughly 3 per hour to reach 800mg sodium target while keeping carb math separate."
    },
    {
      "brand": "Precision Fuel & Hydration",
      "name": "Carb Only Drink Mix",
      "total_quantity": 4,
      "carbs_per_unit": 120,
      "sodium_per_unit": 0,
      "protein_per_unit": 0,
      "tech_notes": "Zero-sodium 2:1 glucose-fructose mix allowing up to 120g/hr from bottles; useful for topping up carbs in hot or long segments."
    },
    {
      "brand": "Precision Fuel & Hydration",
      "name": "30 Energy Chew",
      "total_quantity": 10,
      "carbs_per_unit": 30,
      "sodium_per_unit": 0,
      "protein_per_unit": 0,
      "tech_notes": "Solid chew option to break up flavor fatigue during later hours of the 11-hour effort."
    }
  ],
  "hourly_plan": [
    {
      "hour": 1,
      "action": "Start carbs 15-20 min in: 1 Maurten Gel 100 plus 500ml Drink Mix 320 bottle sips; 2 electrolyte capsules",
      "carbs": 100,
      "sodium": 500
    },
    {
      "hour": 2,
      "action": "1 Maurten Gel 100, 1 Drink Mix 320 bottle, 1 Gel 160 at checkpoint, 3 electrolyte capsules",
      "carbs": 120,
      "sodium": 750
    },
    {
      "hour": 3,
      "action": "Drink Mix 320 bottle, 1 Gel 100, 3 electrolyte capsules, plain water per fluid needs",
      "carbs": 105,
      "sodium": 750
    },
    {
      "hour": 4,
      "action": "Gel 160, 30 Energy Chew, Carb Only Drink Mix bottle, 3 electrolyte capsules",
      "carbs": 100,
      "sodium": 750
    },
    {
      "hour": 5,
      "action": "Drink Mix 320 bottle, 1 Gel 100, 3 electrolyte capsules",
      "carbs": 105,
      "sodium": 750
    },
    {
      "hour": 6,
      "action": "Gel 160, 30 Energy Chew, 3 electrolyte capsules, water with mix",
      "carbs": 100,
      "sodium": 750
    },
    {
      "hour": 7,
      "action": "Drink Mix 320 bottle, 1 Gel 100, 3 electrolyte capsules",
      "carbs": 105,
      "sodium": 750
    },
    {
      "hour": 8,
      "action": "Carb Only Drink Mix bottle, Gel 160, 3 electrolyte capsules",
      "carbs": 100,
      "sodium": 750
    },
    {
      "hour": 9,
      "action": "Drink Mix 320 bottle, 30 Energy Chew, 3 electrolyte capsules",
      "carbs": 100,
      "sodium": 750
    },
    {
      "hour": 10,
      "action": "Gel 100, Drink Mix 320 bottle, 3 electrolyte capsules",
      "carbs": 105,
      "sodium": 750
    },
    {
      "hour": 11,
      "action": "Final push: Gel 160 and Drink Mix 320 sips, 3 electrolyte capsules",
      "carbs": 120,
      "sodium": 750
    }
  ],
  "tips": [
    "Start fueling 15-20 minutes into the race and eat small doses every 15 minutes rather than large boluses; practice this exact plan in training since 100g/h is well above typical intake and requires dedicated gut training over 6-8 weeks.",
    "Keep plain water alongside hydrogel products and use the electrolyte capsules to hit roughly 800mg sodium per hour independently of carb intake, adjusting capsule count if sweat rate runs high.",
    "Mix formats (hydrogel gels, drink mix, chews) to reduce palate fatigue over 11 hours and carry spare Gel 100 packets in case of logistical gaps at aid stations."
  ],
  "feedback_token": "7095c9ce935ee189dbaf4276207247b5.nutrition_lab.7bb95f3e6205f47df776f5c7a9f7f3a4"
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

- Gemini+KB latency: **9.6s** (baseline: 6.2s)
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
      "tech_notes": "Hydrogel-based carbohydrate drink mix for longer, lower-intensity racing; 40g carbs per unit. Sodium not listed in knowledge base, so electrolytes must be covered separately."
    },
    {
      "brand": "Maurten",
      "name": "Gel 100",
      "total_quantity": 12,
      "carbs_per_unit": 25,
      "sodium_per_unit": 0,
      "protein_per_unit": 0,
      "tech_notes": "Firm hydrogel energy gel in a 0.8:1 fructose-to-glucose ratio; 25g carbs per unit. Sodium not listed in knowledge base."
    },
    {
      "brand": "Maurten",
      "name": "Gel 160",
      "total_quantity": 4,
      "carbs_per_unit": 40,
      "sodium_per_unit": 0,
      "protein_per_unit": 0,
      "tech_notes": "Large-format firm hydrogel gel with 40g carbs per unit; useful for hitting higher hourly targets with less packaging. Sodium not listed in knowledge base."
    }
  ],
  "hourly_plan": [
    {
      "hour": 1,
      "action": "Start Drink Mix 160 at 15-20 min in, plus 1 Gel 100 at 30 min; drink plain water with each intake, approx 500 ml/h total, sip electrolytes as needed under heat",
      "carbs": 60,
      "sodium": 0
    },
    {
      "hour": 2,
      "action": "Drink Mix 160 plus 1 Gel 100; continue water at approx 500 ml/h and take sodium-based electrolytes to reach roughly 1000 mg/h total",
      "carbs": 60,
      "sodium": 0
    },
    {
      "hour": 3,
      "action": "Gel 160 at start of hour plus Gel 100 at mid-hour; maintain 500 ml/h water intake and electrolytes in heat",
      "carbs": 65,
      "sodium": 0
    },
    {
      "hour": 4,
      "action": "Drink Mix 160 plus 1 Gel 100; monitor sweat losses and body weight, keep fluids steady at 500 ml/h",
      "carbs": 60,
      "sodium": 0
    },
    {
      "hour": 5,
      "action": "Drink Mix 160 plus 1 Gel 100; increase electrolyte intake for climbing and heat, aiming for approx 1000 mg/h sodium",
      "carbs": 60,
      "sodium": 0
    },
    {
      "hour": 6,
      "action": "Gel 160 plus Gel 100; continue water at 500 ml/h, use cool water or ice on hot sections to limit heat strain",
      "carbs": 65,
      "sodium": 0
    },
    {
      "hour": 7,
      "action": "Drink Mix 160 plus 1 Gel 100; keep carb and fluid intake consistent to protect glycogen for final push",
      "carbs": 60,
      "sodium": 0
    },
    {
      "hour": 8,
      "action": "Final Gel 100 if needed for finish; water as tolerated; avoid new products in final hour",
      "carbs": 25,
      "sodium": 0
    }
  ],
  "tips": [
    "Maurten products in the knowledge base list no sodium, so cover the 1000 mg/h sodium target with separate electrolyte capsules or tablets and verify labels before race day.",
    "Gut-train at least 6-8 weeks before the race, progressing carbs by about 10 g/h every 1-2 weeks and rehearsing exact products and fluid volumes at race-like heat.",
    "Monitor body mass and cramping during the race; losses above 2% body weight impair performance, so adjust water and sodium intake in the heat as needed."
  ],
  "feedback_token": "fce53fcd0294fc08cb771da30643231a.nutrition_lab.d4fdab1f1609ba5b6395058f8a052eae"
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

- Gemini+KB latency: **8.6s** (baseline: 5.5s)
- Catalog membership: ✅ all recommendations exist in the distilled catalog

<details><summary>Gemini+KB output</summary>

```json
{
  "products": [
    {
      "brand": "Precision Fuel & Hydration",
      "name": "1000",
      "total_quantity": 14,
      "carbs_per_unit": 0,
      "sodium_per_unit": 1000,
      "protein_per_unit": 0,
      "tech_notes": "High-strength electrolyte supplement matched to heavy salty sweaters in hot conditions; supports sodium target of 1000mg/h."
    },
    {
      "brand": "Precision Fuel & Hydration",
      "name": "Carb & Electrolyte Drink Mix",
      "total_quantity": 14,
      "carbs_per_unit": 60,
      "sodium_per_unit": 1000,
      "protein_per_unit": 0,
      "tech_notes": "2:1 glucose-to-fructose drink mix delivering 60g carbs and 1000mg sodium per serving, meeting both hourly targets in one product; neutral taste for hot-weather palate fatigue."
    },
    {
      "brand": "Precision Fuel & Hydration",
      "name": "30 Energy Gel",
      "total_quantity": 14,
      "carbs_per_unit": 30,
      "sodium_per_unit": 0,
      "protein_per_unit": 0,
      "tech_notes": "Backup fueling for flexibility in carb delivery; mild neutral flavor and low-stickiness texture suited to heat."
    }
  ],
  "hourly_plan": [
    {
      "hour": 1,
      "action": "Carb & Electrolyte Drink Mix (1 serving in 500ml water) plus 1000 electrolyte tablet with fluids",
      "carbs": 60,
      "sodium": 1000
    },
    {
      "hour": 2,
      "action": "Carb & Electrolyte Drink Mix (1 serving in 500ml water) plus 1000 electrolyte tablet with fluids",
      "carbs": 60,
      "sodium": 1000
    },
    {
      "hour": 3,
      "action": "Carb & Electrolyte Drink Mix (1 serving in 500ml water) plus 1000 electrolyte tablet with fluids",
      "carbs": 60,
      "sodium": 1000
    },
    {
      "hour": 4,
      "action": "Carb & Electrolyte Drink Mix (1 serving in 500ml water) plus 1000 electrolyte tablet with fluids",
      "carbs": 60,
      "sodium": 1000
    },
    {
      "hour": 5,
      "action": "Carb & Electrolyte Drink Mix (1 serving in 500ml water) plus 1000 electrolyte tablet with fluids",
      "carbs": 60,
      "sodium": 1000
    },
    {
      "hour": 6,
      "action": "Carb & Electrolyte Drink Mix (1 serving in 500ml water) plus 1000 electrolyte tablet with fluids",
      "carbs": 60,
      "sodium": 1000
    },
    {
      "hour": 7,
      "action": "Carb & Electrolyte Drink Mix (1 serving in 500ml water) plus 1000 electrolyte tablet with fluids",
      "carbs": 60,
      "sodium": 1000
    },
    {
      "hour": 8,
      "action": "Carb & Electrolyte Drink Mix (1 serving in 500ml water) plus 1000 electrolyte tablet with fluids",
      "carbs": 60,
      "sodium": 1000
    },
    {
      "hour": 9,
      "action": "Carb & Electrolyte Drink Mix (1 serving in 500ml water) plus 1000 electrolyte tablet with fluids",
      "carbs": 60,
      "sodium": 1000
    },
    {
      "hour": 10,
      "action": "Carb & Electrolyte Drink Mix (1 serving in 500ml water) plus 1000 electrolyte tablet with fluids",
      "carbs": 60,
      "sodium": 1000
    },
    {
      "hour": 11,
      "action": "Carb & Electrolyte Drink Mix (1 serving in 500ml water) plus 1000 electrolyte tablet with fluids",
      "carbs": 60,
      "sodium": 1000
    },
    {
      "hour": 12,
      "action": "Carb & Electrolyte Drink Mix (1 serving in 500ml water) plus 1000 electrolyte tablet with fluids",
      "carbs": 60,
      "sodium": 1000
    },
    {
      "hour": 13,
      "action": "Carb & Electrolyte Drink Mix (1 serving in 500ml water) plus 1000 electrolyte tablet with fluids",
      "carbs": 60,
      "sodium": 1000
    },
    {
      "hour": 14,
      "action": "Carb & Electrolyte Drink Mix (1 serving in 500ml water) plus 1000 electrolyte tablet with fluids",
      "carbs": 60,
      "sodium": 1000
    }
  ],
  "tips": [
    "Heavy salty sweating in 32C, 85% humidity means sweat losses far exceed normal; pre-load with 1500 electrolyte drink the night before and on race morning, finishing 45-60 minutes before the start.",
    "Sip fluids every 10-15 minutes rather than large boluses, and watch for cramping as an early dehydration signal; add extra 1000 capsules at aid stations if cramps appear.",
    "Climb sections (4000m gain) reduce gut tolerance; if nausea occurs, switch briefly to the 30 Energy Gel with plain water and resume the drink mix once stable."
  ],
  "feedback_token": "a50d3c740a6d4794df9236af21152db0.nutrition_lab.ed445aa81d7ecc458ba84c408b6bb97e"
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

- Gemini+KB latency: **9.6s** (baseline: 10.2s)
- Catalog membership: ✅ all recommendations exist in the distilled catalog

<details><summary>Gemini+KB output</summary>

```json
{
  "products": [
    {
      "brand": "GU",
      "name": "Roctane Energy Gel",
      "total_quantity": 30,
      "carbs_per_unit": 21,
      "sodium_per_unit": 125,
      "protein_per_unit": 0,
      "tech_notes": "Dual-source gel with BCAAs and electrolytes; supports long-duration efforts. Use alongside water."
    },
    {
      "brand": "Tailwind Nutrition",
      "name": "Tailwind Endurance Fuel",
      "total_quantity": 20,
      "carbs_per_unit": 25.0,
      "sodium_per_unit": 310,
      "protein_per_unit": 0.0,
      "tech_notes": "Complete drink mix providing carbs, sodium and electrolytes in a single bottle; ideal for hourly drink-based fueling."
    },
    {
      "brand": "Näak",
      "name": "Ultra Energy™ Puree | Sweet Potatoes Butternut Squash",
      "total_quantity": 6,
      "carbs_per_unit": 26,
      "sodium_per_unit": 0,
      "protein_per_unit": 5,
      "tech_notes": "Savory real-food option to break up sweet flavor fatigue during overnight hours; low glycemic, easy to eat."
    },
    {
      "brand": "Näak",
      "name": "Ultra Energy™ Waffle | Salted Caramel",
      "total_quantity": 6,
      "carbs_per_unit": 16,
      "sodium_per_unit": 0,
      "protein_per_unit": 3,
      "tech_notes": "Solid, soft-textured snack for variety in later race hours when gels become unappealing."
    }
  ],
  "hourly_plan": [
    {
      "hour": 1,
      "action": "Drink Tailwind Endurance Fuel (1 serving) with water; take 1 GU Roctane gel",
      "carbs": 62,
      "sodium": 435
    },
    {
      "hour": 2,
      "action": "Drink Tailwind Endurance Fuel (1 serving) with water; take 1 GU Roctane gel",
      "carbs": 62,
      "sodium": 435
    },
    {
      "hour": 3,
      "action": "Drink Tailwind Endurance Fuel (1 serving); take 1 Näak Waffle Salted Caramel",
      "carbs": 41,
      "sodium": 310
    },
    {
      "hour": 4,
      "action": "Drink Tailwind Endurance Fuel (1 serving) with water; take 1 GU Roctane gel",
      "carbs": 62,
      "sodium": 435
    },
    {
      "hour": 5,
      "action": "Drink Tailwind Endurance Fuel (1 serving); take 1 Näak Puree",
      "carbs": 51,
      "sodium": 310
    },
    {
      "hour": 6,
      "action": "Drink Tailwind Endurance Fuel (1 serving) with water; take 1 GU Roctane gel",
      "carbs": 62,
      "sodium": 435
    },
    {
      "hour": 7,
      "action": "Drink Tailwind Endurance Fuel (1 serving); take 1 Näak Waffle Salted Caramel",
      "carbs": 41,
      "sodium": 310
    },
    {
      "hour": 8,
      "action": "Drink Tailwind Endurance Fuel (1 serving) with water; take 1 GU Roctane gel",
      "carbs": 62,
      "sodium": 435
    },
    {
      "hour": 9,
      "action": "Drink Tailwind Endurance Fuel (1 serving); take 1 Näak Puree",
      "carbs": 51,
      "sodium": 310
    },
    {
      "hour": 10,
      "action": "Drink Tailwind Endurance Fuel (1 serving) with water; take 1 GU Roctane gel",
      "carbs": 62,
      "sodium": 435
    },
    {
      "hour": 11,
      "action": "Drink Tailwind Endurance Fuel (1 serving); take 1 Näak Waffle Salted Caramel",
      "carbs": 41,
      "sodium": 310
    },
    {
      "hour": 12,
      "action": "Drink Tailwind Endurance Fuel (1 serving) with water; take 1 GU Roctane gel",
      "carbs": 62,
      "sodium": 435
    }
  ],
  "tips": [
    "Shows no Tailwind or GU stock conflicts; keep hourly sodium near 500 mg by adding electrolyte capsules in cold overnight sections if sweat losses rise.",
    "Stick to small, frequent intakes (every 15-20 min) on the climbs and avoid fat-heavy real food, which slows gastric emptying under hard effort.",
    "Carry a spare gel and waffle in the vest, and drink 300-600 ml per hour of plain water to protect gut absorption through the 30-hour window."
  ],
  "feedback_token": "34cff399893d5db7652921060512aa35.nutrition_lab.fe76e5346820fa7cf862752cedc4e93f"
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

- Gemini+KB latency: **8.3s** (baseline: 5.0s)
- Catalog membership: ✅ all recommendations exist in the distilled catalog

<details><summary>Gemini+KB output</summary>

```json
{
  "products": [
    {
      "brand": "Tailwind Nutrition",
      "name": "Tailwind Endurance Fuel",
      "total_quantity": 7,
      "carbs_per_unit": 25.0,
      "sodium_per_unit": 310,
      "protein_per_unit": 0.0,
      "tech_notes": "Dual-carbohydrate dextrose and sucrose formula providing carbs, electrolytes and hydration in one mix; avoids gels that upset the stomach. Per-unit values in the knowledge base are per serving, so 7 units supports roughly 60g carbs/hour across 7 hours with a flask per hour."
    },
    {
      "brand": "Tailwind Nutrition",
      "name": "Tailwind High Carb Fuel (Lemonade)",
      "total_quantity": 4,
      "carbs_per_unit": 90.0,
      "sodium_per_unit": 660,
      "protein_per_unit": 0.0,
      "tech_notes": "High-concentration 2:1 glucose-to-fructose mix for use on the most demanding climbing sections or as a concentrated backup to reach hourly targets without adding bottles."
    }
  ],
  "hourly_plan": [
    {
      "hour": 1,
      "action": "Start sipping Tailwind Endurance Fuel from the bottle every 15 minutes, with plain water as needed; begin carbohydrate intake 15-20 minutes into the run",
      "carbs": 60,
      "sodium": 500
    },
    {
      "hour": 2,
      "action": "Continue Tailwind Endurance Fuel, sipping steadily; add water to match sweat rate in the 25C heat",
      "carbs": 60,
      "sodium": 500
    },
    {
      "hour": 3,
      "action": "Continue Tailwind Endurance Fuel; use one High Carb Fuel serving on the major climb to lift intake while maintaining fluid balance",
      "carbs": 60,
      "sodium": 500
    },
    {
      "hour": 4,
      "action": "Continue Tailwind Endurance Fuel; check thirst, urine color and body weight trend to avoid losing more than 2% body mass",
      "carbs": 60,
      "sodium": 500
    },
    {
      "hour": 5,
      "action": "Continue Tailwind Endurance Fuel; keep sipping every 15 minutes and add plain water at aid stations",
      "carbs": 60,
      "sodium": 500
    },
    {
      "hour": 6,
      "action": "Continue Tailwind Endurance Fuel; use remaining High Carb Fuel serving if fatigue or palate fatigue is noticed",
      "carbs": 60,
      "sodium": 500
    },
    {
      "hour": 7,
      "action": "Finish final Tailwind Endurance Fuel flask; take a last small carbohydrate dose in the final 30 minutes to sustain effort to the line",
      "carbs": 60,
      "sodium": 500
    }
  ],
  "tips": [
    "Because gels upset your stomach, rely almost entirely on Tailwind drink mixes and sip small amounts every 15 minutes rather than gulping large volumes.",
    "Pair your Tailwind bottles with plain water and monitor body weight, keeping losses under 2% in the 25C heat to protect performance and prevent cramping.",
    "Practise this exact Tailwind plan in training at 60g/h for several weeks before race day, increasing gradually by about 10g/h every 1-2 weeks to build gut tolerance."
  ],
  "feedback_token": "f1bd42b39b7104293a3baa454c08e441.nutrition_lab.95c1f5d28aed1842be1f2b3c95a00055"
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

- Gemini+KB latency: **8.4s** (baseline: 6.2s)
- Catalog membership: ✅ all recommendations exist in the distilled catalog

<details><summary>Gemini+KB output</summary>

```json
{
  "products": [
    {
      "brand": "Hammer",
      "name": "Hammer Gel (Vanilla)",
      "total_quantity": 10,
      "carbs_per_unit": 21,
      "sodium_per_unit": 25,
      "protein_per_unit": 0,
      "tech_notes": "Mild, widely tolerated flavor; can be blended with other Hammer flavors to reduce palate fatigue over long efforts."
    },
    {
      "brand": "Precision Fuel & Hydration",
      "name": "1000",
      "total_quantity": 4,
      "carbs_per_unit": 0,
      "sodium_per_unit": 1000,
      "protein_per_unit": 0,
      "tech_notes": "High-strength electrolyte tablet/powder for moderately salty sweaters or hot conditions; supplies sodium independently of carbohydrate intake."
    },
    {
      "brand": "Precision Fuel & Hydration",
      "name": "Carb Only Drink Mix",
      "total_quantity": 2,
      "carbs_per_unit": 120,
      "sodium_per_unit": 0,
      "protein_per_unit": 0,
      "tech_notes": "Zero-sodium 2:1 glucose-fructose mix with a clean neutral taste; allows carbohydrate and sodium to be managed independently."
    }
  ],
  "hourly_plan": [
    {
      "hour": 1,
      "action": "Consume 1 Hammer Gel (Vanilla) at 15 min and 45 min; sip water from bottle; take 1000 mg electrolyte tablet with first aid station.",
      "carbs": 42,
      "sodium": 550
    },
    {
      "hour": 2,
      "action": "Mix Carb Only Drink Mix into bottle for ~60g carbs across the hour; sip steadily with water; 1 Hammer Gel at 30 min.",
      "carbs": 60,
      "sodium": 25
    },
    {
      "hour": 3,
      "action": "Continue carb drink mix sipping and 1 Hammer Gel; take 1000 mg electrolyte tablet mid-hour.",
      "carbs": 60,
      "sodium": 525
    },
    {
      "hour": 4,
      "action": "Sip carb drink mix and water; 1 Hammer Gel at 30 min; monitor gut comfort and sweat rate.",
      "carbs": 60,
      "sodium": 25
    },
    {
      "hour": 5,
      "action": "Continue carb drink mix and gel schedule; take 1000 mg electrolyte tablet with aid station fluids.",
      "carbs": 60,
      "sodium": 525
    },
    {
      "hour": 6,
      "action": "Sip carb drink mix and water; 1 Hammer Gel at 30 min to maintain steady carbohydrate delivery.",
      "carbs": 60,
      "sodium": 25
    },
    {
      "hour": 7,
      "action": "Maintain carb drink mix sipping, 1 Hammer Gel, and 1000 mg electrolyte tablet to cover heavier sodium losses late in race.",
      "carbs": 60,
      "sodium": 525
    },
    {
      "hour": 8,
      "action": "Final hour: sip remaining carb drink mix and water; use last gel only if needed for finish push.",
      "carbs": 60,
      "sodium": 25
    }
  ],
  "tips": [
    "Practice this exact fueling in long training sessions 6 to 8 weeks out and progressively build toward 60 g/h, training at 20% above target before race day.",
    "Drink plain water alongside gels and drink mix (roughly 300 to 600 ml per hour) so the concentrated carbohydrate is absorbed and gut osmolality stays manageable.",
    "Use the sodium tablets to hit roughly 500 mg/h on average; increase to the 1500 mg-level product only if you are a heavy sweater or racing in heat, after testing."
  ],
  "feedback_token": "bb2bb5c1f53ed3d6fdcd497b2922eddc.nutrition_lab.556fa9ca0224b4d0584689061d32776b"
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

- Gemini+KB latency: **10.9s** (baseline: 10.9s)
- Catalog membership: ✅ all recommendations exist in the distilled catalog

<details><summary>Gemini+KB output</summary>

```json
{
  "products": [
    {
      "brand": "Precision Fuel & Hydration",
      "name": "60 Energy Chew Bar",
      "total_quantity": 20,
      "carbs_per_unit": 60,
      "sodium_per_unit": 0,
      "protein_per_unit": 0,
      "tech_notes": "Solid chew format with high carb-to-weight ratio; helps break up flavor fatigue on long efforts. Use roughly one bar per hour, portioned across the hour."
    },
    {
      "brand": "Precision Fuel & Hydration",
      "name": "30 Energy Chew",
      "total_quantity": 40,
      "carbs_per_unit": 30,
      "sodium_per_unit": 0,
      "protein_per_unit": 0,
      "tech_notes": "Chew format for flexible hourly dosing and palate relief; pair with sodium source as needed."
    },
    {
      "brand": "Precision Fuel & Hydration",
      "name": "500",
      "total_quantity": 20,
      "carbs_per_unit": 0,
      "sodium_per_unit": 500,
      "protein_per_unit": 0,
      "tech_notes": "Low-strength electrolyte tablet matched to a ~500 mg/h sodium target in warm conditions; take with water between chews."
    },
    {
      "brand": "Precision Fuel & Hydration",
      "name": "Electrolyte Capsules",
      "total_quantity": 20,
      "carbs_per_unit": 0,
      "sodium_per_unit": 250,
      "protein_per_unit": 0,
      "tech_notes": "Swallowable sodium capsules let you decouple salt from carbs and adjust for heat without changing carb math."
    }
  ],
  "hourly_plan": [
    {
      "hour": 1,
      "action": "Eat 1 Energy Chew Bar (60g) in 15-minute portions; drink 500 ml water; take 1 electrolyte tablet early in the hour",
      "carbs": 60,
      "sodium": 500
    },
    {
      "hour": 2,
      "action": "Eat 1 Energy Chew Bar (60g) in 15-minute portions; drink 500 ml water; take 1 electrolyte tablet early in the hour",
      "carbs": 60,
      "sodium": 500
    },
    {
      "hour": 3,
      "action": "Eat 1 Energy Chew Bar (60g) in 15-minute portions; drink 500 ml water; take 1 electrolyte tablet early in the hour",
      "carbs": 60,
      "sodium": 500
    },
    {
      "hour": 4,
      "action": "Eat 1 Energy Chew Bar (60g) plus real food (salted potato or pretzels) at aid station; drink 500 ml water; take 1 electrolyte tablet",
      "carbs": 60,
      "sodium": 500
    },
    {
      "hour": 5,
      "action": "Eat 1 Energy Chew Bar (60g) in 15-minute portions; drink 500 ml water; take 1 electrolyte tablet early in the hour",
      "carbs": 60,
      "sodium": 500
    },
    {
      "hour": 6,
      "action": "Eat 1 Energy Chew Bar (60g) plus salted broth or rice at aid station; drink 500 ml water; take 1 electrolyte tablet",
      "carbs": 60,
      "sodium": 500
    },
    {
      "hour": 7,
      "action": "Eat 1 Energy Chew Bar (60g) in 15-minute portions; drink 500 ml water; take 1 electrolyte tablet early in the hour",
      "carbs": 60,
      "sodium": 500
    },
    {
      "hour": 8,
      "action": "Eat 1 Energy Chew Bar (60g) plus real food at aid station; drink 500 ml water; take 1 electrolyte tablet",
      "carbs": 60,
      "sodium": 500
    },
    {
      "hour": 9,
      "action": "Eat 1 Energy Chew Bar (60g) in 15-minute portions; drink 500 ml water; take 1 electrolyte tablet early in the hour",
      "carbs": 60,
      "sodium": 500
    },
    {
      "hour": 10,
      "action": "Eat 1 Energy Chew Bar (60g) plus real food at aid station; drink 500 ml water; take 1 electrolyte tablet",
      "carbs": 60,
      "sodium": 500
    },
    {
      "hour": 11,
      "action": "Eat 1 Energy Chew Bar (60g) in 15-minute portions; drink 500 ml water; take 1 electrolyte tablet early in the hour",
      "carbs": 60,
      "sodium": 500
    },
    {
      "hour": 12,
      "action": "Eat 1 Energy Chew Bar (60g) plus salted real food; drink 500 ml water; take 1 electrolyte tablet",
      "carbs": 60,
      "sodium": 500
    },
    {
      "hour": 13,
      "action": "Eat 1 Energy Chew Bar (60g) in 15-minute portions; drink 500 ml water; take 1 electrolyte tablet early in the hour",
      "carbs": 60,
      "sodium": 500
    },
    {
      "hour": 14,
      "action": "Eat 1 Energy Chew Bar (60g) plus real food at aid station; drink 500 ml water; take 1 electrolyte tablet",
      "carbs": 60,
      "sodium": 500
    },
    {
      "hour": 15,
      "action": "Eat 1 Energy Chew Bar (60g) in 15-minute portions; drink 500 ml water; take 1 electrolyte tablet early in the hour",
      "carbs": 60,
      "sodium": 500
    },
    {
      "hour": 16,
      "action": "Eat 1 Energy Chew Bar (60g) plus salted real food; drink 500 ml water; take 1 electrolyte tablet",
      "carbs": 60,
      "sodium": 500
    },
    {
      "hour": 17,
      "action": "Eat 1 Energy Chew Bar (60g) in 15-minute portions; drink 500 ml water; take 1 electrolyte tablet early in the hour",
      "carbs": 60,
      "sodium": 500
    },
    {
      "hour": 18,
      "action": "Eat 1 Energy Chew Bar (60g) plus real food at aid station; drink 500 ml water; take 1 electrolyte tablet",
      "carbs": 60,
      "sodium": 500
    },
    {
      "hour": 19,
      "action": "Eat 1 Energy Chew Bar (60g) in 15-minute portions; drink 500 ml water; take 1 electrolyte tablet early in the hour",
      "carbs": 60,
      "sodium": 500
    },
    {
      "hour": 20,
      "action": "Eat 1 Energy Chew Bar (60g) plus salted real food; drink 500 ml water; take 1 electrolyte tablet",
      "carbs": 60,
      "sodium": 500
    }
  ],
  "tips": [
    "Knowledge base has no Chew-only brand besides Precision Fuel & Hydration for the chew format; sourced all products from it, which satisfies the brand preference set to Any.",
    "Start fueling 15-20 minutes into the run and sip water steadily (300-600 ml per hour, more in the 28C heat) to support gastric emptying and carb transport.",
    "Rotate salted real food (potato, pretzels, broth) at aid stations every 2-3 hours to offset flavor fatigue and keep sodium on track; test all products in training first."
  ],
  "feedback_token": "353a975fa7186036025aa60b0ca662ef.nutrition_lab.7ec7ac8e5292443fdab3329ac3676e40"
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

- Gemini+KB latency: **7.2s** (baseline: 4.5s)
- Catalog membership: ✅ all recommendations exist in the distilled catalog

<details><summary>Gemini+KB output</summary>

```json
{
  "products": [
    {
      "brand": "GU",
      "name": "Original Energy Gel",
      "total_quantity": 3,
      "carbs_per_unit": 22,
      "sodium_per_unit": 60,
      "protein_per_unit": 0,
      "tech_notes": "Dual-source maltodextrin and fructose gel with BCAAs. Take with water to aid absorption and avoid stomach upset during a beginner race."
    },
    {
      "brand": "GU",
      "name": "Hydration Drink Tabs",
      "total_quantity": 2,
      "carbs_per_unit": 0,
      "sodium_per_unit": 320,
      "protein_per_unit": 0,
      "tech_notes": "Dissolve in 16oz water to supply sodium and potassium. Two tabs cover roughly the 500mg/hour sodium target when paired with gels."
    }
  ],
  "hourly_plan": [
    {
      "hour": 1,
      "action": "Start first gel 15-20 minutes in, take one Original Energy Gel with 300-400ml water; sip electrolyte drink from Hydration Drink Tabs",
      "carbs": 44,
      "sodium": 380
    },
    {
      "hour": 2,
      "action": "Take one Original Energy Gel with water and electrolyte drink, sipping steadily",
      "carbs": 44,
      "sodium": 380
    },
    {
      "hour": 3,
      "action": "Take remaining Original Energy Gel with water; finish race with plain water as needed",
      "carbs": 22,
      "sodium": 60
    }
  ],
  "tips": [
    "Start fueling 15-20 minutes into the race and take small, regular doses rather than large boluses to protect the gut.",
    "Pair every gel with water (300-400ml per hour) so carbohydrates absorb properly, and avoid over-drinking.",
    "Practice this exact gel and tab combination during training before race day so nothing is new on the start line."
  ],
  "feedback_token": "8f9173805d0e7a4cef5309f310782f6e.nutrition_lab.e1adae8646f18c7cfca9f51437b98f74"
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

- Gemini+KB latency: **7.2s** (baseline: 5.7s)
- Catalog membership: ✅ all recommendations exist in the distilled catalog

<details><summary>Gemini+KB output</summary>

```json
{
  "products": [
    {
      "brand": "Hammer",
      "name": "Hammer Gel (Orange)",
      "total_quantity": 5,
      "carbs_per_unit": 22,
      "sodium_per_unit": 30,
      "protein_per_unit": 0,
      "tech_notes": "Vegan-friendly flavor option with a light, mild citrus profile suited to a beginner's palate; take with plain water to aid absorption."
    },
    {
      "brand": "GU",
      "name": "Hydration Drink Tabs",
      "total_quantity": 5,
      "carbs_per_unit": 0,
      "sodium_per_unit": 320,
      "protein_per_unit": 0,
      "tech_notes": "Dissolve one tab per 16oz water to supply sodium and potassium; provides the bulk of the hourly sodium target."
    },
    {
      "brand": "Maurten",
      "name": "Gel 100",
      "total_quantity": 3,
      "carbs_per_unit": 25,
      "sodium_per_unit": 0,
      "protein_per_unit": 0,
      "tech_notes": "Firm hydrogel texture that goes down without wash-down water; a good option as a palate-friendly alternative to syrupy gels."
    }
  ],
  "hourly_plan": [
    {
      "hour": 1,
      "action": "Start fueling 15-20 min in: 1 Hammer Gel (Orange) with 300ml plain water; 1 Hydration Drink Tab in 500ml water",
      "carbs": 44,
      "sodium": 320
    },
    {
      "hour": 2,
      "action": "1 Gel 100 with water; continue hydration tab in 500ml water",
      "carbs": 25,
      "sodium": 320
    },
    {
      "hour": 3,
      "action": "1 Hammer Gel (Orange) with 300ml plain water; 1 Hydration Drink Tab in 500ml water",
      "carbs": 22,
      "sodium": 320
    },
    {
      "hour": 4,
      "action": "1 Gel 100 with water; continue hydration tab in 500ml water",
      "carbs": 25,
      "sodium": 320
    }
  ],
  "tips": [
    "Start fueling 15-20 minutes into the run and sip water with every gel to support absorption and gastric emptying.",
    "Your target of 50g carbs/hour is met most cleanly by pairing a Hammer Gel with a Gel 100 each hour; never skip water, as dehydration shuts down carb absorption.",
    "Practise this exact plan in training for 6-8 weeks, progressively building intake by ~10g/h, so your gut is comfortable on race day."
  ],
  "feedback_token": "8cbbc41b696f3dbcf99623bcdd7979b2.nutrition_lab.b78eb9ea97fcb44faaa4fe6c49f1dec5"
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
