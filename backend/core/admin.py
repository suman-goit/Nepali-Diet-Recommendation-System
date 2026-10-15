from django.contrib import admin
from .models import Food, UserProfile, MealPlan, DayPlan, Meal, MealItem

@admin.register(Food)
class FoodAdmin(admin.ModelAdmin):
    list_display = ("food_id", "name", "nepali_name", "category", "diet_tag", "calories", "protein_g")
    search_fields = ("food_id", "name", "nepali_name", "category")
    list_filter = ("category", "diet_tag", "available_year_round")

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "gender", "age", "weight_kg", "goal", "target_calories", "created_at")
    search_fields = ("user__username", "goal", "medical_conditions")

@admin.register(MealPlan)
class MealPlanAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "created_at", "is_active")
    list_filter = ("is_active",)

@admin.register(DayPlan)
class DayPlanAdmin(admin.ModelAdmin):
    list_display = ("id", "meal_plan", "day_number")

@admin.register(Meal)
class MealAdmin(admin.ModelAdmin):
    list_display = ("id", "day_plan", "meal_type", "recipe_name", "cooking_time_mins")

@admin.register(MealItem)
class MealItemAdmin(admin.ModelAdmin):
    list_display = ("id", "meal", "food", "grams", "servings")
