/**
 * Word count aligned with backend-style tokenization (unicode word chars).
 * @param {string} text
 */
export function countWords(text) {
  const re = /\b\w+\b/gu;
  const matches = (text || "").match(re);
  return matches ? matches.length : 0;
}

/**
 * @param {string} text
 * @returns {string[]}
 */
export function splitKeyPointsMultiline(text) {
  return (text || "")
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean);
}

/**
 * @param {string[]|null|undefined} points
 */
export function joinKeyPoints(points) {
  return (points || []).join("\n");
}

const HTML_ESCAPE = {
  "&": "&amp;",
  "<": "&lt;",
  ">": "&gt;",
  '"': "&quot;",
  "'": "&#39;",
};

/**
 * Escape text for safe HTML text-node insertion.
 * @param {string} text
 */
export function escapeHtml(text) {
  return String(text ?? "").replace(/[&<>"']/g, (ch) => HTML_ESCAPE[ch] || ch);
}
