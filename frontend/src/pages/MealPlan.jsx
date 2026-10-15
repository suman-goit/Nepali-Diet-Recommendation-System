import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, ApiError } from "../api";
import { useAuth } from "../context/AuthContext";
import MealCard from "../components/MealCard";

export default function MealPlan() {
  const { profile } = useAuth();
  const [plan, setPlan] = useState(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState("");
  const [activeDay, setActiveDay] = useState(1);
  const [regeneratingKey, setRegeneratingKey] = useState(null);
  const [showExplain, setShowExplain] = useState(false);
  const [foodPool, setFoodPool] = useState(null);
  const [loadingPool, setLoadingPool] = useState(false);
  const [checkedGrocery, setCheckedGrocery] = useState({});
  const [copied, setCopied] = useState(false);
  const [grocerySearch, setGrocerySearch] = useState("");
  const [groceryCategoryFilter, setGroceryCategoryFilter] = useState("ALL");

  useEffect(() => {
    loadLatest();
  }, []);

  async function loadLatest() {
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

  async function handleGenerate() {
    setGenerating(true);
    setError("");
    try {
      const data = await api.generateMealPlan();
      setPlan(data);
      setActiveDay(1);
    } catch (err) {
      setError(err.message);
    } finally {
      setGenerating(false);
    }
  }

  async function handleRegenerate(dayNumber, mealType) {
    const key = `${dayNumber}-${mealType}`;
    setRegeneratingKey(key);
    setError("");
    try {
      const updatedDay = await api.regenerateMeal(dayNumber, mealType);
      setPlan((prev) => ({
        ...prev,
        days: prev.days.map((d) => (d.day_number === dayNumber ? updatedDay : d)),
      }));
    } catch (err) {
      setError(err.message);
    } finally {
      setRegeneratingKey(null);
    }
  }

  async function handleOpenExplain() {
    setShowExplain(true);
    if (!foodPool) {
      setLoadingPool(true);
      try {
        const pool = await api.personalizedFoodPool();
        setFoodPool(pool);
      } catch (err) {
        console.error(err);
      } finally {
        setLoadingPool(false);
      }
    }
  }

  function handleCopyPlan() {
    if (!plan || !plan.days) return;
    const currentDay = plan.days.find((d) => d.day_number === activeDay) || plan.days[0];
    let text = `Nepali Diet Chart - Day ${currentDay.day_number} (DFTQC 2012)\n`;
    text += `Target: ${Math.round(profile.target_calories)} kcal | Protein: ${Math.round(profile.target_protein_g)}g\n\n`;

    currentDay.meals.forEach((m) => {
      text += `${m.meal_type.toUpperCase()}: ${m.recipe_name || "Meal"} (${Math.round(m.totals?.calories || 0)} kcal)\n`;
      m.items.forEach((it) => {
        text += `  - ${it.food.name} (${it.food.nepali_name || ""}): ${it.grams}g\n`;
      });
      text += `\n`;
    });

    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2500);
  }

  function toggleGroceryCheck(id) {
    setCheckedGrocery((prev) => ({ ...prev, [id]: !prev[id] }));
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
          <h3>Complete a health assessment first</h3>
          <p>We need your nutritional targets before generating a meal plan.</p>
          <Link to="/assessment" className="btn btn-primary" style={{ marginTop: 12 }}>
            Start Your Health Assessment
          </Link>
        </div>
      </div>
    );
  }

  if (!plan) {
    return (
      <div className="page">
        <div className="empty-state card">
          <h3>No Meal Plan Generated Yet</h3>
          <p>Generate a personalized 3-day meal plan based on your health assessment.</p>
          {error && <div className="error-banner" style={{ marginTop: 12 }}>{error}</div>}
          <button
            className="btn btn-primary"
            onClick={handleGenerate}
            disabled={generating}
            style={{ marginTop: 12 }}
          >
            {generating ? "Generating…" : "Generate 3-Day Meal Plan"}
          </button>
        </div>
      </div>
    );
  }

  // Aggregate ingredients across all 3 days for Grocery View
  const groupedGrocery = {};
  let allGroceryItems = [];

  plan.days.forEach((d) => {
    d.meals.forEach((m) => {
      m.items.forEach((it) => {
        const cat = it.food.category || "General / Misc";
        const fid = it.food.food_id || it.food.id;
        if (!groupedGrocery[cat]) groupedGrocery[cat] = {};
        if (!groupedGrocery[cat][fid]) {
          groupedGrocery[cat][fid] = {
            id: fid,
            name: it.food.name,
            nepali_name: it.food.nepali_name,
            category: it.food.category,
            measure: it.food.household_measure,
            totalGrams: 0,
          };
        }
        groupedGrocery[cat][fid].totalGrams += Math.round(it.grams);
      });
    });
  });

  Object.values(groupedGrocery).forEach((catMap) => {
    allGroceryItems = allGroceryItems.concat(Object.values(catMap));
  });

  const totalGroceryCount = allGroceryItems.length;
  const checkedGroceryCount = allGroceryItems.filter((it) => checkedGrocery[it.id]).length;
  const groceryProgressPct =
    totalGroceryCount > 0 ? Math.round((checkedGroceryCount / totalGroceryCount) * 100) : 0;

  const day = plan.days.find((d) => d.day_number === activeDay) || plan.days[0];
  const dayTotals = day.meals.reduce(
    (acc, m) => {
      const t = m.totals || {};
      acc.calories += t.calories || 0;
      acc.protein_g += t.protein_g || 0;
      acc.carbs_g += t.carbs_g || 0;
      acc.fat_g += t.fat_g || 0;
      return acc;
    },
    { calories: 0, protein_g: 0, carbs_g: 0, fat_g: 0 }
  );

  const mealOrder = ["Breakfast", "Lunch", "Dinner"];
  const sortedMeals = [...day.meals].sort(
    (a, b) => mealOrder.indexOf(a.meal_type) - mealOrder.indexOf(b.meal_type)
  );

  const targetKcal = profile.target_calories || 1;
  const targetProtein = profile.target_protein_g || 1;
  const targetCarbs = profile.target_carbs_g || 1;
  const targetFat = profile.target_fat_g || 1;

  const calPct = Math.round((dayTotals.calories / targetKcal) * 100);
  const proPct = Math.round((dayTotals.protein_g / targetProtein) * 100);
  const carbPct = Math.round((dayTotals.carbs_g / targetCarbs) * 100);
  const fatPct = Math.round((dayTotals.fat_g / targetFat) * 100);

  return (
    <div className="page">
      <div
        className="page-header"
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "flex-end",
          flexWrap: "wrap",
          gap: "12px",
        }}
      >
        <div>
          <span className="eyebrow">Personalized Nutrition</span>
          <h1>Your 3-Day Meal Plan</h1>
        </div>
        <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
          <button className="btn btn-ghost btn-sm" onClick={() => window.print()}>
            Print Meal Plan
          </button>
          <button className="btn btn-ghost btn-sm" onClick={handleCopyPlan}>
            {copied ? "Copied to Clipboard!" : "Copy Meal Plan"}
          </button>
          <button className="btn btn-ghost btn-sm" onClick={handleOpenExplain}>
            Why These Foods?
          </button>
          <button className="btn btn-primary btn-sm" onClick={handleGenerate} disabled={generating}>
            {generating ? "Regenerating…" : "Generate New Plan"}
          </button>
        </div>
      </div>

      {error && <div className="error-banner">{error}</div>}

      {/* Navigation Tabs */}
      <div className="day-tabs" style={{ marginBottom: "20px" }}>
        {plan.days.map((d) => (
          <button
            key={d.id}
            className={activeDay === d.day_number ? "active" : ""}
            onClick={() => setActiveDay(d.day_number)}
          >
            Day {d.day_number}
          </button>
        ))}
        <button
          className={activeDay === "grocery" ? "active" : ""}
          onClick={() => setActiveDay("grocery")}
          style={{ display: "flex", alignItems: "center", gap: "6px" }}
        >
          <span>3-Day Grocery Checklist</span>
          {totalGroceryCount > 0 && (
            <span
              style={{
                fontSize: "0.72rem",
                background: activeDay === "grocery" ? "var(--terrace)" : "var(--line)",
                color: activeDay === "grocery" ? "#fff" : "var(--ink)",
                padding: "2px 6px",
                borderRadius: "10px",
                fontWeight: 700,
              }}
            >
              {checkedGroceryCount}/{totalGroceryCount}
            </span>
          )}
        </button>
      </div>

      {/* ACTIVE VIEW */}
      {activeDay === "grocery" ? (
        /* STRUCTURED TABLE GROCERY VIEW */
        <div>
          <div className="card" style={{ marginBottom: 20 }}>
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                flexWrap: "wrap",
                gap: 12,
                marginBottom: 14,
              }}
            >
              <div>
                <h2 style={{ fontSize: "1.25rem", margin: 0 }}>Consolidated 3-Day Grocery List</h2>
                <p style={{ color: "var(--ink-soft)", fontSize: "0.85rem", margin: "4px 0 0 0" }}>
                  Aggregated ingredient quantities required for all 9 meals across your 3-day meal plan.
                </p>
              </div>
              <button className="btn btn-ghost btn-sm" onClick={() => window.print()}>
                Print Grocery List
              </button>
            </div>

            {/* Shopping Progress */}
            <div
              style={{
                background: "var(--paper)",
                padding: "12px 16px",
                borderRadius: "var(--radius)",
                marginBottom: 16,
              }}
            >
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  fontSize: "0.85rem",
                  fontWeight: 600,
                  marginBottom: 6,
                }}
              >
                <span>Purchased Items:</span>
                <span style={{ color: "var(--terrace-dark)" }}>
                  {checkedGroceryCount} of {totalGroceryCount} items ({groceryProgressPct}%)
                </span>
              </div>
              <div
                style={{
                  width: "100%",
                  height: 8,
                  background: "var(--line)",
                  borderRadius: 4,
                  overflow: "hidden",
                }}
              >
                <div
                  style={{
                    width: `${groceryProgressPct}%`,
                    height: "100%",
                    background: "var(--terrace)",
                    transition: "width 0.3s ease",
                  }}
                />
              </div>
            </div>

            {/* Filter and Search Bar */}
            <div style={{ display: "flex", gap: "10px", flexWrap: "wrap", marginBottom: 16 }}>
              <input
                type="text"
                placeholder="Search ingredients (e.g. Rice, Dal, Ghyu, Palungo)..."
                value={grocerySearch}
                onChange={(e) => setGrocerySearch(e.target.value)}
                style={{
                  flex: "1 1 240px",
                  padding: "8px 12px",
                  border: "1px solid var(--line)",
                  borderRadius: "var(--radius)",
                  fontSize: "0.88rem",
                }}
              />
              <select
                value={groceryCategoryFilter}
                onChange={(e) => setGroceryCategoryFilter(e.target.value)}
                style={{
                  flex: "0 1 200px",
                  padding: "8px 12px",
                  border: "1px solid var(--line)",
                  borderRadius: "var(--radius)",
                  fontSize: "0.88rem",
                }}
              >
                <option value="ALL">All Categories</option>
                {Object.keys(groupedGrocery).map((cat) => (
                  <option key={cat} value={cat}>
                    {cat}
                  </option>
                ))}
              </select>
            </div>

            {/* Structured Table */}
            <div style={{ overflowX: "auto" }}>
              <table className="grocery-table">
                <thead>
                  <tr>
                    <th style={{ width: "50px", textAlign: "center" }}>Status</th>
                    <th>Ingredient Name (नेपाली नाम)</th>
                    <th>Category</th>
                    <th>Standard Household Unit</th>
                    <th style={{ textAlign: "right" }}>3-Day Total Quantity</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(groupedGrocery)
                    .filter(([cat]) => groceryCategoryFilter === "ALL" || groceryCategoryFilter === cat)
                    .map(([category, itemsMap]) => {
                      const items = Object.values(itemsMap).filter((it) => {
                        if (!grocerySearch) return true;
                        const q = grocerySearch.toLowerCase();
                        return (
                          it.name.toLowerCase().includes(q) ||
                          (it.nepali_name && it.nepali_name.toLowerCase().includes(q))
                        );
                      });

                      if (items.length === 0) return null;

                      return (
                        <tr key={category} className="category-group">
                          <td colSpan={5} style={{ padding: 0 }}>
                            <table style={{ width: "100%", borderCollapse: "collapse" }}>
                              <tbody>
                                <tr className="category-header-row">
                                  <td colSpan={5}>
                                    Category: {category} ({items.length} items)
                                  </td>
                                </tr>
                                {items.map((item) => {
                                  const isDone = !!checkedGrocery[item.id];
                                  return (
                                    <tr
                                      key={item.id}
                                      className={`item-row ${isDone ? "completed" : ""}`}
                                      onClick={() => toggleGroceryCheck(item.id)}
                                      style={{ cursor: "pointer" }}
                                    >
                                      <td
                                        style={{ width: "50px", textAlign: "center" }}
                                        onClick={(e) => e.stopPropagation()}
                                      >
                                        <input
                                          type="checkbox"
                                          checked={isDone}
                                          onChange={() => toggleGroceryCheck(item.id)}
                                          style={{ cursor: "pointer" }}
                                        />
                                      </td>
                                      <td>
                                        <div style={{ fontWeight: 600, fontSize: "0.92rem" }}>
                                          {item.name}
                                        </div>
                                        {item.nepali_name && (
                                          <div
                                            style={{
                                              fontSize: "0.78rem",
                                              color: "var(--ink-soft)",
                                            }}
                                          >
                                            {item.nepali_name}
                                          </div>
                                        )}
                                      </td>
                                      <td>
                                        <span className="tag-pill">{item.category}</span>
                                      </td>
                                      <td style={{ color: "var(--ink-soft)", fontSize: "0.85rem" }}>
                                        {item.measure || "100g serving"}
                                      </td>
                                      <td
                                        style={{
                                          textAlign: "right",
                                          fontFamily: "var(--font-mono)",
                                          fontWeight: 700,
                                          color: "var(--terrace-dark)",
                                          fontSize: "0.95rem",
                                        }}
                                      >
                                        {item.totalGrams}g
                                      </td>
                                    </tr>
                                  );
                                })}
                              </tbody>
                            </table>
                          </td>
                        </tr>
                      );
                    })}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      ) : (
        /* DAY MEAL PLAN VIEW */
        <div>
          <div className="plan-summary">
            <div className="stat-block">
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline" }}>
                <div className="val">
                  {Math.round(dayTotals.calories)}{" "}
                  <small style={{ fontSize: "0.75rem", color: "var(--ink-soft)" }}>kcal</small>
                </div>
                <span className="macro-badge calories">{calPct}%</span>
              </div>
              <div className="lbl">Target: {Math.round(profile.target_calories)} kcal</div>
              <div
                style={{
                  width: "100%",
                  height: 6,
                  background: "var(--line)",
                  borderRadius: 3,
                  marginTop: 8,
                  overflow: "hidden",
                }}
              >
                <div
                  style={{
                    width: `${Math.min(100, calPct)}%`,
                    height: "100%",
                    background: "var(--turmeric)",
                  }}
                />
              </div>
            </div>

            <div className="stat-block">
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline" }}>
                <div className="val">{Math.round(dayTotals.protein_g)}g</div>
                <span className="macro-badge protein">{proPct}%</span>
              </div>
              <div className="lbl">Target: {Math.round(profile.target_protein_g)}g protein</div>
              <div
                style={{
                  width: "100%",
                  height: 6,
                  background: "var(--line)",
                  borderRadius: 3,
                  marginTop: 8,
                  overflow: "hidden",
                }}
              >
                <div
                  style={{
                    width: `${Math.min(100, proPct)}%`,
                    height: "100%",
                    background: "var(--terrace)",
                  }}
                />
              </div>
            </div>

            <div className="stat-block">
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline" }}>
                <div className="val">{Math.round(dayTotals.carbs_g)}g</div>
                <span className="macro-badge carbs">{carbPct}%</span>
              </div>
              <div className="lbl">Target: {Math.round(profile.target_carbs_g)}g carbs</div>
              <div
                style={{
                  width: "100%",
                  height: 6,
                  background: "var(--line)",
                  borderRadius: 3,
                  marginTop: 8,
                  overflow: "hidden",
                }}
              >
                <div
                  style={{
                    width: `${Math.min(100, carbPct)}%`,
                    height: "100%",
                    background: "#0284c7",
                  }}
                />
              </div>
            </div>

            <div className="stat-block">
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline" }}>
                <div className="val">{Math.round(dayTotals.fat_g)}g</div>
                <span className="macro-badge fat">{fatPct}%</span>
              </div>
              <div className="lbl">Target: {Math.round(profile.target_fat_g)}g fat</div>
              <div
                style={{
                  width: "100%",
                  height: 6,
                  background: "var(--line)",
                  borderRadius: 3,
                  marginTop: 8,
                  overflow: "hidden",
                }}
              >
                <div
                  style={{
                    width: `${Math.min(100, fatPct)}%`,
                    height: "100%",
                    background: "#ea580c",
                  }}
                />
              </div>
            </div>
          </div>

          {sortedMeals.map((meal) => (
            <MealCard
              key={meal.id}
              meal={meal}
              onRegenerate={() => handleRegenerate(day.day_number, meal.meal_type)}
              regenerating={regeneratingKey === `${day.day_number}-${meal.meal_type}`}
            />
          ))}
        </div>
      )}

      {/* EXPLAINABILITY MODAL */}
      {showExplain && (
        <div
          style={{
            position: "fixed",
            inset: 0,
            background: "rgba(0,0,0,0.5)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 100,
            padding: 20,
          }}
        >
          <div
            className="card"
            style={{ maxWidth: 700, width: "100%", maxHeight: "85vh", overflowY: "auto" }}
          >
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                marginBottom: 16,
              }}
            >
              <h3>Clinical Recommendation Explainability</h3>
              <button className="btn btn-ghost btn-sm" onClick={() => setShowExplain(false)}>
                Close
              </button>
            </div>

            {loadingPool ? (
              <div className="center-loading">
                <div className="spinner" />
              </div>
            ) : foodPool ? (
              <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
                <div
                  style={{
                    background: "var(--terrace-light)",
                    padding: "14px 18px",
                    borderRadius: "var(--radius)",
                  }}
                >
                  <div style={{ fontWeight: 600, color: "var(--terrace-dark)" }}>
                    {foodPool.count} Eligible Nepali Foods Qualified
                  </div>
                  <div style={{ fontSize: "0.84rem", color: "var(--ink-soft)", marginTop: 4 }}>
                    Passed Allergen, Season ({profile.region}), Dietary preference (
                    {profile.food_preference}), and Decision Tree Medical validation.
                  </div>
                </div>

                {Object.keys(foodPool.daily_limits || {}).length > 0 && (
                  <div>
                    <h4 style={{ fontSize: "0.92rem", marginBottom: 6 }}>
                      Clinical Daily Limits (WHO / ADA Guidelines):
                    </h4>
                    <div style={{ display: "flex", gap: "10px", flexWrap: "wrap" }}>
                      {Object.entries(foodPool.daily_limits).map(([key, val]) => (
                        <span key={key} className="macro-badge fat">
                          {key.replace("_", " ")}: {val}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                <div>
                  <h4 style={{ fontSize: "0.92rem", marginBottom: 6 }}>
                    Excluded Foods & Clinical Reasons:
                  </h4>
                  <div
                    style={{
                      display: "flex",
                      flexDirection: "column",
                      gap: "8px",
                      maxHeight: "250px",
                      overflowY: "auto",
                    }}
                  >
                    {Object.entries(foodPool.excluded || {})
                      .slice(0, 20)
                      .map(([fid, reasons]) => (
                        <div
                          key={fid}
                          style={{
                            padding: "8px 12px",
                            background: "var(--paper)",
                            borderRadius: "var(--radius)",
                            fontSize: "0.82rem",
                          }}
                        >
                          <strong>Food #{fid}:</strong>{" "}
                          <span style={{ color: "var(--crimson)" }}>{reasons.join(" · ")}</span>
                        </div>
                      ))}
                  </div>
                </div>
              </div>
            ) : (
              <p>Failed to load explainability data.</p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
