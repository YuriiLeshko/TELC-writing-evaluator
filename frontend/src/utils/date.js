/**
 * @param {unknown} value ISO string or Date-like
 */
function parseBackendDate(value) {
  if (value == null || value === "") return null;
  if (value instanceof Date) return Number.isNaN(value.getTime()) ? null : value;
  const raw = String(value).trim();
  if (!raw) return null;
  const hasTimezone = /(?:Z|[+-]\d{2}:\d{2})$/i.test(raw);
  const normalized = hasTimezone ? raw : `${raw}Z`;
  const parsed = new Date(normalized);
  return Number.isNaN(parsed.getTime()) ? null : parsed;
}

export function formatDateTime(value) {
  const d = parseBackendDate(value);
  if (!d) return "—";
  return d.toLocaleString(undefined, {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

/**
 * @param {number} totalSeconds
 */
export function formatElapsed(totalSeconds) {
  const s = Math.max(0, Math.floor(Number(totalSeconds) || 0));
  const h = Math.floor(s / 3600);
  const m = Math.floor((s % 3600) / 60);
  const sec = s % 60;
  if (h > 0) {
    return `${h}:${String(m).padStart(2, "0")}:${String(sec).padStart(2, "0")}`;
  }
  return `${m}:${String(sec).padStart(2, "0")}`;
}

/**
 * @param {unknown} startedAt
 * @returns {number} elapsed seconds from startedAt to now (UTC-safe parse)
 */
export function getElapsedSeconds(startedAt) {
  const start = parseBackendDate(startedAt);
  if (!start) return 0;
  const diff = (Date.now() - start.getTime()) / 1000;
  return Math.max(0, Math.floor(diff));
}
