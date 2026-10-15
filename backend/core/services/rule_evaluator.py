"""
Rule Evaluator: Layer 1 deterministic safety filters & WHO/ADA medical scoring.

Pipeline Steps:
1. Hard Exclusions: Allergens, dietary type, geographic region, seasonal availability, religious/meat restrictions.
2. Medical Scoring: Ranks candidate foods using clinical rules (Hypertension: lower sodium; Diabetes: higher fiber, whole foods).
3. Daily Limits: Derives personalized daily nutrient caps from medical_food_rules.csv.
"""
from __future__ import annotations

import csv
from dataclasses import dataclass, field
from datetime import date
from functools import lru_cache
from pathlib import Path
from django.conf import settings

from ..models import Food

DATA_DIR = Path(settings.BASE_DIR) / "data"

# Allergen to food_attributes.csv mapping
ALLERGEN_FIELDS: dict[str, tuple[str, ...]] = {
    "Milk": ("contains_dairy",),
    "Nuts": ("contains_peanut", "contains_tree_nut"),
    "Fish": ("contains_fish",),
    "Gluten": ("contains_gluten",),
    "Egg": ("contains_egg",),
    "Buff": ("contains_buff",),
    "Pork": ("contains_pork",),
}

BUFF_FOOD_IDS: frozenset[str] = frozenset({"J01"})  # Buffalo Meat (Lean)
PORK_FOOD_IDS: frozenset[str] = frozenset({"J08"})  # Pork Muscle

DIETARY_TYPES: dict[str, set[str]] = {
    "Vegan": {"vegan"},
    "Vegetarian": {"vegan", "vegetarian"},
    "Eggetarian": {"vegan", "vegetarian", "eggetarian"},
    "Non-Vegetarian": {"vegan", "vegetarian", "eggetarian", "non_vegetarian"},
}

DM_PREFERRED_CATEGORIES = frozenset({
    "green leafy", "vegetables", "pulses", "fruits", "cereals", "nuts & oilseeds",
})
DM_PENALISED_PROCESSING = frozenset({"processed", "ultra_processed"})


@dataclass
class FoodDecision:
    food_id: str
    classification: str  # "Suitable" | "Limit"
    score: float
    reasons: list[str] = field(default_factory=list)


@dataclass
class FoodPool:
    foods: list[Food]
    decisions: dict[str, FoodDecision]
    excluded: dict[str, list[str]]
    daily_limits: dict[str, float]
    unsupported_conditions: list[str]


def _bool(value: str | bool | None) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes"}


