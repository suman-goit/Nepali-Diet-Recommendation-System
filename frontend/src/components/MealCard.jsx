import { useState } from "react";

export default function MealCard({ meal, onRegenerate, regenerating }) {
  const totals = meal.totals || {};
  const [showSteps, setShowSteps] = useState(false);

  return (
    <div className="meal-card" style={{ marginBottom: "20px" }}>
      <div
        className="meal-card-head"
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "flex-start",
          flexWrap: "wrap",
          gap: "8px",
        }}
      >
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <span className="meal-type-tag" style={{ fontWeight: 700, fontSize: "0.85rem" }}>
              {meal.meal_type}
            </span>
            {meal.cooking_time_mins && (
              <span
                className="tag-pill"
                style={{
                  background: "var(--turmeric-soft)",
                  color: "var(--turmeric)",
                  border: "1px solid var(--line)",
                }}
              >
                Prep: {meal.cooking_time_mins} mins
              </span>
            )}
          </div>
          {meal.recipe_name && (
            <div style={{ marginTop: "6px" }}>
              <div style={{ fontWeight: 600, fontSize: "1.05rem", color: "var(--terrace-dark)" }}>
                {meal.recipe_name}
              </div>
              {meal.nepali_name && (
                <div style={{ fontSize: "0.88rem", color: "var(--ink-soft)", fontStyle: "italic" }}>
                  {meal.nepali_name}
                </div>
              )}
            </div>
          )}
        </div>

        <button
          className="btn btn-ghost btn-sm"
          onClick={onRegenerate}
          disabled={regenerating}
        >
          {regenerating ? "Regenerating…" : "Regenerate Dish"}
        </button>
      </div>

      <div style={{ marginTop: "14px" }}>
        <div
          style={{
            fontSize: "0.78rem",
            textTransform: "uppercase",
            letterSpacing: "0.05em",
            color: "var(--ink-soft)",
            fontWeight: 600,
            marginBottom: "6px",
          }}
        >
          Ingredients & Portions:
        </div>

        {meal.items.length === 0 ? (
          <p style={{ color: "var(--ink-soft)", fontSize: "0.85rem" }}>
            No items found for this meal within current constraints.
          </p>
        ) : (
          meal.items.map((item) => (
            <div
              className="food-item"
              key={item.id}
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                padding: "8px 0",
              }}
            >
              <div>
                <div className="fname" style={{ fontSize: "0.92rem", fontWeight: 500 }}>
                  {item.food.name}
                </div>
                {item.food.nepali_name && (
                  <div className="fnepali" style={{ color: "var(--ink-soft)", fontSize: "0.8rem" }}>
                    {item.food.nepali_name} ({item.food.household_measure})
                  </div>
                )}
              </div>
              <div className="fgrams" style={{ textAlign: "right" }}>
                <div style={{ fontWeight: 600 }}>{item.grams}g</div>
                <div style={{ fontSize: "0.75rem", color: "var(--ink-soft)" }}>
                  {Math.round(item.food.calories * (item.grams / 100))} kcal
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {meal.recipe_steps && (
        <div style={{ marginTop: "12px", borderTop: "1px dashed var(--line)", paddingTop: "10px" }}>
          <button
            type="button"
            onClick={() => setShowSteps((s) => !s)}
            style={{
              background: "none",
              border: "none",
              padding: 0,
              fontSize: "0.82rem",
              color: "var(--terrace)",
              fontWeight: 600,
              cursor: "pointer",
            }}
          >
            {showSteps ? "Hide Preparation & Cooking Steps" : "View Preparation & Cooking Steps"}
          </button>
          {showSteps && (
            <div
              style={{
                background: "var(--terrace-light)",
                borderRadius: "var(--radius)",
                padding: "10px 14px",
                marginTop: "8px",
                fontSize: "0.85rem",
                lineHeight: 1.5,
                color: "var(--ink)",
              }}
            >
              {meal.recipe_steps}
            </div>
          )}
        </div>
      )}

      <div
        className="meal-totals"
        style={{
          display: "flex",
          gap: "8px",
          flexWrap: "wrap",
          marginTop: "14px",
          borderTop: "1px solid var(--line)",
          paddingTop: "10px",
        }}
      >
        <span className="macro-badge calories">{Math.round(totals.calories || 0)} kcal</span>
        <span className="macro-badge protein">Protein: {Math.round(totals.protein_g || 0)}g</span>
        <span className="macro-badge carbs">Carbs: {Math.round(totals.carbs_g || 0)}g</span>
        <span className="macro-badge fat">Fat: {Math.round(totals.fat_g || 0)}g</span>
      </div>
    </div>
  );
}
