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
  if (!userId) {
    throw new Error("User not authenticated");
  }

  const payload = {
    user_id: userId,
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
export async function fetchNextStep(analysis, language, problemId) {
  const res = await fetch(`${API_BASE_URL}/next-step`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      ...analysis,
      language: normalizeLanguage(language),
      problem_id: problemId,
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

export async function fetchCategories(language) {
  const res = await fetch(`${API_BASE_URL}/categories/${encodeURIComponent(language)}`);
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(text || `Failed to load categories for ${language}`);
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

export async function fetchStats(userId) {
  if (!userId) {
    throw new Error("User not authenticated");
  }

  const res = await fetch(`${API_BASE_URL}/user/stats/${encodeURIComponent(userId)}`);
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    console.error("fetchStats backend error:", text || res.status);
    return { heatmap: [], learning_speed: [], lessons_completed: [] };
  }

  const data = await res.json().catch(() => null);
  if (!data || typeof data !== "object") {
    return { heatmap: [], learning_speed: [], lessons_completed: [] };
  }

  const cleanData = data?.stats || data?.data || data;
  if (!cleanData || typeof cleanData !== "object") {
    return { heatmap: [], learning_speed: [], lessons_completed: [] };
  }

  return {
    heatmap: Array.isArray(cleanData.heatmap) ? cleanData.heatmap : [],
    learning_speed: Array.isArray(cleanData.learning_speed) ? cleanData.learning_speed : [],
    lessons_completed: Array.isArray(cleanData.lessons_completed)
      ? cleanData.lessons_completed
      : typeof cleanData.lessons_completed === "number"
      ? cleanData.lessons_completed
      : [],
  };
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
  const userId = localStorage.getItem("user_id");
  if (!userId) {
    throw new Error("User not authenticated");
  }
  const payload = typeof messagesOrText === "string" ? { message: messagesOrText, user_id: userId } : { messages: messagesOrText, user_id: userId };
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

export async function fetchCurriculumProblems() {
  const res = await fetch(`${API_BASE_URL}/learning/problems`);
  return res.json();
}

export async function fetchCurriculumCategories(language) {
  const res = await fetch(`${API_BASE_URL}/learning/categories/${encodeURIComponent(language)}`);
  return res.json();
}