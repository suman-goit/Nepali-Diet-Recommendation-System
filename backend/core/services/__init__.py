"""
Services Package: Modular business logic for the Nepali Diet Recommendation System.
1. nutrition_service: Calculates BMR, TDEE, and bodyweight-anchored macro targets (g/kg).
2. rule_evaluator: Deterministic safety filtering (Allergens, Diet, Region, Season, WHO/ADA scoring).
3. ml_service: Shallow Decision Tree for ML dual-validation of Hypertension and Diabetes suitability.
4. recipe_optimizer: Matches authentic Nepali recipes and solves portion scaling via PuLP Goal Programming.
"""
