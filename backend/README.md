# Nepali Diet Recommendation System — Backend (Django + DRF)

This is the simplified, modular Django REST Framework backend for the Nepali Diet Recommendation System.

---

## 1. Modular Services Architecture

The business logic is neatly organized into clear, explainable services under `core/services/`:

```
core/
├── models.py                   # ORM Models (Food, UserProfile, MealPlan, DayPlan, Meal, MealItem)
├── serializers.py              # DRF Serializers
├── views.py                    # REST API View controllers
├── urls.py                     # API Routes
└── services/                   # Modular Core Business Logic
    ├── nutrition_service.py    # BMR (Mifflin-St Jeor), TDEE, & bodyweight-anchored macro scaling (g/kg)
    ├── rule_evaluator.py       # Layer 1: Safety exclusions & WHO/ADA medical rank scoring
    ├── ml_service.py           # Layer 2: Decision Tree ML validator (Hypertension & Diabetes)
    └── recipe_optimizer.py     # Layer 3: Authentic Nepali recipe matching & PuLP portion scaling
```

---

## 2. API Endpoints Reference

| Category | Endpoint | Method | Description |
| :--- | :--- | :--- | :--- |
| **Auth** | `/api/auth/signup/` | `POST` | Register a new user account |
| **Auth** | `/api/auth/login/` | `POST` | Authenticate user credentials & obtain token |
| **Auth** | `/api/auth/logout/` | `POST` | Invalidate active token |
| **Auth** | `/api/auth/me/` | `GET` | Get current user info & latest health profile |
| **Assessment** | `/api/assessment/` | `POST` | Submit health assessment questionnaire & calculate targets |
| **Assessment** | `/api/assessment/latest/` | `GET` | Retrieve latest assessment and nutritional targets |
| **Assessment** | `/api/assessment/history/` | `GET` | Retrieve chronological assessment history |
| **Assessment** | `/api/assessment/<id>/` | `DELETE` | Delete a specific historical assessment record |
| **Explainability** | `/api/food-pool/` | `GET` | Clinical explainability: qualified foods, daily limits & exclusion reasons |
| **Meal Plan** | `/api/meal-plan/generate/` | `POST` | Generate new 3-day personalized Nepali meal plan |
| **Meal Plan** | `/api/meal-plan/latest/` | `GET` | Retrieve currently active 3-day meal plan |
| **Meal Plan** | `/api/meal-plan/regenerate-meal/` | `POST` | Regenerate a single meal slot with an alternative dish |

---

## 3. Setup and Execution

```bash
# 1. Enter backend directory
cd backend

# 2. Run migrations
python manage.py migrate

# 3. Seed Nepali food composition table (DFTQC 2012)
python manage.py seed_data

# 4. Train and cache the medical decision tree
python manage.py train_decision_tree

# 5. Start the backend server
python manage.py runserver 8000
```
Backend API will be accessible at `http://localhost:8000/api/`.
