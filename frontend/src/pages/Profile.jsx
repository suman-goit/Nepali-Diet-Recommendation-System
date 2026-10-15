import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function Profile() {
  const { username, profile, logout } = useAuth();
  const navigate = useNavigate();

  function handleLogout() {
    logout();
    navigate("/login");
  }

  return (
    <div className="page">
      <div className="page-header">
        <span className="eyebrow">Account</span>
        <h1>User Profile: {username}</h1>
      </div>

      <div className="card" style={{ maxWidth: 520 }}>
        <h3>Active Health Assessment</h3>
        {profile ? (
          <div style={{ display: "flex", flexDirection: "column", gap: 10, fontSize: "0.92rem", marginTop: 12 }}>
            <div><strong>Gender:</strong> {profile.gender}</div>
            <div><strong>Age:</strong> {profile.age} years</div>
            <div>
              <strong>Height / Weight:</strong> {profile.height_cm} cm / {profile.weight_kg} kg
            </div>
            <div><strong>Activity Level:</strong> {profile.activity_level}</div>
            <div><strong>Goal:</strong> {profile.goal}</div>
            <div><strong>Food Preference:</strong> {profile.food_preference}</div>
            <div><strong>Region:</strong> {profile.region}</div>
            <div><strong>Medical Conditions:</strong> {profile.medical_conditions || "None declared"}</div>
            <div><strong>Allergies:</strong> {profile.allergies || "None declared"}</div>
          </div>
        ) : (
          <p style={{ color: "var(--ink-soft)" }}>No assessment recorded yet.</p>
        )}
      </div>

      <button className="btn btn-danger" onClick={handleLogout} style={{ marginTop: 20 }}>
        Logout
      </button>
    </div>
  );
}
