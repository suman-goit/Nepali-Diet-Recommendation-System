"""
Recipe Optimizer Service: Layer 3 Authentic Nepali Recipe Matching & Portion Scaling.

Pipeline:
1. Loads 125+ authentic Nepali recipes from nepali_recipes.csv.
2. Filters dishes where ALL ingredients belong to the user's qualified food pool (passed Rule Evaluator & ML Tree).
3. Scales ingredient quantities via Goal Programming (PuLP) to hit exact caloric & macronutrient meal splits:
   - Breakfast: 25% of daily target
   - Lunch: 40% of daily target
   - Dinner: 35% of daily target
4. Returns complete culinary metadata (Nepali Devanagari script, steps, cooking time) + exact portion gram weights.
"""
from __future__ import annotations

import csv
import random
from functools import lru_cache
from pathlib import Path
import pulp
from django.conf import settings

from ..models import Food

DATA_DIR = Path(settings.BASE_DIR) / "data"

MEAL_SPLIT = {"Breakfast": 0.25, "Lunch": 0.40, "Dinner": 0.35}
DEVIATION_WEIGHTS = {"calories": 1.0, "protein_g": 2.0, "carbs_g": 0.5, "fat_g": 0.5}

DIET_HIERARCHY = {
    "Vegan": {"Vegan"},
    "Vegetarian": {"Vegan", "Vegetarian"},
    "Eggetarian": {"Vegan", "Vegetarian", "Eggetarian"},
    "Non-Vegetarian": {"Vegan", "Vegetarian", "Eggetarian", "Non-Vegetarian"},
}


