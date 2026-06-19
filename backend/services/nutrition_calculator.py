from typing import List, Dict, Any

class NutritionCalculator:
    @staticmethod
    def calculate_fueling_strategy(
        duration_hours: float,
        sweat_rate: str,       # 'low', 'moderate', 'high'
        weather_temp: str,     # 'cool', 'moderate', 'hot'
        products: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Calculates fluid, sodium, and carbohydrate targets per hour based on 
        race duration, sweat index, and weather metrics.
        Matches targets against products in database to return an hourly recipe.
        """
        sweat_rate = sweat_rate.lower()
        weather_temp = weather_temp.lower()

        # 1. Calculate Carbohydrate Targets (grams / hour)
        if duration_hours < 1.0:
            target_carbs_hr = 0.0
            carb_complexity = "None"
        elif duration_hours <= 2.5:
            target_carbs_hr = 45.0
            carb_complexity = "Moderate (standard absorption)"
        elif duration_hours <= 6.0:
            target_carbs_hr = 75.0
            carb_complexity = "High (requires multi-transport carbs)"
        else:
            target_carbs_hr = 90.0
            carb_complexity = "Extreme (requires gut training and glucose-fructose ratios)"

        # 2. Calculate Fluid and Sodium Targets (per hour)
        # Fluid base range in ml/hr
        if sweat_rate == "low" or weather_temp == "cool":
            target_fluid_ml_hr = 500.0
            target_sodium_mg_hr = 400.0
        elif sweat_rate == "high" or weather_temp == "hot":
            target_fluid_ml_hr = 850.0
            target_sodium_mg_hr = 1000.0
        else:
            target_fluid_ml_hr = 650.0
            target_sodium_mg_hr = 650.0

        # Adjust for hot extreme weather
        if weather_temp == "hot":
            target_fluid_ml_hr += 100.0
            target_sodium_mg_hr += 200.0

        # 3. Solver Recipe: Find combinations of products to hit target
        # Filter products into gels and drink mixes
        gels = [p for p in products if p["type"] == "gel"]
        mixes = [p for p in products if p["type"] == "drink_mix"]
        
        recipe_products = []
        rec_carbs = 0.0
        rec_sodium = 0.0
        rec_caffeine = 0.0
        rec_fluid = 0.0

        # Rule-based matching heuristics:
        if target_carbs_hr > 0:
            # If sodium is high, prioritize drink mixes first
            if target_sodium_mg_hr >= 600.0 and mixes:
                # Add 1 scoop/serving of drink mix
                mix = mixes[0]
                recipe_products.append({"product": f"{mix['brand']} {mix['name']}", "qty": 1, "type": "drink_mix"})
                rec_carbs += mix["carbs_grams"]
                rec_sodium += mix["sodium_mg"]
                rec_caffeine += mix["caffeine_mg"]
                rec_fluid += mix["water_ratio_ml"]

            # Fill remaining carbs with gels
            if rec_carbs < target_carbs_hr and gels:
                gel = gels[0]
                needed_gel_carbs = target_carbs_hr - rec_carbs
                # Calculate integer quantities of gels (e.g. 1 or 2 gels)
                qty = max(1, round(needed_gel_carbs / gel["carbs_grams"]))
                recipe_products.append({"product": f"{gel['brand']} {gel['name']}", "qty": qty, "type": "gel"})
                rec_carbs += gel["carbs_grams"] * qty
                rec_sodium += gel["sodium_mg"] * qty
                rec_caffeine += gel["caffeine_mg"] * qty

            # If sodium is still too low, add electrolyte-rich drinks or advise salt capsules
            if rec_sodium < target_sodium_mg_hr - 200.0:
                # Add a drink mix if not already added
                has_mix = any(item["type"] == "drink_mix" for item in recipe_products)
                if not has_mix and mixes:
                    mix = mixes[0]
                    recipe_products.append({"product": f"{mix['brand']} {mix['name']}", "qty": 1, "type": "drink_mix"})
                    rec_carbs += mix["carbs_grams"]
                    rec_sodium += mix["sodium_mg"]
                    rec_fluid += mix["water_ratio_ml"]

        # Default fluid recommendation matches water mixing volume or baseline target
        recommended_fluid_ml = max(target_fluid_ml_hr, rec_fluid)

        # 4. Warnings and Notes
        warnings = []
        if target_carbs_hr >= 90.0:
            warnings.append(
                "WARNING: Target carb intake is at elite level (90g+/hr). "
                "This requires dynamic gut-training blocks in your training plan. "
                "Do not attempt this on race day without multiple practice blocks."
            )
        if rec_sodium > 1200.0:
            warnings.append(
                "CAUTION: Extremely high sodium intake. Check sweat test data to confirm. "
                "Ensure fluid volume matches salt intake to prevent GI distress."
            )

        return {
            "targets": {
                "carbs_grams_per_hour": target_carbs_hr,
                "sodium_mg_per_hour": target_sodium_mg_hr,
                "fluid_ml_per_hour": target_fluid_ml_hr,
                "carb_complexity": carb_complexity
            },
            "recommended_hourly_recipe": recipe_products,
            "recipe_totals": {
                "carbs_grams": round(rec_carbs, 1),
                "sodium_mg": round(rec_sodium, 1),
                "caffeine_mg": round(rec_caffeine, 1),
                "fluid_ml": round(recommended_fluid_ml, 1)
            },
            "warnings": warnings
        }
