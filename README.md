# Nepali Diet Recommendation System (Minor Project III/II)
### Clinical Nutrition & Personalized Dietary Optimization Platform (DFTQC 2012)

A modular, explainable clinical dietary recommendation system tailored specifically for Nepali dietary habits, regional food availability (Mountain, Hills, Terai), seasonality, and chronic health conditions (Hypertension, Diabetes, Anaemia, Celiac, Lactose Intolerance).

---

## 1. Project Directory Structure

The project is organized into clean, standalone modules:

```
Minor-Project-III-II/
├── datasets/                     # Clean datasets & clinical rules
│   ├── food_table_clean.csv      # 225 Nepali foods with 6 nutritional vitals + sodium/sugar (DFTQC 2012)
│   ├── nepali_recipes.csv        # 125+ authentic Nepali recipes (Dal Bhat, Dhindo, Momos, Kwati, etc.)
│   ├── medical_food_rules.csv    # WHO & ADA evidence-based nutrient thresholds
│   ├── food_attributes.csv       # Allergen & dietary metadata (dairy, nuts, gluten, veg/vegan)
│   ├── rda_benchmarks_clean.csv  # ICMR / WHO RDA benchmark table
│   ├── synthetic_user_profiles_clean.csv # User simulation profiles
│   └── README.md                 # Dataset dictionary and schema documentation
│
├── ml_training/                  # Dedicated Machine Learning module
│   ├── train_decision_tree.py    # Standalone script to train & validate the Decision Tree
│   ├── evaluate_model.ipynb      # Interactive Jupyter notebook for ML evaluation & visualization
│   ├── decision_tree.joblib      # Serialized trained model artifact
│   └── README.md                 # ML methodology and decision rule explanation
│
├── backend/                      # Django REST Framework Backend API
│   ├── config/                   # Django settings, URLs, WSGI, ASGI
│   ├── core/
│   │   ├── models.py             # ORM models (Food, UserProfile, MealPlan, DayPlan, Meal, MealItem)
│   │   ├── serializers.py        # DRF serializers
│   │   ├── views.py              # REST API controllers
│   │   ├── urls.py               # Route endpoints
│   │   ├── admin.py              # Django administration portal
│   │   ├── services/             # Core Business Logic Layer
│   │   │   ├── nutrition_service.py   # BMR (Mifflin-St Jeor), TDEE, & bodyweight-anchored macro scaling
│   │   │   ├── rule_evaluator.py      # Layer 1: Deterministic safety exclusions & clinical rank scoring
│   │   │   ├── ml_service.py          # Layer 2: Decision Tree ML validator (Hypertension & Diabetes)
│   │   │   └── recipe_optimizer.py    # Layer 3: Authentic recipe matching & PuLP LP portion scaling
│   │   ├── management/commands/  # `seed_data.py`, `train_decision_tree.py`
│   │   └── ml_artifacts/         # Production model artifact (decision_tree.joblib)
│   ├── data/                     # Local data CSV copies for runtime loading
│   ├── manage.py
│   ├── requirements.txt
│   └── README.md
│
├── frontend/                     # React + Vite Client Application
│   ├── src/
│   │   ├── components/           # Navbar, MealCard, DeltaFeed
│   │   ├── pages/                # Home, Assessment, MealPlan, Grocery, History, Profile, Login, Signup
│   │   ├── context/              # AuthContext (token storage & session management)
│   │   ├── api.js                # REST API client
│   │   ├── styles.css            # Clean UI styles
│   │   ├── App.jsx               # Client routing
│   │   └── main.jsx
│   ├── package.json
│   ├── vite.config.js
│   └── README.md
│
├── run_project.sh                # One-click startup script (Linux / macOS)
├── run_project.bat               # One-click startup script (Windows)
├── .gitignore                    # Git ignore file
└── README.md                     # Main project documentation
```

---

## 2. Recommendation Pipeline

The recommendation engine runs a 3-layer hybrid decision pipeline:

