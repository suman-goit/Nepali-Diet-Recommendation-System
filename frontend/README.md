# Nepali Diet Recommendation System — Frontend Client (React + Vite)

This is the simplified, clean React + Vite client interface for the Nepali Diet Recommendation System.

---

## 1. Features & Screens
- **Dashboard (`/`)**: Displays personalized daily energy and macronutrient targets on an authentic visual Thali Dial, progress tracking against previous assessments, and daily hydration tracker.
- **Health Assessment (`/assessment`)**: Questionnaire capturing gender, age, height, weight, activity level, goal, dietary preference, region, medical conditions, and allergies with live target estimation preview.
- **3-Day Meal Plan (`/meal-plan`)**: 3-day meal plans featuring authentic Nepali dishes (Breakfast, Lunch, Dinner), ingredient portions in grams, cooking steps, meal regeneration, and clinical recommendation explainability.
- **Grocery Checklist (`/grocery`)**: Consolidated shopping list aggregated across all 3 days, categorized with item checkboxes and print view.
- **Assessment History (`/history`)**: Chronological assessment records with PDF print and deletion options.
- **User Profile (`/profile`) & Auth (`/login`, `/signup`)**: Token-based authentication and account settings.

---

## 2. Setup and Execution

```bash
# 1. Enter frontend directory
cd frontend

# 2. Install dependencies (if not already installed)
npm install

# 3. Start development server
npm run dev
```

The application will be running at `http://localhost:5173`.
Make sure the Django backend is running at `http://localhost:8000`.
