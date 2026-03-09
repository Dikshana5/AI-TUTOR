import { useState, useEffect, useRef } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import backgroundImage from "../assets/background.png";
import { analyzeCode, fetchNextStep, sendChatMessage } from "../api";
import { normalizeLanguage } from "../normalizelanguage";
import "../styles/run.css";

const PROBLEM_TEMPLATES = {
  "C++": [
    `// Problem 1: Print numbers from 1 to N\n\n#include <iostream>\nusing namespace std;\n\nint main() {\n int n;\n cin >> n;\n // your code here\n return 0;\n}`,
    `// Problem 2: Check if a number is prime\n\n#include <iostream>\nusing namespace std;\n\nint main() {\n int n;\n cin >> n;\n // your code here\n return 0;\n}`,
  ],
  "JAVA": [
    `// Problem 1: Reverse a string\n\npublic class Main {\n public static void main(String[] args) {\n  // your code here\n }\n}`,
    `// Problem 2: Find largest element in array\n\npublic class Main {\n public static void main(String[] args) {\n  // your code here\n }\n}`,
  ],
  "PYTHON": [
    `# Problem 1: Count vowels in a string\n\ns = input()\n# your code here\n`,
    `# Problem 2: Find factorial of a number\n\nn = int(input())\n# your code here\n`,
  ],
};

