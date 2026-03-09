// Simple API client for the AI Tutor backend

export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

// ✅ SIMPLIFIED + CLEAN
export function normalizeLanguage(label) {
  const upper = (label || "").toUpperCase();
  if (upper.includes("PYTHON")) return "python";
  if (upper.includes("JAVA")) return "java";
  if (upper.includes("C++")) return "cpp";
  return "python";
}

export async function analyzeCode({ code, language, userId, sessionId }) {
  const payload = {
    user_id: userId || "web_user",
    session_id: sessionId || `session_${Date.now()}`,
    content: code,
    content_type: "code",
    language: normalizeLanguage(language),
  };

  const res = await fetch(`${API_BASE_URL}/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `Analyze failed with status ${res.status}`);
  }

  return res.json();
}

// ✅ FORCE LANGUAGE INTO NEXT-STEP
export async function fetchNextStep(analysis, language) {
  const res = await fetch(`${API_BASE_URL}/next-step`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      ...analysis,
      language: normalizeLanguage(language),
    }),
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `Next step failed with status ${res.status}`);
  }

  return res.json();
}

export async function fetchProblems() {
  const res = await fetch(`${API_BASE_URL}/problems`);
  if (!res.ok) {
    throw new Error("Failed to load problems from backend");
  }
  return res.json();
}

export async function fetchHealth() {
  const res = await fetch(`${API_BASE_URL}/health`);
  if (!res.ok) {
    throw new Error("Backend health check failed");
  }
  return res.json();
}

// --- NEW AUTH FUNCTIONS ---

export async function signup(userData) {
  const res = await fetch(`${API_BASE_URL}/signup`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(userData),
  });

  if (!res.ok) {
    const errorData = await res.json();
    throw new Error(errorData.detail || "Signup failed");
  }

  return res.json();
}

export async function login(credentials) {
  const res = await fetch(`${API_BASE_URL}/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(credentials),
  });

  if (!res.ok) {
    const errorData = await res.json();
    throw new Error(errorData.detail || "Login failed");
  }

  return res.json();
}

export async function sendChatMessage(messagesOrText) {
  const payload = typeof messagesOrText === "string" ? { message: messagesOrText } : { messages: messagesOrText };
  const res = await fetch(`${API_BASE_URL}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `Chat failed with status ${res.status}`);
  }

  return res.json();
}
