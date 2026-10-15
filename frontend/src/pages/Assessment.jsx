import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api";
import { useAuth } from "../context/AuthContext";

const ACTIVITY_LEVELS = ["Sedentary", "Lightly Active", "Moderate", "Very Active", "Extra Active"];
const GOALS = ["Weight Loss", "Maintenance", "Muscle Gain", "Healthy Living"];
const DIET_TYPES = ["Vegetarian", "Vegan", "Eggetarian", "Non-Vegetarian"];
const REGIONS = ["Mountain", "Hills", "Terai"];
const MEDICAL_CONDITIONS = [
  "Hypertension",
  "Diabetes",
  "Anaemia",
  "Underweight",
  "Obesity",
  "Lactose Intolerance",
  "Celiac",
];
const ALLERGIES = ["Milk", "Nuts", "Fish", "Gluten", "Egg"];
const MEAT_RESTRICTIONS = [
  { value: "Buff", label: "Buff (Buffalo Meat)" },
  { value: "Pork", label: "Pork" },
];

export default function Assessment() {
  const navigate = useNavigate();
  const { refreshMe } = useAuth();
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [form, setForm] = useState({
    gender: "Female",
    age: "",
    height_cm: "",
    weight_kg: "",
    activity_level: "Moderate",
    goal: "Maintenance",
    food_preference: "Vegetarian",
    region: "Hills",
    medical_conditions: [],
    allergies: [],
  });

  function update(field, value) {
    setForm((f) => ({ ...f, [field]: value }));
  }

  function toggleMulti(field, value) {
    setForm((f) => {
      const set = new Set(f[field]);
      set.has(value) ? set.delete(value) : set.add(value);
      return { ...f, [field]: Array.from(set) };
    });
  }

  // Calculate live preview metrics based on user input
  const heightM = Number(form.height_cm) / 100;
  const weightKg = Number(form.weight_kg);
  const ageVal = Number(form.age);

  const liveBmi = heightM > 0 && weightKg > 0 ? (weightKg / (heightM * heightM)).toFixed(1) : null;

  const bmrBase = 10 * weightKg + 6.25 * Number(form.height_cm) - 5 * ageVal;
  const liveBmr =
    weightKg && form.height_cm && ageVal
      ? Math.round(form.gender === "Male" ? bmrBase + 5 : bmrBase - 161)
      : null;

  const activityMultiplier =
    {
      "Sedentary": 1.2,
      "Lightly Active": 1.375,
      "Moderate": 1.55,
      "Very Active": 1.725,
      "Extra Active": 1.9,
    }[form.activity_level] || 1.2;

  const liveTdee = liveBmr ? Math.round(liveBmr * activityMultiplier) : null;

  const goalAdjustment =
    {
      "Weight Loss": -500,
      "Maintenance": 0,
      "Muscle Gain": 300,
      "Healthy Living": 0,
    }[form.goal] || 0;

  const liveTargetCalories = liveTdee ? Math.max(1200, liveTdee + goalAdjustment) : null;
  const liveProteinG = weightKg
    ? Math.round(weightKg * (form.goal === "Weight Loss" ? 1.1 : form.goal === "Muscle Gain" ? 1.3 : 0.85))
    : null;

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const payload = {
        gender: form.gender,
        age: Number(form.age),
        height_cm: Number(form.height_cm),
        weight_kg: Number(form.weight_kg),
        activity_level: form.activity_level,
        goal: form.goal,
        food_preference: form.food_preference,
        region: form.region,
        medical_conditions: form.medical_conditions.join(","),
        allergies: form.allergies.join(","),
      };
      await api.createAssessment(payload);
      await refreshMe();
      navigate("/");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="page">
      <div className="page-header">
        <span className="eyebrow">Health Assessment</span>
        <h1>Tell Us About Yourself</h1>
        <p style={{ color: "var(--ink-soft)" }}>
          Every assessment is recorded chronologically to track your progress.
          Your targets and personalized meal plan will be calculated from this data.
        </p>
      </div>

      <form className="card" onSubmit={handleSubmit} style={{ maxWidth: 640 }}>
        {error && <div className="error-banner">{error}</div>}

        <div className="field-row">
          <div className="field">
            <label>Gender</label>
            <select value={form.gender} onChange={(e) => update("gender", e.target.value)}>
              <option>Female</option>
              <option>Male</option>
            </select>
          </div>
          <div className="field">
            <label>Age</label>
            <input
              type="number"
              min="1"
              max="120"
              required
              value={form.age}
              onChange={(e) => update("age", e.target.value)}
            />
          </div>
        </div>

        <div className="field-row">
          <div className="field">
            <label>Height (cm)</label>
            <input
              type="number"
              step="0.1"
              required
              value={form.height_cm}
              onChange={(e) => update("height_cm", e.target.value)}
            />
          </div>
          <div className="field">
            <label>Weight (kg)</label>
            <input
              type="number"
              step="0.1"
              required
              value={form.weight_kg}
              onChange={(e) => update("weight_kg", e.target.value)}
            />
          </div>
        </div>

        <div className="field-row">
          <div className="field">
            <label>Activity Level</label>
            <select
              value={form.activity_level}
              onChange={(e) => update("activity_level", e.target.value)}
            >
              {ACTIVITY_LEVELS.map((a) => (
                <option key={a}>{a}</option>
              ))}
            </select>
          </div>
          <div className="field">
            <label>Goal</label>
            <select value={form.goal} onChange={(e) => update("goal", e.target.value)}>
              {GOALS.map((g) => (
                <option key={g}>{g}</option>
              ))}
            </select>
          </div>
        </div>

        <div className="field-row">
          <div className="field">
            <label>Food Preference</label>
            <select
              value={form.food_preference}
              onChange={(e) => update("food_preference", e.target.value)}
            >
              {DIET_TYPES.map((d) => (
                <option key={d}>{d}</option>
              ))}
            </select>
          </div>
          <div className="field">
            <label>Region</label>
            <select value={form.region} onChange={(e) => update("region", e.target.value)}>
              {REGIONS.map((r) => (
                <option key={r}>{r}</option>
              ))}
            </select>
          </div>
        </div>

        <div className="field">
          <label>Medical Conditions (optional)</label>
          <div style={{ display: "flex", flexWrap: "wrap", gap: "8px" }}>
            {MEDICAL_CONDITIONS.map((c) => (
              <label key={c} className="checkbox-row" style={{ fontSize: "0.85rem" }}>
                <input
                  type="checkbox"
                  checked={form.medical_conditions.includes(c)}
                  onChange={() => toggleMulti("medical_conditions", c)}
                />
                {c}
              </label>
            ))}
          </div>
        </div>

        {liveBmi && (
          <div
            style={{
              background: "var(--terrace-light)",
              border: "1px solid var(--line)",
              borderRadius: "var(--radius)",
              padding: "14px 16px",
              marginBottom: "16px",
            }}
          >
            <div
              style={{
                fontWeight: 600,
                fontSize: "0.85rem",
                color: "var(--terrace-dark)",
                marginBottom: 8,
              }}
            >
              Live Estimated Nutritional Targets
            </div>
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "repeat(auto-fit, minmax(120px, 1fr))",
                gap: "10px",
                fontSize: "0.88rem",
              }}
            >
              <div>BMI: <strong>{liveBmi}</strong></div>
              <div>BMR: <strong>{liveBmr} kcal</strong></div>
              <div>TDEE: <strong>{liveTdee} kcal</strong></div>
              <div>Target: <strong>{liveTargetCalories} kcal</strong></div>
              <div>Protein: <strong>{liveProteinG}g/day</strong></div>
            </div>
          </div>
        )}

        <div className="field">
          <label>Allergies (optional)</label>
          <div style={{ display: "flex", flexWrap: "wrap", gap: "8px" }}>
            {ALLERGIES.map((a) => (
              <label key={a} className="checkbox-row" style={{ fontSize: "0.85rem" }}>
                <input
                  type="checkbox"
                  checked={form.allergies.includes(a)}
                  onChange={() => toggleMulti("allergies", a)}
                />
                {a}
              </label>
            ))}
          </div>
        </div>

        <div className="field">
          <label>Cultural / Meat Restrictions (optional)</label>
          <div style={{ display: "flex", flexWrap: "wrap", gap: "8px" }}>
            {MEAT_RESTRICTIONS.map(({ value, label }) => (
              <label key={value} className="checkbox-row" style={{ fontSize: "0.85rem" }}>
                <input
                  type="checkbox"
                  checked={form.allergies.includes(value)}
                  onChange={() => toggleMulti("allergies", value)}
                />
                {label}
              </label>
            ))}
          </div>
        </div>

        <button className="btn btn-primary btn-block" disabled={loading} style={{ marginTop: 8 }}>
          {loading ? "Saving…" : "Save Assessment"}
        </button>
      </form>
    </div>
  );
}
