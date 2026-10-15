"""
Nutrition Service: Calculates evidence-based energy and macronutrient targets.

Formulas & Standards:
- BMR: Mifflin-St Jeor Equation (clinical standard)
- TDEE: Physical Activity Level (PAL) multipliers
- Protein: Anchored to body weight (g/kg/day) to prevent overestimation on high-calorie plans (ISSN/ACSM guideline)
- Fat: 25-30% of total daily energy
- Carbs: Remainder of daily calories
- Dietary Fiber: 14g / 1000 kcal
- Omega-3: 1.6g / day
"""

ACTIVITY_MULTIPLIERS = {
    "Sedentary": 1.2,
    "Lightly Active": 1.375,
    "Moderate": 1.55,
    "Very Active": 1.725,
    "Extra Active": 1.9,
}

GOAL_CALORIE_ADJUSTMENT = {
    "Weight Loss": -500,
    "Maintenance": 0,
    "Healthy Living": 0,
    "Muscle Gain": 300,
}

PROTEIN_G_PER_KG = {
    "Weight Loss": 1.1,       # Preserves lean mass in caloric deficit (ICMR 2020)
    "Maintenance": 0.85,      # ICMR-NIN 2020 Recommended Dietary Allowance (0.83 g/kg)
    "Healthy Living": 0.85,
    "Muscle Gain": 1.3,       # Realistic muscle synthesis target for Nepali diets
}

PROTEIN_G_MIN = 35.0
PROTEIN_G_MAX = 180.0

FAT_RATIOS = {
    "Weight Loss": 0.30,
    "Maintenance": 0.25,
    "Healthy Living": 0.25,
    "Muscle Gain": 0.25,
}

FIBER_G_PER_1000KCAL = 14.0
OMEGA3_G_PER_DAY = 1.6


def calculate_bmi(weight_kg: float, height_cm: float) -> float:
    """Computes Body Mass Index (BMI = kg / m^2)."""
    height_m = height_cm / 100.0
    if height_m <= 0:
        return 0.0
    return round(weight_kg / (height_m ** 2), 1)


def calculate_bmr(weight_kg: float, height_cm: float, age: int, gender: str) -> float:
    """Computes Basal Metabolic Rate using the Mifflin-St Jeor equation."""
    base = 10.0 * weight_kg + 6.25 * height_cm - 5.0 * age
    if gender.strip().lower() == "male":
        return round(base + 5.0, 1)
    return round(base - 161.0, 1)


def calculate_tdee(bmr: float, activity_level: str) -> float:
    """Computes Total Daily Energy Expenditure."""
    multiplier = ACTIVITY_MULTIPLIERS.get(activity_level, 1.2)
    return round(bmr * multiplier, 1)


def calculate_clinical_targets(profile) -> dict:
    """
    Computes all clinical nutritional targets for a UserProfile instance.
    Returns a dictionary of targets ready to be persisted.
    """
    bmi = calculate_bmi(profile.weight_kg, profile.height_cm)
    bmr = calculate_bmr(profile.weight_kg, profile.height_cm, profile.age, profile.gender)
    tdee = calculate_tdee(bmr, profile.activity_level)

    # Caloric target with safe floor
    target_calories = tdee + GOAL_CALORIE_ADJUSTMENT.get(profile.goal, 0)
    target_calories = max(target_calories, 1200.0)

    # 1. Protein target anchored to body weight
    g_per_kg = PROTEIN_G_PER_KG.get(profile.goal, PROTEIN_G_PER_KG["Maintenance"])
    target_protein_g = profile.weight_kg * g_per_kg
    target_protein_g = min(max(target_protein_g, PROTEIN_G_MIN), PROTEIN_G_MAX)

    # 2. Fat target as % of daily calories
    fat_ratio = FAT_RATIOS.get(profile.goal, FAT_RATIOS["Maintenance"])
    target_fat_g = (target_calories * fat_ratio) / 9.0

    # 3. Carbohydrates fill remaining calories
    protein_kcal = target_protein_g * 4.0
    fat_kcal = target_fat_g * 9.0
    remaining_kcal = max(target_calories - protein_kcal - fat_kcal, 0.0)
    target_carbs_g = remaining_kcal / 4.0

    # 4. Fiber and Omega-3
    target_fiber_g = (target_calories / 1000.0) * FIBER_G_PER_1000KCAL
    target_omega3_g = OMEGA3_G_PER_DAY

    return {
        "bmi": bmi,
        "bmr": bmr,
        "tdee": tdee,
        "target_calories": round(target_calories, 1),
        "target_protein_g": round(target_protein_g, 1),
        "target_carbs_g": round(target_carbs_g, 1),
        "target_fat_g": round(target_fat_g, 1),
        "target_fiber_g": round(target_fiber_g, 1),
        "target_omega3_g": round(target_omega3_g, 1),
    }
