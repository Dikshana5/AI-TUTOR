import "../styles/home.css";
import "../styles/projects.css";
import { useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import backgroundImage from "../assets/background.png";
import { fetchCategories, fetchProblems } from "../api";

const normalizeLang = (lang) => {
  const l = (lang || "").toString().trim().toLowerCase();
  if (l === "cpp" || l === "c++") return "c++";
  return l;
};

export default function Projects() {
  const location = useLocation();
  // This line defines the variable that was "not defined"
  const [selectedLang, setSelectedLang] = useState(location?.state?.language || "PYTHON");
  const navigate = useNavigate();
 

  // Set by Learn.jsx when a language card is clicked.
  const selectedLangParam = location?.state?.language || "";

  // Step 2: topics
  const [topics, setTopics] = useState([]);
  const [topicsLoading, setTopicsLoading] = useState(false);
  const [topicsError, setTopicsError] = useState("");

  // Step 3: problems for selected topic
  const [selectedTopic, setSelectedTopic] = useState(null);
  const [problems, setProblems] = useState([]);
  const [problemsLoading, setProblemsLoading] = useState(false);
  const [problemsError, setProblemsError] = useState("");

  // Cache problems so we don’t re-fetch on topic switches within same language selection.
  const [allProblemsCache, setAllProblemsCache] = useState(null);

  const [error, setError] = useState("");

  useEffect(() => {
    // Fetch all problems on mount
    fetchProblems().then(data => {
      console.log("Fetched problems data:", data);
      setAllProblemsCache(data?.problems || data?.data || data || []);
    }).catch(err => console.error("Failed to fetch problems:", err));
  }, []);

  useEffect(() => {
    const lang = selectedLangParam;
    if (!lang) {
      // Try to recover the language from localStorage if state is lost on refresh
      const savedLang = localStorage.getItem("selected_language") || "PYTHON";
      setError(""); 
      // Trigger the fetch with the recovered language
      fetchCategories(savedLang).then(cats => setTopics(Array.isArray(cats) ? cats : cats?.topics || []));
      return;
    }

    setError("");
    setTopics([]);
    setTopicsError("");
    setSelectedTopic(null);
    setProblems([]);
    setProblemsError("");
    setAllProblemsCache(null);

    const run = async () => {
      setTopicsLoading(true);
      try {
        const cats = await fetchCategories(lang);
        // Backend returns a list of topic strings.
        setTopics(Array.isArray(cats) ? cats : cats?.topics || []);
      } catch (e) {
        setTopicsError(e?.message || "Could not load topics for this language.");
      } finally {
        setTopicsLoading(false);
      }
    };

    run();
  }, [selectedLang]); 

    const handleSelectTopic = async (topic) => {
    setSelectedTopic(topic);
    setProblemsError("");

    // 1. Correctly prioritize the current language state
    const currentLang = selectedLangParam || selectedLang || "PYTHON";

    // 2. Ensure cache is populated before filtering
    let cache = allProblemsCache;
    if (!cache || cache.length === 0) {
      setProblemsLoading(true);
      try {
        const data = await fetchProblems();
        // Extract array from possible wrappers like data.problems or data.data
        cache = data?.problems || data?.data || data || [];
        setAllProblemsCache(cache);
      } catch (e) {
        setProblemsError(e?.message || "Could not load problems.");
        setProblemsLoading(false);
        return;
      }
      setProblemsLoading(false);
    }

    // 3. FIXED FILTER LOGIC: Robust normalization for all languages
    const filtered = (cache || []).filter((p) => {
      // Normalize backend data
      const pLang = normalizeLang(p?.language);
      const pTopic = (p?.topic || "").toString().trim().toLowerCase();
      
      // Normalize frontend state/selection
      const selectedLangNorm = normalizeLang(currentLang);
      const selectedTopicNorm = (topic || "").toString().trim().toLowerCase();
    
      // Strict match after normalization
      return pLang === selectedLangNorm && pTopic === selectedTopicNorm;
    });

    console.log(`Filtered ${filtered.length} projects for ${currentLang} -> ${topic}`);
    setProblems(filtered);
  };



  return (
    <div className="home" style={{ backgroundImage: `url(${backgroundImage})` }}>
      <div className="overlay"></div>

      <h1 className="logo">COUTOR</h1>
      <p className="projects-tagline">{'{ FROM CODE TO KNOWLEDGE };'}</p>
      <h2 className="projects-heading">PROJECT-BASED LEARNING STARTS HERE!?!!</h2>
      <div className="fun-zone-selector" style={{ display: 'flex', gap: '15px', justifyContent: 'center', marginBottom: '40px' }}>
        {["PYTHON", "JAVA", "C++"].map((lang) => (
          <button
            key={lang}
            onClick={() => setSelectedLang(lang)}
            className="lang-toggle-btn"
            style={{
              padding: '12px 24px',
              background: selectedLang === lang ? '#41c8ff' : '#222',
              color: 'white',
              border: '1px solid #444',
              borderRadius: '30px',
              cursor: 'pointer',
              fontFamily: 'Koulen, sans-serif'
            }}
          >
            {lang} PROJECTS
          </button>
        ))}
      </div>

      
      {error && <p style={{ color: "salmon", textAlign: "center" }}>{error}</p>}

      <div className="projects-container">
        {/* Step 2 */}
        <section style={{ marginBottom: "32px" }}>
          <h2 style={{ color: "white", marginBottom: "12px" }}>Step 2: Choose a topic</h2>

          {topicsLoading && (
            <p style={{ color: "white", opacity: 0.8 }}>Loading topics...</p>
          )}
          {topicsError && (
            <p style={{ color: "salmon", textAlign: "center" }}>{topicsError}</p>
          )}

          {!topicsLoading && !topicsError && topics.length === 0 && (
            <p style={{ color: "white", opacity: 0.8 }}>No topics found.</p>
          )}

          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
              gap: "12px",
              marginTop: "12px",
            }}
          >
            {topics.map((t) => (
              <div
                key={t}
                className="project-card"
                onClick={() => handleSelectTopic(t)}
                style={{
                  cursor: "pointer",
                  border: selectedTopic === t ? "2px solid #41c8ff" : undefined,
                  background: selectedTopic === t ? "rgba(65, 200, 255, 0.08)" : undefined,
                }}
              >
                <h3 style={{ margin: 0 }}>{t}</h3>
                <p style={{ marginTop: "8px", opacity: 0.85 }}>Select to view problems</p>
              </div>
            ))}
          </div>
        </section>

        {/* Step 3 */}
        <section>
          <h2 style={{ color: "white", marginBottom: "12px" }}>
            Step 3: Problems {selectedTopic ? `- ${selectedTopic}` : ""}
          </h2>

          {!selectedTopic && (
            <p style={{ color: "white", opacity: 0.8 }}>
              Pick a topic above to load specific problems.
            </p>
          )}

          {problemsError && (
            <p style={{ color: "salmon", textAlign: "center" }}>{problemsError}</p>
          )}

          {problemsLoading && (
            <p style={{ color: "white", opacity: 0.8 }}>Loading problems...</p>
          )}

          {selectedTopic && !problemsLoading && problems.length === 0 && !problemsError && (
            <p style={{ color: "white", opacity: 0.8 }}>No problems found for this topic.</p>
          )}

          <div style={{ display: "grid", gap: "12px" }}>
            {problems.map((problem) => (
              <div
                key={problem.id}
                className="project-card"
                onClick={() =>
                  navigate("/run", {
                    state: {
                      language: problem.language,
                      title: problem.title,
                      description: problem.description,
                    },
                  })
                }
                style={{ cursor: "pointer" }}
              >
                <h3>{problem.title}</h3>
                <p>{problem.description}</p>
              </div>
            ))}
          </div>
        </section>
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


