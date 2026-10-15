"""
Machine Learning Training Module: Decision Tree for Medical Suitability
======================================================================
This standalone script trains an explainable, shallow Decision Tree Classifier
to determine the medical suitability of authentic Nepali food items for patients
with Hypertension and Diabetes.

Clinical Guideline Thresholds:
- WHO Guideline (Hypertension): Sodium <= 400 mg per 100g serving
- ADA Guideline (Diabetes): Free Sugars <= 15 g per 100g serving

Features Used:
1. sodium_mg (float)
2. sugar_g (float)
3. carbs_g (float)
4. fat_g (float)
5. calories (float)
6. condition_Diabetes (one-hot binary: 0 or 1)
7. condition_Hypertension (one-hot binary: 0 or 1)

Output Target:
- suitable (binary: 1 = Suitable / Safe, 0 = Limit / Exclude)
"""

import os
import joblib
import pandas as pd
from pathlib import Path
from sklearn.tree import DecisionTreeClassifier, export_text
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix

# Clinical thresholds
SODIUM_THRESHOLD_MG = 400.0  # WHO recommendation proxy
SUGAR_THRESHOLD_G = 15.0     # ADA recommendation proxy

# Base paths
CURRENT_DIR = Path(__file__).resolve().parent
DATASET_PATH = CURRENT_DIR.parent / "datasets" / "food_table_clean.csv"
MODEL_OUTPUT_DIR = CURRENT_DIR
BACKEND_MODEL_DIR = CURRENT_DIR.parent / "backend" / "core" / "ml_artifacts"

FEATURE_COLS = [
    "sodium_mg",
    "sugar_g",
    "carbs_g",
    "fat_g",
    "calories",
    "condition_Diabetes",
    "condition_Hypertension",
]


def load_and_preprocess_dataset(csv_path: Path) -> pd.DataFrame:
    """Loads clean Nepali food dataset and creates medical evaluation pairs."""
    if not csv_path.exists():
        raise FileNotFoundError(f"Dataset not found at: {csv_path}")

    foods_df = pd.read_csv(csv_path)
    records = []

    # Cross-product of every food with tracked clinical conditions
    for _, food in foods_df.iterrows():
        for condition in ["Hypertension", "Diabetes"]:
            is_suitable = 1
            if condition == "Hypertension" and float(food.get("sodium_mg", 0) or 0) > SODIUM_THRESHOLD_MG:
                is_suitable = 0
            if condition == "Diabetes" and float(food.get("sugar_g", 0) or 0) > SUGAR_THRESHOLD_G:
                is_suitable = 0

            records.append({
                "food_id": food["food_id"],
                "food_name": food["food_name"],
                "sodium_mg": float(food.get("sodium_mg", 0) or 0),
                "sugar_g": float(food.get("sugar_g", 0) or 0),
                "carbs_g": float(food.get("carbs_g", 0) or 0),
                "fat_g": float(food.get("fat_g", 0) or 0),
                "calories": float(food.get("calories", 0) or 0),
                "condition": condition,
                "suitable": is_suitable,
            })

    dataset = pd.DataFrame(records)

    # One-hot encode the condition column
    ohe = pd.get_dummies(dataset["condition"], prefix="condition")
    for col in ["condition_Diabetes", "condition_Hypertension"]:
        if col not in ohe.columns:
            ohe[col] = False

    final_df = pd.concat([dataset, ohe], axis=1)
    return final_df


def train_and_evaluate():
    print("=" * 70)
    print("  Nepali Diet Planner: ML Medical Suitability Model Training")
    print("=" * 70)

    # 1. Load data
    df = load_and_preprocess_dataset(DATASET_PATH)
    print(f"[✓] Loaded {len(df)} sample rows from {DATASET_PATH.name}")
    print(f"    - Hypertension samples: {sum(df['condition'] == 'Hypertension')}")
    print(f"    - Diabetes samples:     {sum(df['condition'] == 'Diabetes')}")
    print(f"    - Suitable (Class 1):   {sum(df['suitable'] == 1)}")
    print(f"    - Unsuitable (Class 0): {sum(df['suitable'] == 0)}\n")

    # 2. Features and Target
    X = df[FEATURE_COLS]
    y = df["suitable"]

    # 3. Train-Test Split (80% Train, 20% Test)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )

    # 4. Train Decision Tree (max_depth=4 for high explainability)
    clf = DecisionTreeClassifier(
        max_depth=4,
        criterion="gini",
        random_state=42
    )
    clf.fit(X_train, y_train)

    # 5. Evaluate
    y_pred_train = clf.predict(X_train)
    y_pred_test = clf.predict(X_test)

    train_acc = accuracy_score(y_train, y_pred_train)
    test_acc = accuracy_score(y_test, y_pred_test)

    print(f"[*] Training Accuracy:   {train_acc * 100:.2f}%")
    print(f"[*] Test Accuracy:       {test_acc * 100:.2f}%\n")

    print("[*] Classification Report on Test Set:")
    print(classification_report(y_test, y_pred_test, target_names=["Unsuitable (0)", "Suitable (1)"]))

    print("[*] Confusion Matrix:")
    print(confusion_matrix(y_test, y_pred_test))
    print("\n" + "-" * 70)

    # 6. Print Decision Rules
    print("[*] Decision Tree Logic & Branching Rules:")
    tree_rules = export_text(clf, feature_names=FEATURE_COLS)
    print(tree_rules)
    print("-" * 70)

    # 7. Feature Importances
    print("[*] Feature Importances:")
    for name, imp in zip(FEATURE_COLS, clf.feature_importances_):
        print(f"    - {name:<25}: {imp:.4f}")
    print("-" * 70)

    # 8. Save Artifacts
    # Retrain on full dataset for production deployment
    clf_full = DecisionTreeClassifier(max_depth=4, criterion="gini", random_state=42)
    clf_full.fit(X, y)

    MODEL_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    BACKEND_MODEL_DIR.mkdir(parents=True, exist_ok=True)

    saved_path_1 = MODEL_OUTPUT_DIR / "decision_tree.joblib"
    saved_path_2 = BACKEND_MODEL_DIR / "decision_tree.joblib"

    joblib.dump(clf_full, saved_path_1)
    joblib.dump(clf_full, saved_path_2)

    print(f"[✓] Model artifact saved to: {saved_path_1}")
    print(f"[✓] Model artifact deployed to backend: {saved_path_2}")
    print("=" * 70)


if __name__ == "__main__":
    train_and_evaluate()
