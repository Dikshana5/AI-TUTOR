import { useState, useEffect, useMemo } from "react";

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  AreaChart,
  Area,
  CartesianGrid,
  ResponsiveContainer,
} from "recharts";
import backgroundImage from "../assets/background.png";
import { fetchStats } from "../api";
import "../styles/progress.css";



const Progress = () => {
  const [stats, setStats] = useState({ 
    heatmap: [], 
    learning_speed: [], 
    lessons_completed: [] 
  });
  const [loading, setLoading] = useState(true);

 useEffect(() => {
  // 1. Get the actual user ID from login or test setup
  const userId = localStorage.getItem("user_id");
  console.log("Progress fetch using user_id:", userId);
  if (!userId) {
    console.warn("No user_id found in localStorage, skipping stats fetch.");
    setLoading(false);
    return;
  }

  // 2. Start loading
  setLoading(true);

  // 3. Fetch from your FastAPI backend
  fetchStats(userId)
    .then(data => {
      console.log("Progress 200 response:", data);
      const cleanData = data?.stats || data?.data || data;
      console.log("Resolved stats payload:", cleanData);

      const isValidObject = cleanData && typeof cleanData === "object";
      const hasRequiredKeys = isValidObject && ["heatmap", "learning_speed", "lessons_completed"].every((key) => key in cleanData);

      if (!isValidObject || !hasRequiredKeys) {
        console.warn("Malformed stats response, using fallback stats.");
        setStats({ heatmap: [], learning_speed: [], lessons_completed: [] });
        return;
      }

      setStats({
        heatmap: Array.isArray(cleanData.heatmap) ? cleanData.heatmap : [],
        learning_speed: Array.isArray(cleanData.learning_speed) ? cleanData.learning_speed : [],
        lessons_completed: Array.isArray(cleanData.lessons_completed)
          ? cleanData.lessons_completed
          : typeof cleanData.lessons_completed === "number"
          ? cleanData.lessons_completed
          : [],
      });
    })
    .catch(err => {
      console.error("Stats error:", err);
      setStats({ heatmap: [], learning_speed: [], lessons_completed: [] });
    })
    .finally(() => {
      // 5. CRITICAL: This removes the "Loading progress..." screen
      setLoading(false);
    });
}, []);



  // ✅ FIXED: Removed stray [] and used fallbacks
  const dailyContributions = stats?.heatmap || [];
  const learningSpeed = stats?.learning_speed || [];
  const lessonsCompleted = stats?.lessons_completed || [];
  const lessonItems = Array.isArray(stats?.lessons_completed)
    ? stats.lessons_completed
    : typeof stats?.lessons_completed === "number"
    ? Array.from({ length: stats.lessons_completed })
    : [];

  const [selectedYear, setSelectedYear] = useState(2026);
  const colors = ["#563263", "#b23e53", "#f14c55", "#fe6345", "#fc7b49"];

  if (!stats) return <p>Loading...</p>;

  if (loading) {
    return (
      <div className="progress-container" style={{ backgroundImage: `url(${backgroundImage})` }}>
        <div className="progress-overlay"></div>
        <div className="progress-content" style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
          <p style={{ color: 'white', fontSize: '24px' }}>Loading progress...</p>
        </div>
      </div>
    );
  }

  return (
    <>
      <div className="progress-container" style={{ backgroundImage: `url(${backgroundImage})` }}>
        <div className="progress-overlay"></div>
        <div className="progress-content">
        
        {/* Daily Contributions */}
        <div className="progress-section daily-contributions">
          <h2>daily contributions</h2>
          <div className="contrib-header">
            <span className="contrib-summary">7 contributions in the last year</span>
            <div className="year-selector">
              {[2026, 2025, 2024].map((year) => (
                <button
                  key={year}
                  className={`year-btn ${selectedYear === year ? "active" : ""}`}
                  onClick={() => setSelectedYear(year)}
                >
                  {year}
                </button>
              ))}
            </div>
          </div>
          <div className="contrib-grid">
            <div className="contrib-rows">
              {(stats?.heatmap || []).map((entry, idx) => (
                <div key={idx} className="contrib-row">
                  <span className="day-label">{entry?.month} {entry?.day}</span>
                  <div
                    className="contrib-cell"
                    style={{ backgroundColor: colors[Math.min(entry?.count || 0, 4)] }}
                  ></div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Charts Section */}
        <div className="charts-wrapper">
          <div className="progress-section learning-speed">
            <h2>learning speed</h2>
            <ResponsiveContainer width="100%" height={250}>
              <AreaChart data={learningSpeed}>
                <defs>
                  <linearGradient id="colorSpeed" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#563263" stopOpacity={0.8} />
                    <stop offset="95%" stopColor="#563263" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#444" />
                <XAxis dataKey="day" stroke="#999" />
                <YAxis stroke="#999" />
                <Tooltip />
                <Area type="monotone" dataKey="speed" stroke="#563263" fill="url(#colorSpeed)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>

          <div className="progress-section lessons-completed">
            <h2>lessons completed</h2>
            <div className="lessons-chart">
              <div className="lessons-header">
                {["S", "M", "T", "W", "T", "F", "S"].map((day, i) => (
                  <span key={i} className="lesson-day">{day}</span>
                ))}
              </div>
              {lessonItems.map((lesson, idx) => (
                <div key={lesson?.id || idx} className="lesson-row">
                  <span className="lesson-name">{lesson?.project || `Lesson ${idx + 1}`}</span>
                  <div className="lesson-bar" style={{ backgroundColor: lesson?.color || "#563263", width: `${lesson?.progress || 0}%` }}>
                    <span className="lesson-label">{lesson?.label || "Project Progress"}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

      </div>
    </div>
  </>
  );
};

export default Progress;
