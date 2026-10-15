# Nepali Diet Recommendation System — Datasets Guide

This folder contains all the standardized datasets used across the project for ML training, rule evaluation, nutritional calculations, and recipe composition.

---

## Dataset Overview & Sources

| Dataset File | Source / Basis | Description & Role |
| :--- | :--- | :--- |
| **`food_table_clean.csv`** | **DFTQC 2012** (Govt. of Nepal) | 225 authentic Nepali raw and cooked food items with 6 core nutritional vitals (Calories, Protein, Carbs, Fat, Fiber, Omega-3) and medical parameters (Sodium, Sugar). |
| **`nepali_recipes.csv`** | **Authentic Nepali Cuisine** | 125+ traditional recipes (Dal Bhat, Dhindo, Momos, Thukpa, Kwati, Gundruk, etc.) mapped to ingredient food IDs and base compositions. |
| **`medical_food_rules.csv`** | **WHO / ADA Clinical Guidelines** | Evidence-based rule set defining nutrient cutoffs, daily limits, and ranking adjustments for conditions such as Hypertension and Diabetes. |
| **`food_attributes.csv`** | **Dietary & Allergen Mapping** | Multi-attribute flags per food item (e.g., dairy, peanuts, tree nuts, gluten, egg, vegetarian/vegan tags, processing level). |
| **`rda_benchmarks_clean.csv`** | **ICMR / WHO RDA** | Recommended Dietary Allowances benchmark by age, gender, and activity level. |
| **`synthetic_user_profiles_clean.csv`** | **Simulation Dataset** | 1,000+ synthetic Nepali user profiles for testing, validation, and benchmarking. |

---

## Detailed Schema Definitions

### 1. `food_table_clean.csv`
- `food_id`: Unique identifier (e.g., `A01`, `B12`).
- `food_name`: English name of the ingredient / dish.
- `nepali_name`: Authentic Devanagari script name (e.g., चामल, दाल, गुन्द्रुक).
- `category`: Food category (Cereals, Pulses, Green Leafy, Vegetables, Meat, Fish, etc.).
- `calories`: Energy content (kcal / 100g).
- `protein_g`: Protein content (g / 100g).
- `carbs_g`: Carbohydrate content (g / 100g).
- `fat_g`: Fat content (g / 100g).
- `fiber_g`: Dietary fiber content (g / 100g).
- `omega3_g`: Omega-3 fatty acids content (g / 100g).
- `sodium_mg`: Sodium content (mg / 100g) — used for Hypertension filtering.
- `sugar_g`: Sugar content (g / 100g) — used for Diabetes filtering.
- `portion_grams`: Standard serving portion size in grams.
- `household_measure`: Everyday household unit (e.g., "1 kauri cup", "1 piece", "100g serving").
- `region_mountain`, `region_hills`, `region_terai`: Boolean availability flags per geographic region of Nepal.
- `available_year_round`, `season_*`: Seasonal availability flags.

### 2. `nepali_recipes.csv`
- `recipe_id`: Unique identifier for the Nepali recipe (e.g., `REC001`).
- `recipe_name`: Standard English name (e.g., "Mustang Thakali Dal Bhat Set").
- `nepali_name`: Authentic Nepali name (e.g., "मुस्ताङ थकाली दाल भात सेट").
- `meal_type`: Suitable meal slot (`Breakfast`, `Lunch`, `Dinner`).
- `diet_type`: Dietary category (`Vegan`, `Vegetarian`, `Eggetarian`, `Non-Vegetarian`).
- `cooking_time_mins`: Estimated preparation and cooking time in minutes.
- `ingredients_composition`: Comma-separated list of `food_id:grams` pairs (e.g., `A01:120,B02:80,C05:100`).
- `recipe_steps`: Clear, step-by-step culinary preparation instructions.

### 3. `medical_food_rules.csv`
- `condition`: Target medical condition (`Hypertension`, `Diabetes`, `Any`).
- `feature`: Nutritional attribute evaluated (`sodium_mg`, `sugar_g`, `fiber_g`).
- `operator`: Threshold comparison (`<`, `<=`, `>`, `>=`).
- `threshold`: Cutoff value.
- `unit`: Unit of measurement (`mg`, `g`, `g/1000kcal`).
- `action`: Impact on recommendation (`EXCLUDE`, `PENALISE`, `LIMIT`, `PREFER`).
- `source`: Clinical standard reference (e.g., WHO Guideline, ADA Standards of Care).
