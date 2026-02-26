import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import "../styles/home.css";
import { fetchHealth } from "../api";

export default function Progress() {
  const navigate = useNavigate();
  const [health, setHealth] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    fetchHealth()
      .then((data) => {
        if (!cancelled) setHealth(data);
      })
      .catch(() => {
        if (!cancelled)
          setError("Backend is offline. Start the API server to track progress.");
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div className="home">
      <div className="overlay"></div>
      <div className="top-controls">
        <span></span>
        <span></span>
        <span></span>
        <span></span>
      </div>
      <h1 className="logo">COUTOR</h1>

      <button
        onClick={() => navigate("/")}
        style={{
          position: "absolute",
          top: "20px",
          left: "20px",
          padding: "8px 16px",
          background: "#d9d9d9",
          border: "1px solid #999",
          borderRadius: "20px",
          cursor: "pointer",
          fontSize: "16px",
          fontFamily: "Koulen, sans-serif",
          zIndex: 100,
        }}
      >
        ← BACK
      </button>

      <h2 style={{ color: "white", marginTop: "50px" }}>PROGRESS</h2>

      <div style={{ color: "white", marginTop: "20px" }}>
        {health && (
          <>
            <p>Status: {health.status}</p>
            <p>Engine: {health.engine}</p>
          </>
        )}
        {error && <p style={{ color: "salmon" }}>{error}</p>}
        {!health && !error && <p>Checking backend status...</p>}
      </div>

    </div>
  );
}