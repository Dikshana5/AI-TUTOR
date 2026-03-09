import { useState, useMemo } from "react";
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
import "../styles/progress.css";

const Progress = () => {
  const [selectedYear, setSelectedYear] = useState(2026);

  const colors = ["#563263", "#b23e53", "#f14c55", "#fe6345", "#fc7b49"];

  /* Daily Contributions Heatmap Data */
  const dailyContributions = useMemo(() => {
    const data = [];
    const months = ["Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec", "Jan", "Feb"];
    const days = ["Mon", "Wed", "Fri"];
    
    // Generate random contribution counts
    months.forEach((month, idx) => {
      days.forEach((day) => {
        data.push({
          month,
          day,
          count: Math.floor(Math.random() * 5),
        });
      });
    });
    return data;
  }, []);

  const learningSpeed = [
    { day: "Mon", speed: 2.5 },
    { day: "Tue", speed: 3.8 },
    { day: "Wed", speed: 3.1 },
    { day: "Thu", speed: 6.2 },
    { day: "Fri", speed: 5.8 },
  ];

  const lessonsCompleted = [
    { project: "Problem 1", progress: 100, color: "#563263" },
    { project: "Problem 2", progress: 85, color: "#b23e53" },
    { project: "Problem 3", progress: 70, color: "#f14c55" },
    { project: "Problem 4", progress: 65, color: "#fe6345" },
    { project: "Problem 5", progress: 55, color: "#fc7b49" },
    { project: "Problem 6", progress: 90, color: "#563263" },
    { project: "Problem 7", progress: 75, color: "#b23e53" },
    { project: "Problem 8", progress: 80, color: "#f14c55" },
    { project: "Problem 9", progress: 60, color: "#fe6345" },
    { project: "Problem 10", progress: 95, color: "#fc7b49" },
  ];

  return (
    <div
      className="progress-container"
      style={{ backgroundImage: `url(${backgroundImage})` }}
    >
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
            <div className="contrib-header-grid">
              {["Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec", "Jan", "Feb"].map((m) => (
                <div key={m} className="month-label">{m}</div>
              ))}
            </div>
            <div className="contrib-rows">
              {["Mon", "Wed", "Fri"].map((day) => (
                <div key={day} className="contrib-row">
                  <span className="day-label">{day}</span>
                  {["Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec", "Jan", "Feb"].map((month, idx) => (
                    <div
                      key={`${day}-${month}`}
                      className="contrib-cell"
                      style={{
                        backgroundColor: colors[Math.floor(Math.random() * 5)],
                      }}
                    ></div>
                  ))}
                </div>
              ))}
            </div>
          </div>

          <div className="contrib-legend">
            <span>Learn how we count contributions</span>
            <div className="legend-scale">
              <span>Less</span>
              {[0, 1, 2, 3, 4].map((i) => (
                <div key={i} className="legend-cell" style={{ backgroundColor: colors[i] }}></div>
              ))}
              <span>More</span>
            </div>
          </div>
        </div>

        {/* Charts Section */}
        <div className="charts-wrapper">
          {/* Learning Speed */}
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
                <YAxis stroke="#999" domain={[0, 8]} />
                <Tooltip />
                <Area
                  type="monotone"
                  dataKey="speed"
                  stroke="#563263"
                  fillOpacity={1}
                  fill="url(#colorSpeed)"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>

          {/* Lessons Completed */}
          <div className="progress-section lessons-completed">
            <h2>lessons completed</h2>
            <div className="lessons-chart">
              <div className="lessons-header">
                {["S", "M", "T", "W", "T", "F", "S"].map((d, i) => (
                  <span key={i} className="lesson-day">{d}</span>
                ))}
              </div>
              {lessonsCompleted.map((lesson, idx) => (
                <div key={idx} className="lesson-row">
                  <span className="lesson-name">{lesson.project}</span>
                  <div className="lesson-bar" style={{ backgroundColor: lesson.color, width: `${lesson.progress}%` }}>
                    <span className="lesson-label">Lorem ipsum dolor sit amet</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Progress;
