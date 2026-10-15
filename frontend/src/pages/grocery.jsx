import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, ApiError } from "../api";
import { useAuth } from "../context/AuthContext";

export default function Grocery() {
  const { profile } = useAuth();
  const [plan, setPlan] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [checkedItems, setCheckedItems] = useState({});

  useEffect(() => {
    loadMealPlan();
  }, []);

  async function loadMealPlan() {
    setLoading(true);
    try {
      const data = await api.mealPlanLatest();
      setPlan(data);
    } catch (err) {
      if (err instanceof ApiError && err.status === 404) {
        setPlan(null);
      } else {
        setError(err.message);
      }
    } finally {
      setLoading(false);
    }
  }

  function toggleCheck(id) {
    setCheckedItems((prev) => ({ ...prev, [id]: !prev[id] }));
  }

  if (loading) {
    return (
      <div className="center-loading">
        <div className="spinner" />
      </div>
    );
  }

  if (!profile) {
    return (
      <div className="page">
        <div className="empty-state card">
          <h3>Complete your health assessment first</h3>
          <p>We need your nutritional targets and active meal plan to generate your grocery list.</p>
          <Link to="/assessment" className="btn btn-primary" style={{ marginTop: 12 }}>
            Start Health Assessment
          </Link>
        </div>
      </div>
    );
  }

  if (!plan || !plan.days || plan.days.length === 0) {
    return (
      <div className="page">
        <div className="empty-state card">
          <h3>No Active Meal Plan Found</h3>
          <p>Please generate a 3-day meal plan first to view your aggregated grocery checklist.</p>
          <Link to="/meal-plan" className="btn btn-primary" style={{ marginTop: 12 }}>
            Go to Meal Plan
          </Link>
        </div>
      </div>
    );
  }

  // Aggregate ingredients across all 3 days
  const groupedCategories = {};
  plan.days.forEach((day) => {
    day.meals.forEach((meal) => {
      meal.items.forEach((item) => {
        const cat = item.food.category || "General / Misc";
        const fid = item.food.food_id || item.food.id;
        if (!groupedCategories[cat]) {
          groupedCategories[cat] = {};
        }
        if (!groupedCategories[cat][fid]) {
          groupedCategories[cat][fid] = {
            id: fid,
            name: item.food.name,
            nepali_name: item.food.nepali_name,
            category: item.food.category,
            measure: item.food.household_measure,
            totalGrams: 0,
          };
        }
        groupedCategories[cat][fid].totalGrams += Math.round(item.grams);
      });
    });
  });

  return (
    <div className="page">
      <div
        className="page-header"
        style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end" }}
      >
        <div>
          <span className="eyebrow">Shopping & Pantry</span>
          <h1>3-Day Consolidated Grocery Checklist</h1>
          <p style={{ color: "var(--ink-soft)" }}>
            Aggregated ingredient quantities required for all 3 days of your personalized Nepali meal plan.
          </p>
        </div>
        <button className="btn btn-ghost btn-sm" onClick={() => window.print()}>
          Print Grocery List
        </button>
      </div>

      {error && <div className="error-banner">{error}</div>}

      <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
        {Object.entries(groupedCategories).map(([category, itemsMap]) => {
          const items = Object.values(itemsMap);
          return (
            <div className="card" key={category}>
              <h3
                style={{
                  color: "var(--terrace)",
                  fontSize: "1.15rem",
                  borderBottom: "1px solid var(--line)",
                  paddingBottom: "8px",
                  marginBottom: "14px",
                }}
              >
                Category: {category}
              </h3>
              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))",
                  gap: "12px",
                }}
              >
                {items.map((item) => {
                  const isDone = checkedItems[item.id];
                  return (
                    <label
                      key={item.id}
                      className={`checkbox-card ${isDone ? "selected" : ""}`}
                      style={{
                        padding: "12px 14px",
                        textDecoration: isDone ? "line-through" : "none",
                        opacity: isDone ? 0.6 : 1,
                      }}
                    >
                      <input
                        type="checkbox"
                        checked={!!isDone}
                        onChange={() => toggleCheck(item.id)}
                      />
                      <div style={{ flex: 1 }}>
                        <div style={{ fontWeight: 600 }}>{item.name}</div>
                        {item.nepali_name && (
                          <div style={{ fontSize: "0.78rem", color: "var(--ink-soft)" }}>
                            {item.nepali_name}
                          </div>
                        )}
                      </div>
                      <div
                        style={{
                          fontFamily: "var(--font-mono)",
                          fontWeight: 700,
                          color: "var(--terrace-dark)",
                        }}
                      >
                        {item.totalGrams}g
                      </div>
                    </label>
                  );
                })}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