@lru_cache(maxsize=1)
def load_all_recipes() -> list[dict]:
    """Loads and caches authentic Nepali recipes from CSV."""
    path = DATA_DIR / "nepali_recipes.csv"
    if not path.exists():
        return []
    with path.open(encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def parse_composition(comp_str: str) -> list[tuple[str, float]]:
    """Parses 'A01:120,B02:80' into [('A01', 120.0), ('B02', 80.0)]."""
    results = []
    for part in (comp_str or "").split(","):
        if ":" in part:
            fid, grams = part.strip().split(":", 1)
            try:
                results.append((fid.strip(), float(grams.strip())))
            except ValueError:
                continue
    return results


def get_eligible_recipes(allowed_food_ids: set[str], meal_type: str, diet_type: str) -> list[dict]:
    """Filters recipes where every ingredient is in the safe food pool."""
    all_recipes = load_all_recipes()
    allowed_diets = DIET_HIERARCHY.get(diet_type, DIET_HIERARCHY["Non-Vegetarian"])

    eligible = []
    for rec in all_recipes:
        if rec["meal_type"] != meal_type:
            continue
        if rec["diet_type"] not in allowed_diets:
            continue

        comp = parse_composition(rec.get("ingredients_composition", ""))
        if not comp:
            continue

        if all(fid in allowed_food_ids for fid, _ in comp):
            eligible.append(rec)

    return eligible


def solve_recipe_meal(
    foods_list: list[Food],
    day_targets: dict,
    meal_type: str,
    profile,
    exclude_recipe_ids: set[str] | None = None,
) -> dict:
    """
    Selects the best matching authentic Nepali dish and solves portion scaling via PuLP.
    """
    exclude_recipe_ids = exclude_recipe_ids or set()
    food_map = {f.food_id: f for f in foods_list}
    allowed_fids = set(food_map.keys())

    eligible_recipes = get_eligible_recipes(
        allowed_food_ids=allowed_fids,
        meal_type=meal_type,
        diet_type=profile.food_preference,
    )

    candidates = [r for r in eligible_recipes if r["recipe_id"] not in exclude_recipe_ids]
    if not candidates:
        candidates = eligible_recipes

    split = MEAL_SPLIT.get(meal_type, 0.33)
    target_cal = day_targets["target_calories"] * split
    target_pro = day_targets["target_protein_g"] * split
    target_carb = day_targets["target_carbs_g"] * split
    target_fat = day_targets["target_fat_g"] * split

    if not candidates:
        return _fallback_meal_solve(foods_list, day_targets, meal_type)

    # Sort by proximity to target calories and pick from top candidates for culinary variety
    candidates.sort(key=lambda r: abs(float(r.get("calories_per_serving", 0) or 0) - target_cal))
    top_k = min(8, len(candidates))
    chosen_recipe = random.choice(candidates[:top_k])

    comp = parse_composition(chosen_recipe["ingredients_composition"])
    recipe_foods = [(food_map[fid], base_grams) for fid, base_grams in comp if fid in food_map]

    if not recipe_foods:
        return _fallback_meal_solve(foods_list, day_targets, meal_type)

    # PuLP Optimization: Solve for scale factor (portion multiplier 0.5x to 2.5x)
    prob = pulp.LpProblem(f"scale_{chosen_recipe['recipe_id']}", pulp.LpMinimize)
    scale = pulp.LpVariable("scale_factor", lowBound=0.5, upBound=2.5)

    def total_nutrient(attr):
        return pulp.lpSum(
            scale * (base_grams / 100.0) * getattr(f, attr)
            for f, base_grams in recipe_foods
        )

    targets = {
        "calories": target_cal,
        "protein_g": target_pro,
        "carbs_g": target_carb,
        "fat_g": target_fat,
    }

    over = {}
    under = {}
    for attr in DEVIATION_WEIGHTS:
        over[attr] = pulp.LpVariable(f"over_{attr}", lowBound=0)
        under[attr] = pulp.LpVariable(f"under_{attr}", lowBound=0)
        prob += total_nutrient(attr) - targets[attr] == over[attr] - under[attr]

    prob += pulp.lpSum(
        DEVIATION_WEIGHTS[attr] * (over[attr] + under[attr]) for attr in DEVIATION_WEIGHTS
    )

    try:
        prob.solve(pulp.PULP_CBC_CMD(msg=0))
        scale_val = pulp.value(scale)
        if scale_val is None or scale_val < 0.3:
            scale_val = 1.0
    except Exception:
        scale_val = 1.0

    items = []
    for f, base_grams in recipe_foods:
        actual_grams = round(base_grams * scale_val, 1)
        servings = round(actual_grams / (f.portion_grams or 100.0), 2)
        items.append({"food": f, "servings": servings, "grams": actual_grams})

    return {
        "recipe_id": chosen_recipe["recipe_id"],
        "recipe_name": chosen_recipe["recipe_name"],
        "nepali_name": chosen_recipe["nepali_name"],
        "recipe_steps": chosen_recipe["recipe_steps"],
        "cooking_time_mins": int(chosen_recipe.get("cooking_time_mins", 20) or 20),
        "items": items,
    }


def _fallback_meal_solve(foods_list: list[Food], day_targets: dict, meal_type: str) -> dict:
    """Fallback solver when no pre-authored recipe matches strict multi-condition constraints."""
    split = MEAL_SPLIT.get(meal_type, 0.33)
    target_cal = day_targets["target_calories"] * split
    target_pro = day_targets["target_protein_g"] * split
    target_carb = day_targets["target_carbs_g"] * split
    target_fat = day_targets["target_fat_g"] * split

    candidates = [f for f in foods_list if meal_type in (f.suitable_meals or "Breakfast,Lunch,Dinner")]
    if not candidates:
        candidates = foods_list[:5]

    sample_foods = candidates[:min(4, len(candidates))]
    items = []
    for f in sample_foods:
        portion = float(f.portion_grams or 100.0)
        items.append({"food": f, "servings": 1.0, "grams": portion})

    return {
        "recipe_id": "CUSTOM",
        "recipe_name": f"Balanced Nepali {meal_type} Set",
        "nepali_name": f"सन्तुलित नेपाली {meal_type} थाली",
        "recipe_steps": "Prepare wholesome grains, lentils, and seasonal vegetables with minimal oil, seasoned with cumin, garlic, and turmeric.",
        "cooking_time_mins": 25,
        "items": items,
    }


def calculate_meal_totals(items: list) -> dict:
    """Sums nutrient totals across meal items for display."""
    totals = {
        "calories": 0.0,
        "protein_g": 0.0,
        "carbs_g": 0.0,
        "fat_g": 0.0,
        "fiber_g": 0.0,
        "omega3_g": 0.0,
    }
    for item in items:
        food = item["food"]
        grams = item["grams"]
        factor = grams / 100.0
        totals["calories"] += food.calories * factor
        totals["protein_g"] += food.protein_g * factor
        totals["carbs_g"] += food.carbs_g * factor
        totals["fat_g"] += food.fat_g * factor
        totals["fiber_g"] += food.fiber_g * factor
        totals["omega3_g"] += food.omega3_g * factor

    return {k: round(v, 1) for k, v in totals.items()}
