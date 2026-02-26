import { useState, useEffect } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import backgroundImage from "../assets/background.png";
import { analyzeCode, fetchNextStep } from "../api";
import { normalizeLanguage } from "../normalizelanguage";

const PROBLEM_TEMPLATES = {
  "C++": [
    "// Problem 1: Print numbers from 1 to N\n\n#include <iostream>\nusing namespace std;\n\nint main() {\n    int n;\n    cin >> n;\n\n    // your code here\n\n    return 0;\n}",
    "// Problem 2: Check if a number is prime\n\n#include <iostream>\nusing namespace std;\n\nint main() {\n    int n;\n    cin >> n;\n\n    // your code here\n\n    return 0;\n}",
  ],
  "JAVA": [
    "// Problem 1: Reverse a string\n\npublic class Main {\n    public static void main(String[] args) {\n        // your code here\n    }\n}",
    "// Problem 2: Find largest element in array\n\npublic class Main {\n    public static void main(String[] args) {\n        // your code here\n    }\n}",
  ],
  "PYTHON": [
    "# Problem 1: Count vowels in a string\n\ns = input()\n# your code here\n",
    "# Problem 2: Find factorial of a number\n\nn = int(input())\n# your code here\n",
  ],
};

export default function Run() {
  const navigate = useNavigate();
  const location = useLocation();

  const language =
    location.state?.language && PROBLEM_TEMPLATES[location.state.language]
      ? location.state.language
      : "PYTHON";

  const [problemIndex, setProblemIndex] = useState(0);
  const [code, setCode] = useState("");
  const [loading, setLoading] = useState(false);
  const [analysis, setAnalysis] = useState(null);
  const [nextStep, setNextStep] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    setCode(PROBLEM_TEMPLATES[language][problemIndex]);
    setAnalysis(null);
    setNextStep(null);
    setError("");
  }, [language, problemIndex]);

  async function handleAnalyze() {
    if (!code.trim()) {
      setError("Please write a solution before analyzing.");
      return;
    }

    setLoading(true);
    setError("");

    try {
      const result = await analyzeCode({
        code,
        language: normalizeLanguage(language),
        userId: "web_user",
        sessionId: `session_${Date.now()}`,
      });

      setAnalysis(result);

      const step = await fetchNextStep(result, normalizeLanguage(language));
      setNextStep(step);
    } catch (e) {
      setError("AI analysis failed. Try again.");
    } finally {
      setLoading(false);
    }
  }

  async function handleNextProblem() {
  if (!analysis) {
    setError("Analyze your code first.");
    return;
  }

  setLoading(true);
  setError("");

  try {
    const nextProblem = await fetchNextStep(analysis);

    // Load AI-suggested problem
    setCode(nextProblem.template || nextProblem.description || "");
    setAnalysis(null);
  } catch (e) {
    setError("Failed to load next challenge.");
  } finally {
    setLoading(false);
  }
}

  return (
    <div
      style={{
        backgroundImage: `url(${backgroundImage})`,
        backgroundSize: "cover",
        minHeight: "100vh",
        padding: "40px",
        color: "white",
        fontFamily: "Koulen, sans-serif",
      }}
    >
      <button onClick={() => navigate("/projects")}>← BACK</button>

      <h1>RUN — {language}</h1>
      <h3>
        Problem {problemIndex + 1} of {PROBLEM_TEMPLATES[language].length}
      </h3>

      <textarea
        value={code}
        onChange={(e) => setCode(e.target.value)}
        style={{
          width: "100%",
          minHeight: "320px",
          background: "rgba(0,0,0,0.8)",
          color: "white",
          fontFamily: "monospace",
          padding: "12px",
          borderRadius: "8px",
          border: "1px solid #555",
        }}
      />

      <button onClick={handleAnalyze} disabled={loading} style={{ marginTop: 12 }}>
        {loading ? "Analyzing..." : "Analyze with AI"}
      </button>

      {error && <p style={{ color: "salmon" }}>{error}</p>}

      {analysis && (
  <div
    style={{
      marginTop: "20px",
      background: "rgba(0,0,0,0.7)",
      padding: "16px",
      borderRadius: "10px",
      border: "1px solid #555",
    }}
  >
    <p>
      <strong>Confidence:</strong>{" "}
      {Math.round((analysis.confidence || 0) * 100)}%
    </p>

    <p>
      <strong>Detected Issues:</strong>{" "}
      {analysis.error_types?.length
        ? analysis.error_types.join(", ")
        : "None"}
    </p>

    <hr style={{ margin: "12px 0", opacity: 0.3 }} />

    <h3 style={{ marginBottom: "8px" }}>AI Feedback</h3>

    {analysis.diagnosis?.map((d, idx) => (
      <div key={idx} style={{ marginBottom: "12px" }}>
        <p>{d.message}</p>

        {d.fix && (
          <p style={{ color: "#9be7ff", marginTop: "6px" }}>
            <strong>Suggested Fix:</strong> {d.fix}
          </p>
        )}
      </div>
    ))}
  </div>
)}

      {nextStep && (
        <div style={{ marginTop: 20, background: "#000", padding: 16, borderRadius: 8 }}>
          <h3>{nextStep.title}</h3>
          <p>{nextStep.description}</p>
          {nextStep.hint && <p>💡 {nextStep.hint}</p>}
        </div>
      )}

      <button
        onClick={handleNextProblem}
        style={{
          marginTop: 24,
          padding: "10px 22px",
          borderRadius: 20,
          border: "none",
          background: "black",
          color: "white",
          cursor: "pointer",
        }}
      >
        Start Next Challenge →
      </button>
    </div>
  );
}
