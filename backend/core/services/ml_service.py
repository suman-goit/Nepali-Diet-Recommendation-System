"""
ML Service: Layer 2 Machine Learning Medical Suitability Filter.

Uses the trained Decision Tree Classifier (max_depth=4) to validate
whether food items are clinically suitable for patients with Hypertension and Diabetes.
"""
import os
import joblib
import pandas as pd
from pathlib import Path
from django.conf import settings

MODEL_PATH = Path(settings.BASE_DIR) / "core" / "ml_artifacts" / "decision_tree.joblib"

FEATURE_COLS = [
    "sodium_mg",
    "sugar_g",
    "carbs_g",
    "fat_g",
    "calories",
    "condition_Diabetes",
    "condition_Hypertension",
]

_model_cache = None


def get_model():
    """Loads and caches the serialized Decision Tree model."""
    global _model_cache
    if _model_cache is None:
        if MODEL_PATH.exists():
            _model_cache = joblib.load(MODEL_PATH)
        else:
            raise FileNotFoundError(
                f"Decision tree artifact not found at {MODEL_PATH}. "
                "Run: python manage.py train_decision_tree"
            )
    return _model_cache


def is_food_suitable(food, condition: str) -> bool:
    """
    Evaluates a single food item against a clinical condition using ML inference.
    Returns True if suitable, False otherwise.
    """
    if condition not in ("Hypertension", "Diabetes"):
        return True

    model = get_model()

    def _val(obj, key):
        if hasattr(obj, key):
            return getattr(obj, key)
        return obj.get(key, 0)

    features_dict = {
        "sodium_mg": float(_val(food, "sodium_mg") or 0),
        "sugar_g": float(_val(food, "sugar_g") or 0),
        "carbs_g": float(_val(food, "carbs_g") or 0),
        "fat_g": float(_val(food, "fat_g") or 0),
        "calories": float(_val(food, "calories") or 0),
        "condition_Diabetes": condition == "Diabetes",
        "condition_Hypertension": condition == "Hypertension",
    }

    X = pd.DataFrame([features_dict])[FEATURE_COLS]
    prediction = model.predict(X)[0]
    return bool(prediction == 1)


def filter_foods_by_ml(foods_list: list, medical_conditions: list[str]) -> list:
    """
    Filters a list of Food objects down to items suitable for all user medical conditions.
    """
    tracked_conditions = [c for c in medical_conditions if c in ("Hypertension", "Diabetes")]
    if not tracked_conditions:
        return list(foods_list)

    return [
        food for food in foods_list
        if all(is_food_suitable(food, cond) for cond in tracked_conditions)
    ]