```
                       User Health Assessment
             (Age, Gender, Weight, Height, Activity, Goal,
            Food Preference, Region, Medical Conditions, Allergies)
                                │
                                ▼
         ┌──────────────────────────────────────────────┐
         │             Nutrition Service                │
         │  • BMI = Weight / (Height)^2                 │
         │  • BMR = Mifflin-St Jeor Formula             │
         │  • TDEE = BMR × Activity Multiplier          │
         │  • Protein Target = Weight (kg) × g/kg Ratio │ (Avoids overestimation)
         │  • Target Calories = TDEE ± Goal Offset      │
         └──────────────────────┬───────────────────────┘
                                │
                                ▼
         ┌──────────────────────────────────────────────┐
         │    Layer 1: Rule Evaluator (Deterministic)   │
         │  • Allergen Exclusions (Milk, Nuts, Gluten)  │
         │  • Dietary Restrictions (Vegan, Veg, Non-Veg)│
         │  • Region Availability (Mountain, Hills, Terai)
         │  • Seasonal Availability (Spring/Summer/etc.)│
         │  • Evidence-based WHO/ADA medical rank score │
         └──────────────────────┬───────────────────────┘
                                │ Qualified Food Candidates
                                ▼
         ┌──────────────────────────────────────────────┐
         │     Layer 2: Decision Tree ML Filter         │
         │  • Dual-validation for Hypertension/Diabetes │
         │  • Checks sodium <= 400mg & sugar <= 15g     │
         │  • White-box interpretable decision branches │
         └──────────────────────┬───────────────────────┘
                                │ Safe Food Pool
                                ▼
         ┌──────────────────────────────────────────────┐
         │   Layer 3: Recipe Optimizer (PuLP LP Solver) │
         │  • Matches 125+ authentic Nepali dishes      │
         │  • Splits calories 25% Breakfast, 40% Lunch, │
         │    35% Dinner                                │
         │  • Goal Programming scales ingredient grams  │
         │    to minimize deviation from exact targets  │
         └──────────────────────┬───────────────────────┘
                                │
                                ▼
         ┌──────────────────────────────────────────────┐
         │           Final 3-Day Meal Plan              │
         │  • Authentic Nepali dishes (Devanagari text) │
         │  • Exact ingredient gram weights             │
         │  • Step-by-step cooking preparation steps    │
         │  • Consolidated 3-Day Grocery Checklist      │
         └──────────────────────────────────────────────┘
```

---

## 3. Prerequisites

Before running the project, make sure you have the following installed on your machine:
- **Python 3.10+** (Python 3.10, 3.11, or 3.12 recommended)
- **Node.js 18+** and **npm**
- **Git**

---

## 4. Setup and Run Guide (Platform Specific)

### Option A: Linux (Ubuntu / Debian / Fedora / Arch)

#### Terminal 1 — Backend (Django + DRF)
```bash
# 1. Navigate to the backend directory
cd backend

# 2. Create a virtual environment
python3 -m venv .venv

# 3. Activate the virtual environment
source .venv/bin/activate

# 4. Upgrade pip and install backend dependencies
pip install --upgrade pip
pip install -r requirements.txt

# 5. Apply database migrations
python manage.py migrate

# 6. Seed the Nepali food database (DFTQC 2012)
python manage.py seed_data

# 7. Train and serialize the medical decision tree
python manage.py train_decision_tree

# 8. Start the Django development server
python manage.py runserver 8000
```
Backend API will be running at `http://127.0.0.1:8000/`.

#### Terminal 2 — Frontend (React + Vite)
```bash
# 1. Open a new terminal and navigate to the frontend directory
cd frontend

# 2. Install npm dependencies
npm install

# 3. Start Vite development server
npm run dev
```
Frontend Client will be running at `http://localhost:5173/`.

---

### Option B: macOS (Intel & Apple Silicon M1/M2/M3)

#### Terminal 1 — Backend (Django + DRF)
```bash
# 1. Navigate to the backend directory
cd backend

# 2. Create a virtual environment
python3 -m venv .venv

# 3. Activate the virtual environment
source .venv/bin/activate

# 4. Upgrade pip and install backend dependencies
pip install --upgrade pip
pip install -r requirements.txt

# 5. Apply database migrations
python manage.py migrate

# 6. Seed the Nepali food database
python manage.py seed_data

# 7. Train the Decision Tree model
python manage.py train_decision_tree

# 8. Start the Django server
python manage.py runserver 8000
```

#### Terminal 2 — Frontend (React + Vite)
```bash
# 1. Open a new terminal and navigate to the frontend directory
cd frontend

# 2. Install dependencies
npm install

# 3. Start development server
npm run dev
```

---

### Option C: Windows

#### Using Windows Command Prompt (`cmd.exe`)

