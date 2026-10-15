"""
Management Command: python manage.py train_decision_tree
Trains the shallow Decision Tree Classifier for Hypertension & Diabetes medical suitability
and updates the joblib artifact in core/ml_artifacts/.
"""
import pandas as pd
from django.core.management.base import BaseCommand
from core.models import Food
from core.services import ml_service
from sklearn.tree import DecisionTreeClassifier
import joblib

SODIUM_THRESHOLD_MG = 400.0
SUGAR_THRESHOLD_G = 15.0


class Command(BaseCommand):
    help = "Trains and serializes the Medical Suitability Decision Tree"

    def handle(self, *args, **options):
        foods = Food.objects.all()
        if not foods.exists():
            self.stderr.write(
                self.style.ERROR("No foods found in the database. Please run 'python manage.py seed_data' first.")
            )
            return

        records = []
        for food in foods:
            for condition in ["Hypertension", "Diabetes"]:
                is_suitable = 1
                if condition == "Hypertension" and food.sodium_mg > SODIUM_THRESHOLD_MG:
                    is_suitable = 0
                if condition == "Diabetes" and food.sugar_g > SUGAR_THRESHOLD_G:
                    is_suitable = 0

                records.append({
                    "sodium_mg": food.sodium_mg,
                    "sugar_g": food.sugar_g,
                    "carbs_g": food.carbs_g,
                    "fat_g": food.fat_g,
                    "calories": food.calories,
                    "condition": condition,
                    "suitable": is_suitable,
                })

        df = pd.DataFrame(records)
        ohe = pd.get_dummies(df["condition"], prefix="condition")
        for col in ["condition_Diabetes", "condition_Hypertension"]:
            if col not in ohe.columns:
                ohe[col] = False

        train_df = pd.concat([df.drop(columns=["condition"]), ohe], axis=1)

        X = train_df[ml_service.FEATURE_COLS]
        y = train_df["suitable"]

        clf = DecisionTreeClassifier(max_depth=4, criterion="gini", random_state=42)
        clf.fit(X, y)

        accuracy = (clf.predict(X) == y).mean()

        ml_service.MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(clf, ml_service.MODEL_PATH)

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully trained Decision Tree on {len(foods)} foods ({len(train_df)} pairs). "
                f"Accuracy: {accuracy * 100:.2f}%. Saved to {ml_service.MODEL_PATH}"
            )
        )
