from django.urls import path
from . import views

urlpatterns = [
    # Authentication
    path("auth/signup/", views.signup, name="auth-signup"),
    path("auth/login/", views.login, name="auth-login"),
    path("auth/logout/", views.logout, name="auth-logout"),
    path("auth/me/", views.me, name="auth-me"),

    # Health Assessment
    path("assessment/", views.create_assessment, name="assessment-create"),
    path("assessment/latest/", views.assessment_latest, name="assessment-latest"),
    path("assessment/history/", views.assessment_history, name="assessment-history"),
    path("assessment/<int:pk>/", views.assessment_delete, name="assessment-delete"),

    # Clinical Explainability
    path("food-pool/", views.personalized_food_pool, name="food-pool-explain"),

    # Meal Plan Generation & Regeneration
    path("meal-plan/generate/", views.generate_meal_plan, name="meal-plan-generate"),
    path("meal-plan/latest/", views.meal_plan_latest, name="meal-plan-latest"),
    path("meal-plan/regenerate-meal/", views.regenerate_meal, name="meal-plan-regenerate-meal"),
]
