import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { api } from "../api";
import DeltaFeed from "../components/DeltaFeed";

export default function Home() {
  const { username, profile, ready } = useAuth();
  const [history, setHistory] = useState(null);
  const [loading, setLoading] = useState(true);
  const [glassesDrank, setGlassesDrank] = useState(0);

  useEffect(() => {
    if (!profile) {
      setLoading(false);
      return;
    }
    api
      .assessmentHistory()
      .then(setHistory)
      .catch(() => setHistory(null))
      .finally(() => setLoading(false));
  }, [profile]);

  if (!ready || loading) {
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
          <h3>Welcome, {username}</h3>
          <p>You haven't completed a health assessment yet.</p>
          <Link to="/assessment" className="btn btn-primary" style={{ marginTop: 12 }}>
            Start Your Health Assessment
          </Link>
        </div>
      </div>
    );
  }

  const caloriePct = profile.target_calories
    ? Math.min(100, Math.round((profile.target_calories / 3000) * 100))
    : 0;
  const proteinPct = profile.target_protein_g
    ? Math.min(100, Math.round((profile.target_protein_g / 150) * 100))
    : 0;

  const previous = history && history.length > 1 ? history[1] : null;
  const weightKg = profile.weight_kg || 65;
  const targetWaterLiters = ((weightKg * 35) / 1000).toFixed(1);
  const totalGlasses = Math.min(12, Math.max(6, Math.round((weightKg * 35) / 250)));

  return (
    <div className="page">
      <div className="page-header">
        <span className="eyebrow">Dashboard</span>
        <h1>Namaste, {username}</h1>
      </div>

      <div className="card" style={{ marginBottom: 16 }}>
        <h3>Today's Nutritional Targets</h3>
        <div className="thali">
          <div className="thali-plate" style={{ "--pct": caloriePct }}>
            <div className="thali-reading">
              <span className="num">{Math.round(profile.target_calories)}</span>
              <span className="label">kcal target</span>
            </div>
          </div>
          <div className="thali-plate" style={{ "--pct": proteinPct }}>
            <div className="thali-reading">
              <span className="num">{Math.round(profile.target_protein_g)}g</span>
              <span className="label">protein target</span>
            </div>
          </div>
          <div className="thali-legend">
            <div className="row">
              <span className="swatch" style={{ background: "var(--terrace)" }} />
              BMI {profile.bmi} · BMR {Math.round(profile.bmr)} kcal
            </div>
            <div className="row">
              <span className="swatch" style={{ background: "var(--turmeric)" }} />
              TDEE {Math.round(profile.tdee)} kcal/day
            </div>
            <div className="row">
              <span className="swatch" style={{ background: "var(--indigo)" }} />
              Carbs {Math.round(profile.target_carbs_g)}g · Fat{" "}
              {Math.round(profile.target_fat_g)}g · Fiber {Math.round(profile.target_fiber_g)}g
            </div>
          </div>
        </div>
        <Link to="/assessment" className="btn btn-ghost btn-sm" style={{ marginTop: 16 }}>
          Retake Assessment
        </Link>
      </div>

      <div className="card" style={{ marginBottom: 16 }}>
        <h3>Progress Since Last Assessment</h3>
        <DeltaFeed current={profile} previous={previous} />
      </div>

      <div className="card" style={{ marginBottom: 16 }}>
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            marginBottom: 8,
          }}
        >
          <h3>Daily Hydration Goal</h3>
          <span
            style={{
              fontFamily: "var(--font-mono)",
              fontWeight: 700,
              color: "#0284c7",
              fontSize: "0.95rem",
            }}
          >
            {targetWaterLiters} Liters / day ({glassesDrank} of {totalGlasses} glasses)
          </span>
        </div>
        <p style={{ color: "var(--ink-soft)", fontSize: "0.85rem", marginBottom: 14 }}>
          Recommended for your body weight ({weightKg} kg) for digestion and metabolic balance. Click a slot to track:
        </p>

        <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
          {Array.from({ length: totalGlasses }).map((_, idx) => {
            const isFilled = idx < glassesDrank;
            return (
              <button
                key={idx}
                type="button"
                onClick={() => setGlassesDrank(idx + 1 === glassesDrank ? idx : idx + 1)}
                style={{
                  background: isFilled ? "#0284c7" : "var(--paper)",
                  color: isFilled ? "#ffffff" : "var(--ink-soft)",
                  border: `1px solid ${isFilled ? "#0284c7" : "var(--line)"}`,
                  borderRadius: "6px",
                  padding: "6px 10px",
                  fontSize: "0.78rem",
                  fontFamily: "var(--font-mono)",
                  fontWeight: 600,
                  cursor: "pointer",
                  transition: "all 0.15s ease",
                }}
              >
                {isFilled ? `Glass ${idx + 1} ✓` : `Glass ${idx + 1}`}
              </button>
            );
          })}
        </div>
        {glassesDrank >= totalGlasses && (
          <div
            style={{
              marginTop: 10,
              fontSize: "0.82rem",
              color: "var(--terrace)",
              fontWeight: 600,
            }}
          >
            Daily hydration target reached!
          </div>
        )}
      </div>

      <div className="card">
        <h3>Personalized Meal Plan</h3>
        <p style={{ color: "var(--ink-soft)", marginBottom: 12 }}>
          Generate an authentic 3-day Nepali meal plan tailored to your health goals, medical conditions, and regional availability.
        </p>
        <Link to="/meal-plan" className="btn btn-primary">
          View Meal Plan
        </Link>
      </div>
    </div>
  );
}