export default function Run() {
  const navigate = useNavigate();
  const location = useLocation();

  const isProject = Boolean(location.state?.title);

  const language =
    location.state?.language &&
    PROBLEM_TEMPLATES[location.state.language]
      ? location.state.language
      : "PYTHON";

  const [problemIndex, setProblemIndex] = useState(0);
  const [code, setCode] = useState("");
  const [loading, setLoading] = useState(false);
  const [analysis, setAnalysis] = useState(null);
  const [output, setOutput] = useState("");
  const [error, setError] = useState("");
  const [chatOpen, setChatOpen] = useState(false);
  const [chatStyle, setChatStyle] = useState({ left: 20, top: 120, width: 260, height: 250 });
  const [chatMessages, setChatMessages] = useState([]);
  const [chatInput, setChatInput] = useState("");

  useEffect(() => {
    if (isProject) {
      // start with empty code for projects
      setCode("// write your code here\n");
    } else {
      setCode(PROBLEM_TEMPLATES[language][problemIndex]);
    }
    setAnalysis(null);
    setOutput("");
    setError("");
  }, [language, problemIndex, isProject]);

  async function handleAnalyze() {
    if (!code.trim()) {
      setError("Please write a solution before analyzing.");
      return;
    }

    setLoading(true);
    setError("");
    setOutput("");

    try {
      const result = await analyzeCode({
        code,
        language: normalizeLanguage(language),
        userId: "web_user",
        sessionId: `session_${Date.now()}`,
      });

      setAnalysis(result);
      setOutput("Analysis complete. Check feedback below.");
    } catch (e) {
      setError("AI analysis failed. Try again.");
      setOutput("");
    } finally {
      setLoading(false);
    }
  }

  function toggleChat() {
    const analysisSidebar = document.querySelector(".analysis-sidebar");
    const margin = 16;
    const extraWidth = 20; // 0.5cm additional width
    let desiredHeight, topPosition, rightPos, panelWidth;

    if (analysisSidebar) {
      // Project mode: align chat perfectly with analysis sidebar
      const rect = analysisSidebar.getBoundingClientRect();
      // Match analysis sidebar dimensions exactly, plus extra width
      desiredHeight = rect.height;
      topPosition = rect.top;
      rightPos = window.innerWidth - rect.right + margin - extraWidth;
      panelWidth = rect.width + extraWidth;
    } else {
      // Lesson mode: position chat on the right side
      desiredHeight = 250;
      topPosition = 120;
      rightPos = 20;
      panelWidth = 260;
    }

    setChatStyle({
      right: rightPos,
      top: topPosition,
      width: panelWidth,
      height: desiredHeight,
    });
    setChatOpen((s) => !s);
  }

  useEffect(() => {
    function onResize() {
      if (!chatOpen) return;
      const analysisSidebar = document.querySelector(".analysis-sidebar");
// reduce panel width by 0.5cm (20px) instead of adding
    const extraWidth = -20; // subtract extra width
      const margin = 16;

      if (analysisSidebar) {
        const rect = analysisSidebar.getBoundingClientRect();
        setChatStyle({
          right: window.innerWidth - rect.right + margin - extraWidth,
          top: rect.top,
          width: rect.width + extraWidth,
          height: rect.height,
        });
      }
    }
    window.addEventListener("resize", onResize);
    return () => window.removeEventListener("resize", onResize);
  }, [chatOpen]);

  async function handleSendChat(e) {
    e && e.preventDefault();
    if (!chatInput.trim()) return;
    const userMsg = chatInput.trim();
    setChatMessages((m) => [...m, { role: "user", content: userMsg }]);
    setChatInput("");

    try {
      const res = await sendChatMessage(userMsg);
      const reply = res.reply || res.text || "";
      setChatMessages((m) => [...m, { role: "assistant", content: reply }]);
    } catch (err) {
      setChatMessages((m) => [...m, { role: "assistant", content: "(error) Could not get reply" }]);
    }
  }

  const messagesEndRef = useRef(null);
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [chatMessages]);

  return (
    <div
      className="run-container"
      style={{ backgroundImage: `url(${backgroundImage})` }}
    >
      <div className="overlay"></div>

      <button className="back-btn" onClick={() => navigate("/projects")}>
        {"<<"}
      </button>

      <div className="run-content">
        {/* LEFT SIDEBAR - LESSONS (lesson mode only) */}
        {!isProject && (
          <div className="left-sidebar">
            <h3>LESSONS</h3>
            <div className="lessons-list">
              {PROBLEM_TEMPLATES[language].map((_, idx) => (
                <button
                  key={idx}
                  className={`lesson-btn ${
                    problemIndex === idx ? "active" : ""
                  }`}
                  onClick={() => setProblemIndex(idx)}
                >
                  Problem {idx + 1}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* CENTER - CODE & OUTPUT */}
        <div className={`code-output-section ${isProject ? "project-layout" : ""}`}>
          {/* CODE EDITOR */}
          <div className="code-box">
            <div className="code-header">
              <h3>
              {isProject
                ? location.state?.title || "CODE"
                : `CODE — ${language}`}
            </h3>
            {!isProject && (
              <span className="problem-counter">
                {problemIndex + 1} / {PROBLEM_TEMPLATES[language].length}
              </span>
            )}
            </div>
            <textarea
              className="code-editor"
              value={code}
              onChange={(e) => setCode(e.target.value)}
              placeholder="Write your code here..."
            />
            <div className="code-footer">
              <button
                className="analyze-btn"
                onClick={handleAnalyze}
                disabled={loading}
              >
                {loading ? "Analyzing..." : "Analyse with Syntheia"}
              </button>
            </div>
          </div>

          {/* OUTPUT SECTION */}
          <div className="output-box">
            <div className="output-header">
              <h3>OUTPUT</h3>
            </div>
            <div className="output-content">
              {error && (
                <p style={{ color: "#ff6b6b" }}>❌ {error}</p>
              )}
              {output && <p style={{ color: "#4CAF50" }}>{output}</p>}
              {!error && !output && (
                <p style={{ opacity: 0.5 }}>Output appears here...</p>
              )}
            </div>
          </div>
        </div>

        {/* RIGHT SIDEBAR - ANALYSIS (both modes) */}
        <div className="analysis-sidebar">
          <h3>ANALYSIS</h3>
          <div className="analysis-content">
            {analysis ? (
              <>
                <p>
                  <strong>Confidence:</strong>{" "}
                  {Math.round((analysis.confidence || 0) * 100)}%
                </p>
                {analysis.diagnosis?.map((d, idx) => (
                  <div key={idx} style={{ marginTop: "8px" }}>
                    <p>{d.message}</p>
                    {d.fix && (
                      <p style={{ color: "#9be7ff", fontSize: "12px" }}>
                        ✓ {d.fix}
                      </p>
                    )}
                  </div>
                ))}
              </>
            ) : (
              <p style={{ opacity: 0.6 }}>Run analysis to see feedback</p>
            )}
          </div>
        </div>
      </div>

      {/* CHAT BUBBLE ICON - BOTTOM LEFT */}
      <div className="chat-bubble" onClick={toggleChat} role="button" tabIndex={0}>
        💬
      </div>

      {chatOpen && (
        <div
          className="chat-panel"
          style={{ right: chatStyle.right, top: chatStyle.top, width: chatStyle.width, height: chatStyle.height }}
        >
          <div className="chat-panel-header">
            <strong>Syntheia - Your Coding Tutor</strong>
            <button className="chat-close" onClick={() => setChatOpen(false)}>#</button>
          </div>
          <div className="chat-panel-body">
            <div className="chat-messages">
              {chatMessages.length === 0 && (
                <p style={{ opacity: 0.85 }}>Ask the tutor a question or get hints related to the lessons.</p>
              )}
              {chatMessages.map((m, i) => (
                <div key={i} className={`chat-msg ${m.role}`}>
                  <span className="msg-role">{m.role === "user" ? "You" : "Tutor"}</span>
                  <div className="msg-content">{m.content}</div>
                </div>
              ))}
              <div ref={messagesEndRef} />
            </div>

            <form className="chat-input-form" onSubmit={handleSendChat}>
              <input
                className="chat-input"
                value={chatInput}
                onChange={(e) => setChatInput(e.target.value)}
                placeholder="Ask Syntheia"
              />
              <button className="chat-send" type="submit">Send</button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}