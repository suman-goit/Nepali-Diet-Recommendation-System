# Machine Learning Training Module (Decision Tree Classifier)

This module handles the training, validation, explainability analysis, and export of the **Medical Suitability Decision Tree**.

---

## 1. Problem Formulation
Clinical dietary safety demands **100% explainability** and zero black-box obscurity. Patients with conditions such as **Hypertension** and **Diabetes** must not receive dangerous foods (e.g. foods excessively high in sodium or simple sugars).

To achieve dual validation alongside the deterministic Rule Evaluator, we train a shallow **Decision Tree Classifier (`max_depth=4`)**:
- **Inputs**: Nutritional features (`sodium_mg`, `sugar_g`, `carbs_g`, `fat_g`, `calories`) + One-hot encoded medical condition flags (`condition_Hypertension`, `condition_Diabetes`).
- **Output**: Binary classification (`1 = Suitable / Safe`, `0 = Unsuitable / Exclude`).

---

## 2. Clinical Guideline Thresholds
1. **Hypertension (WHO / AHA guideline)**:
   - Threshold proxy: $\text{Sodium} \le 400\text{ mg per 100g serving}$.
   - Foods exceeding $400\text{ mg sodium}$ are classified as `Unsuitable (0)` for hypertensive profiles.
2. **Diabetes (ADA Standards of Medical Care)**:
   - Threshold proxy: $\text{Free Sugars} \le 15\text{ g per 100g serving}$.
   - Foods exceeding $15\text{ g sugar}$ are classified as `Unsuitable (0)` for diabetic profiles.

---

## 3. Why Decision Trees?
- **White-Box Explainability**: The decision logic can be translated directly into human-readable `if-then-else` clinical rules.
- **Fast Inference**: Single tree evaluation runs in sub-millisecond time.
- **Deterministic & Auditable**: Critical for medical/nutritional recommendations during defense and peer review.

---

## 4. How to Run Training
```bash
# Run training script
python train_decision_tree.py
```

This will:
1. Load `../datasets/food_table_clean.csv`.
2. Generate condition-food evaluation matrix.
3. Train an explainable `DecisionTreeClassifier(max_depth=4, random_state=42)`.
4. Output Accuracy, Precision, Recall, Confusion Matrix, and Rule Tree.
5. Export `decision_tree.joblib` directly to both `ml_training/` and `../backend/core/ml_artifacts/`.
