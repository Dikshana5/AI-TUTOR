export function normalizeLanguage(label) {
  const upper = (label || "").toUpperCase();
  if (upper.includes("PYTHON")) return "python";
  if (upper.includes("JAVA")) return "java";
  if (upper.includes("C++")) return "cpp";
  return "python";
}
