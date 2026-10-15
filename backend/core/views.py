from django.contrib.auth import authenticate
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .models import DayPlan, Meal, MealItem, MealPlan, UserProfile
from .serializers import (
    DayPlanSerializer,
    MealPlanSerializer,
    SignupSerializer,
    UserProfileSerializer,
)
from .services import ml_service, nutrition_service, recipe_optimizer, rule_evaluator


# =====================================================================
# 1. Authentication Endpoints
# =====================================================================
@api_view(["POST"])
@permission_classes([AllowAny])
def signup(request):
    """Creates a new user account and returns an auth token."""
    serializer = SignupSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        token, _ = Token.objects.get_or_create(user=user)
        return Response({"token": token.key, "username": user.username}, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
@permission_classes([AllowAny])
def login(request):
    """Authenticates credentials and returns an auth token."""
    username = request.data.get("username")
    password = request.data.get("password")
    user = authenticate(username=username, password=password)
    if not user:
        return Response({"detail": "Invalid username or password"}, status=status.HTTP_401_UNAUTHORIZED)
    token, _ = Token.objects.get_or_create(user=user)
    return Response({"token": token.key, "username": user.username})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout(request):
    """Deletes the active authentication token."""
    request.user.auth_token.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def me(request):
    """Returns the authenticated user's details and latest health profile."""
    latest = request.user.profiles.first()
    data = {"username": request.user.username}
    if latest:
        data["latest_profile"] = UserProfileSerializer(latest).data
    return Response(data)


# =====================================================================
# 2. Health Assessment Endpoints
# =====================================================================
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_assessment(request):
    """
    Submits a health assessment questionnaire.
    Computes BMI, BMR, TDEE, and bodyweight-anchored macro targets.
    """
    serializer = UserProfileSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    profile = serializer.save(user=request.user)
    targets = nutrition_service.calculate_clinical_targets(profile)
    for key, value in targets.items():
        setattr(profile, key, value)
    profile.save()

    return Response(UserProfileSerializer(profile).data, status=status.HTTP_201_CREATED)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def assessment_latest(request):
    """Returns the user's most recent health assessment."""
    profile = request.user.profiles.first()
    if not profile:
        return Response({"detail": "No assessment found"}, status=status.HTTP_404_NOT_FOUND)
    return Response(UserProfileSerializer(profile).data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def assessment_history(request):
    """Returns the chronological history of all user assessments."""
    profiles = request.user.profiles.all()[:365]
    return Response(UserProfileSerializer(profiles, many=True).data)


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def assessment_delete(request, pk):
    """Deletes a historical assessment entry."""
    profile = get_object_or_404(UserProfile, pk=pk, user=request.user)
    profile.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


# =====================================================================
# 3. Clinical Explainability & Food Pool Endpoint
# =====================================================================
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def personalized_food_pool(request):
    """
    Returns the complete list of qualified foods, clinical ranking scores,
    and reasons for every excluded food item for defense explainability.
    """
    profile = request.user.profiles.first()
    if not profile:
        return Response({"detail": "Complete a health assessment first"}, status=status.HTTP_400_BAD_REQUEST)

    pool = rule_evaluator.evaluate_food_pool(profile)
    return Response({
        "count": len(pool.foods),
        "daily_limits": pool.daily_limits,
        "unsupported_conditions": pool.unsupported_conditions,
        "foods": [
            {
                "food_id": food.food_id,
                "name": food.name,
                "nepali_name": food.nepali_name,
                "category": food.category,
                "classification": pool.decisions[food.food_id].classification,
                "score": pool.decisions[food.food_id].score,
                "reasons": pool.decisions[food.food_id].reasons,
            }
            for food in pool.foods
        ],
        "excluded": pool.excluded,
    })


# =====================================================================
# 4. Meal Plan Generation & Regeneration Endpoints
# =====================================================================
def _get_qualified_foods_for_profile(profile):
    """Hybrid Filtering: Layer 1 Rule Evaluator + Layer 2 Decision Tree ML."""
    pool = rule_evaluator.evaluate_food_pool(profile)
    rule_safe_foods = pool.foods

    conditions = [c.strip() for c in (profile.medical_conditions or "").split(",") if c.strip()]
    final_foods = ml_service.filter_foods_by_ml(rule_safe_foods, conditions)
    return final_foods


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def generate_meal_plan(request):
    """
    Generates a 3-Day personalized meal plan using authentic Nepali recipes
    and PuLP Goal Programming portion scaling.
    """
    profile = request.user.profiles.first()
    if not profile:
        return Response({"detail": "Complete a health assessment first"}, status=status.HTTP_400_BAD_REQUEST)

    foods = _get_qualified_foods_for_profile(profile)
    if not foods:
        return Response({"detail": "No foods match your dietary constraints"}, status=status.HTTP_400_BAD_REQUEST)

    day_targets = {
        "target_calories": profile.target_calories,
        "target_protein_g": profile.target_protein_g,
        "target_carbs_g": profile.target_carbs_g,
        "target_fat_g": profile.target_fat_g,
    }

    # Archive existing plans and create new active plan
    request.user.meal_plans.update(is_active=False)
    meal_plan = MealPlan.objects.create(user=request.user, profile=profile, is_active=True)

    used_recipes = set()
    meal_order = ["Breakfast", "Lunch", "Dinner"]

    for day_number in range(1, 4):  # 3-Day Plan
        day_plan = DayPlan.objects.create(meal_plan=meal_plan, day_number=day_number)
        for meal_type in meal_order:
            solved = recipe_optimizer.solve_recipe_meal(
                foods_list=foods,
                day_targets=day_targets,
                meal_type=meal_type,
                profile=profile,
                exclude_recipe_ids=used_recipes,
            )
            used_recipes.add(solved["recipe_id"])

            meal = Meal.objects.create(
                day_plan=day_plan,
                meal_type=meal_type,
                recipe_id=solved.get("recipe_id", ""),
                recipe_name=solved.get("recipe_name", ""),
                nepali_name=solved.get("nepali_name", ""),
                recipe_steps=solved.get("recipe_steps", ""),
                cooking_time_mins=solved.get("cooking_time_mins", 20),
            )
            for item in solved.get("items", []):
                MealItem.objects.create(
                    meal=meal,
                    food=item["food"],
                    servings=item["servings"],
                    grams=item["grams"],
                )

    return Response(MealPlanSerializer(meal_plan).data, status=status.HTTP_201_CREATED)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def meal_plan_latest(request):
    """Returns the user's active 3-Day meal plan."""
    meal_plan = request.user.meal_plans.filter(is_active=True).first()
    if not meal_plan:
        return Response({"detail": "No active meal plan found"}, status=status.HTTP_404_NOT_FOUND)
    return Response(MealPlanSerializer(meal_plan).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def regenerate_meal(request):
    """Regenerates a single meal slot with an alternative recipe."""
    day_number = request.data.get("day_number")
    meal_type = request.data.get("meal_type")
    meal_plan = request.user.meal_plans.filter(is_active=True).first()
    if not meal_plan:
        return Response({"detail": "No active meal plan found"}, status=status.HTTP_404_NOT_FOUND)

    day_plan = get_object_or_404(DayPlan, meal_plan=meal_plan, day_number=day_number)
    meal = get_object_or_404(Meal, day_plan=day_plan, meal_type=meal_type)

    profile = meal_plan.profile
    foods = _get_qualified_foods_for_profile(profile)

    day_targets = {
        "target_calories": profile.target_calories,
        "target_protein_g": profile.target_protein_g,
        "target_carbs_g": profile.target_carbs_g,
        "target_fat_g": profile.target_fat_g,
    }

    exclude_recipe_ids = {meal.recipe_id} if meal.recipe_id else set()
    solved = recipe_optimizer.solve_recipe_meal(
        foods_list=foods,
        day_targets=day_targets,
        meal_type=meal_type,
        profile=profile,
        exclude_recipe_ids=exclude_recipe_ids,
    )

    meal.recipe_id = solved.get("recipe_id", "")
    meal.recipe_name = solved.get("recipe_name", "")
    meal.nepali_name = solved.get("nepali_name", "")
    meal.recipe_steps = solved.get("recipe_steps", "")
    meal.cooking_time_mins = solved.get("cooking_time_mins", 20)
    meal.save()

    meal.items.all().delete()
    for item in solved.get("items", []):
        MealItem.objects.create(
            meal=meal,
            food=item["food"],
            servings=item["servings"],
            grams=item["grams"],
        )

    return Response(DayPlanSerializer(day_plan).data)
