import "../styles/home.css";
import "../styles/projects.css";
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import backgroundImage from "../assets/background.png";
import { fetchProblems } from "../api";

const groupByLanguage = (projects = []) => {
  return projects.reduce((acc, p) => {
    const lang = p.language || "Other";
    if (!acc[lang]) acc[lang] = [];
    acc[lang].push(p);
    return acc;
  }, {});
};

export default function Projects() {
  const navigate = useNavigate();
  const [problems, setProblems] = useState([]);
  const [error, setError] = useState("");

  useEffect(() => {
    fetchProblems()
      .then((data) => setProblems(data || []))
      .catch(() =>
        setError("Could not load projects from the tutor backend.")
      );
  }, []);

  const groupedProjects = groupByLanguage(problems);

  return (
    <div className="home" style={{ backgroundImage: `url(${backgroundImage})` }}>
      <div className="overlay"></div>

      <h1 className="logo">COUTOR</h1>
      <p className="projects-tagline">{'{ FROM CODE TO KNOWLEDGE };'}</p>
      <h2 className="projects-heading">
        PROJECT-BASED LEARNING STARTS HERE!?!!
      </h2>

      {error && (
        <p style={{ color: "salmon", textAlign: "center" }}>{error}</p>
      )}

      <div className="projects-container">
        {Object.keys(groupedProjects).map((language) => (
          <div key={language} style={{ marginBottom: "32px" }}>
            <h2 style={{ color: "white", marginBottom: "12px" }}>
              {language}
            </h2>

            <div style={{ display: "grid", gap: "12px" }}>
              {groupedProjects[language].map((p, idx) => (
                <div
                  key={p.id || p.title || idx}
                  className="project-card"
                  onClick={() =>
                    navigate("/run", {
                      state: {
                        language: p.language,
                        title: p.title,
                        description: p.description,
                      },
                    })
                  }
                  style={{ cursor: "pointer" }}
                >
                  <h3>{p.title}</h3>
                  <p>{p.description}</p>
                </div>
              ))}
            </div>
          </div>
        ))}

        {problems.length === 0 && !error && (
          <p style={{ color: "white", opacity: 0.8 }}>
            Loading projects from the AI tutor...
          </p>
        )}
      </div>

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
        {"<<"}
      </button>
    </div>
  );
}