##### Terminal 1 — Backend:
```cmd
:: 1. Navigate to backend
cd backend

:: 2. Create virtual environment
python -m venv .venv

:: 3. Activate virtual environment
.venv\Scripts\activate.bat

:: 4. Upgrade pip and install dependencies
python -m pip install --upgrade pip
pip install -r requirements.txt

:: 5. Apply migrations
python manage.py migrate

:: 6. Seed data
python manage.py seed_data

:: 7. Train decision tree model
python manage.py train_decision_tree

:: 8. Run server
python manage.py runserver 8000
```

##### Terminal 2 — Frontend:
```cmd
:: 1. Navigate to frontend
cd frontend

:: 2. Install dependencies
npm install

:: 3. Start development server
npm run dev
```

---

#### Using Windows PowerShell

If you get a script execution policy restriction error in PowerShell, first run:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

##### Terminal 1 — Backend:
```powershell
# 1. Navigate to backend
cd backend

# 2. Create virtual environment
python -m venv .venv

# 3. Activate virtual environment
.venv\Scripts\Activate.ps1

# 4. Install dependencies
pip install -r requirements.txt

# 5. Run database migrations
python manage.py migrate

# 6. Seed Nepali food table
python manage.py seed_data

# 7. Train Decision Tree
python manage.py train_decision_tree

# 8. Start server
python manage.py runserver 8000
```

##### Terminal 2 — Frontend:
```powershell
# 1. Navigate to frontend
cd frontend

# 2. Install packages
npm install

# 3. Start client
npm run dev
```

---

## 5. One-Click Quick Start Scripts

If you have your environment set up and want to launch both servers together with a single command:

- **On Linux / macOS**:
  ```bash
  chmod +x run_project.sh
  ./run_project.sh
  ```

- **On Windows**:
  Double-click `run_project.bat` or run in terminal:
  ```cmd
  run_project.bat
  ```

---

## 6. Standalone ML Training & Evaluation

The machine learning module is completely standalone and can be trained and evaluated separately from the Django web server:

### Run Training Script
```bash
cd ml_training
python train_decision_tree.py
```
This trains the Decision Tree (`max_depth=4`), prints accuracy, precision, recall, confusion matrix, and feature importances, and exports `decision_tree.joblib` to both `ml_training/` and `backend/core/ml_artifacts/`.

### Run Interactive Jupyter Notebook
```bash
cd ml_training
jupyter notebook evaluate_model.ipynb
```
Visualizes the decision tree branching rules, confusion matrix heatmap, and distribution graphs.

---

## 7. API Endpoints Reference

| Category | Endpoint | Method | Description |
| :--- | :--- | :--- | :--- |
| **Auth** | `/api/auth/signup/` | `POST` | Register user account |
| **Auth** | `/api/auth/login/` | `POST` | Login & receive token |
| **Auth** | `/api/auth/logout/` | `POST` | Invalidate token |
| **Auth** | `/api/auth/me/` | `GET` | Get user profile and latest health assessment |
| **Assessment** | `/api/assessment/` | `POST` | Submit health assessment questionnaire |
| **Assessment** | `/api/assessment/latest/` | `GET` | Get latest nutritional targets |
| **Assessment** | `/api/assessment/history/` | `GET` | Get chronological assessment history |
| **Assessment** | `/api/assessment/<id>/` | `DELETE` | Delete assessment record |
| **Explainability** | `/api/food-pool/` | `GET` | View qualified foods, clinical daily limits & exclusion reasons |
| **Meal Plan** | `/api/meal-plan/generate/` | `POST` | Generate new 3-day personalized Nepali meal plan |
| **Meal Plan** | `/api/meal-plan/latest/` | `GET` | Retrieve active 3-day meal plan |
| **Meal Plan** | `/api/meal-plan/regenerate-meal/` | `POST` | Regenerate a specific meal slot |

---

## 8. Common Troubleshooting

1. **Port Already in Use**:
   - If port 8000 is occupied: `python manage.py runserver 8080`
   - If port 5173 is occupied: Vite will automatically suggest port 5174.
2. **Missing Database / Table Error**:
   - Run `python manage.py migrate` followed by `python manage.py seed_data`.
3. **Missing Model Artifact**:
   - If you see `decision_tree.joblib not found`, run: `python manage.py train_decision_tree`.
4. **Vite Backend Connection**:
   - Ensure the backend is running at `http://127.0.0.1:8000` or `http://localhost:8000`. By default, Vite proxies requests or connects directly through `src/api.js`.

