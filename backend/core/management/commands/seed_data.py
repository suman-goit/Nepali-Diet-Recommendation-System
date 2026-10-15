"""
Management Command: python manage.py seed_data
Populates the Food table with 225 authentic Nepali foods from data/food_table_clean.csv.
"""
import os
import pandas as pd
from django.conf import settings
from django.core.management.base import BaseCommand
from core.models import Food

DATA_PATH = os.path.join(settings.BASE_DIR, "data", "food_table_clean.csv")

VEGAN_CATEGORIES = {
    "Cereals", "Pulses", "Green Leafy", "Vegetables", "Roots & Tubers",
    "Fruits", "Condiments", "Nuts & Oilseeds", "Veg Products",
}
NON_VEG_CATEGORIES = {"Meat", "Fish"}
EGG_CATEGORIES = {"Eggs"}


def determine_diet_tag(category: str) -> str:
    """Categorizes food into dietary groups."""
    if category in NON_VEG_CATEGORIES:
        return "Non-Vegetarian"
    if category in EGG_CATEGORIES:
        return "Eggetarian"
    if category in VEGAN_CATEGORIES:
        return "Vegan"
    return "Vegetarian"


class Command(BaseCommand):
    help = "Seeds the database with Nepali foods from data/food_table_clean.csv"

    def handle(self, *args, **options):
        if not os.path.exists(DATA_PATH):
            self.stderr.write(self.style.ERROR(f"Dataset not found at {DATA_PATH}"))
            return

        df = pd.read_csv(DATA_PATH)
        created_count, updated_count = 0, 0

        for _, row in df.iterrows():
            defaults = {
                "name": row["food_name"],
                "nepali_name": row.get("nepali_name") or "",
                "category": row["category"],
                "diet_tag": determine_diet_tag(row["category"]),
                "calories": float(row.get("calories", 0) or 0),
                "protein_g": float(row.get("protein_g", 0) or 0),
                "carbs_g": float(row.get("carbs_g", 0) or 0),
                "fat_g": float(row.get("fat_g", 0) or 0),
                "fiber_g": float(row.get("fiber_g", 0) or 0),
                "omega3_g": float(row.get("omega3_g", 0) or 0),
                "sodium_mg": float(row.get("sodium_mg", 0) or 0),
                "sugar_g": float(row.get("sugar_g", 0) or 0),
                "portion_grams": float(row.get("portion_grams", 100) or 100),
                "household_measure": row.get("household_measure") or "100g serving",
                "price_tier": int(row.get("price_tier", 2) or 2),
                "available_year_round": bool(row.get("available_year_round", True)),
                "region_mountain": bool(row.get("region_mountain", True)),
                "region_hills": bool(row.get("region_hills", True)),
                "region_terai": bool(row.get("region_terai", True)),
                "nutrient_estimate_source": row.get("nutrient_estimate_source") or "",
            }

            _, was_created = Food.objects.update_or_create(
                food_id=row["food_id"], defaults=defaults
            )
            if was_created:
                created_count += 1
            else:
                updated_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully seeded {len(df)} foods ({created_count} created, {updated_count} updated)."
            )
        )