def _csv_rows(filename: str) -> list[dict[str, str]]:
    path = DATA_DIR / filename
    with path.open(encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def _csv_list(value: str) -> list[str]:
    return [item.strip() for item in (value or "").split(",") if item.strip()]


@lru_cache(maxsize=1)
def _load_knowledge_base():
    """Loads and caches datasets from disk."""
    foods = {row["food_id"]: row for row in _csv_rows("food_table_clean.csv")}
    all_attrs = {row["food_id"]: row for row in _csv_rows("food_attributes.csv")}
    rules = _csv_rows("medical_food_rules.csv")

    attributes = {fid: all_attrs[fid] for fid in foods if fid in all_attrs}
    return foods, attributes, rules


def _season_for(day: date) -> str:
    if day.month in (3, 4, 5):
        return "spring"
    if day.month in (6, 7, 8):
        return "summer"
    if day.month in (9, 10, 11):
        return "autumn"
    return "winter"


def _daily_limits(conditions: list[str], calorie_target: float | None, rules: list[dict[str, str]]) -> dict[str, float]:
    limits: dict[str, float] = {}
    for rule in rules:
        if rule["condition"] not in conditions or rule.get("scope") != "daily":
            continue
        feature = rule["feature"]
        threshold = rule.get("threshold", "").strip()
        if not threshold:
            continue
        value = float(threshold)
        if rule.get("unit", "") == "g/1000kcal":
            if calorie_target is None:
                continue
            value = value * calorie_target / 1000.0
        op = rule.get("operator", "")
        if op in ("<", "<="):
            limits[f"max_{feature}"] = min(limits.get(f"max_{feature}", value), value)
        elif op in (">", ">="):
            limits[f"min_{feature}"] = max(limits.get(f"min_{feature}", value), value)
    return {k: round(v, 1) for k, v in limits.items()}


def evaluate_food_pool(profile, on_date: date | None = None) -> FoodPool:
    """
    Evaluates every food against user profile requirements.
    Applies deterministic exclusions and calculates evidence-based ranking scores.
    """
    source_foods, attributes, rules = _load_knowledge_base()

    conditions = _csv_list(profile.medical_conditions)
    allergies = _csv_list(profile.allergies)
    season = _season_for(on_date or date.today())
    region_field = {
        "Mountain": "region_mountain",
        "Hills": "region_hills",
        "Terai": "region_terai",
    }.get(profile.region)
    allowed_diet_types = DIETARY_TYPES.get(profile.food_preference, DIETARY_TYPES["Non-Vegetarian"])

    selected_ids: list[str] = []
    decisions: dict[str, FoodDecision] = {}
    excluded: dict[str, list[str]] = {}

    for food_id, source in source_foods.items():
        attrs = attributes.get(food_id, {})
        exclusions: list[str] = []

        # 1a. Dietary Preference
        raw_dt = attrs.get("dietary_type", "").strip().lower().replace("-", "_").replace(" ", "_")
        if raw_dt in ("veg_and_non_veg", "veg_and_non-veg"):
            raw_dt = "non_vegetarian"
        dt_normalised = raw_dt.rstrip("s")
        if dt_normalised and dt_normalised not in allowed_diet_types:
            exclusions.append(f"Not compatible with {profile.food_preference} diet")

        # 1b. Region Availability
        if region_field and not _bool(source.get(region_field, "false")):
            exclusions.append(f"Not commonly available in {profile.region}")

        # 1c. Seasonality
        if not _bool(source.get("available_year_round", "false")) and not _bool(source.get(f"season_{season}", "false")):
            exclusions.append(f"Out of season ({season})")

        # 1d. Allergies & Meat Restrictions
        for allergy in allergies:
            if allergy == "Buff":
                if food_id in BUFF_FOOD_IDS:
                    exclusions.append("Excluded: contains buffalo meat (Buff restriction)")
                continue
            if allergy == "Pork":
                if food_id in PORK_FOOD_IDS:
                    exclusions.append("Excluded: contains pork (Pork restriction)")
                continue

            for attr_field in ALLERGEN_FIELDS.get(allergy, ()):
                status = attrs.get(attr_field, "no").strip().lower()
                if status in {"yes", "unknown"}:
                    label = "contains" if status == "yes" else "has unverified"
                    exclusions.append(f"{label} {allergy.lower()} allergen")
                    break

        # 1e. Celiac / Lactose Intolerance
        if "Celiac" in conditions:
            if attrs.get("contains_gluten", "no").strip().lower() in {"yes", "unknown"}:
                exclusions.append("Contains or has unverified gluten (Celiac restriction)")
        if "Lactose Intolerance" in conditions:
            if attrs.get("contains_dairy", "no").strip().lower() in {"yes", "unknown"}:
                exclusions.append("Contains or has unverified dairy (Lactose Intolerance restriction)")

        if exclusions:
            excluded[food_id] = exclusions
            continue

        # 2. Medical Scoring for Eligible Foods
        score = 0.0
        classification = "Suitable"
        reasons: list[str] = []
        processing = attrs.get("processing_level", "").strip().lower()
        category = source.get("category", "").strip().lower()

        if "Hypertension" in conditions:
            sodium = float(source.get("sodium_mg", 0) or 0)
            score -= sodium / 100.0
            reasons.append("Hypertension: lower-sodium foods ranked higher (WHO guideline)")

        if "Diabetes" in conditions:
            fiber = float(source.get("fiber_g", 0) or 0)
            score += fiber * 2.0
            if processing in DM_PENALISED_PROCESSING:
                score -= 5.0
                classification = "Limit"
                reasons.append("Diabetes: processed food limited (ADA guideline)")
            if category in DM_PREFERRED_CATEGORIES:
                score += 2.0
                reasons.append("Diabetes: fiber-rich whole food group preferred (ADA guideline)")

        if not reasons:
            reasons.append("Meets all diet, allergen, region, and season safety filters")

        selected_ids.append(food_id)
        decisions[food_id] = FoodDecision(food_id, classification, round(score, 2), reasons)

    # 3. Retrieve DB Objects and Sort by Rank Score
    db_foods = Food.objects.in_bulk(selected_ids, field_name="food_id")
    eligible = sorted(
        (db_foods[fid] for fid in selected_ids if fid in db_foods),
        key=lambda f: decisions[f.food_id].score,
        reverse=True,
    )

    rule_conditions = {r["condition"] for r in rules if r.get("condition") != "Any"}
    ignored = {"Celiac", "Lactose Intolerance"}
    unsupported = sorted(set(conditions) - rule_conditions - ignored)

    return FoodPool(
        foods=eligible,
        decisions=decisions,
        excluded=excluded,
        daily_limits=_daily_limits(conditions, profile.target_calories, rules),
        unsupported_conditions=unsupported,
    )
