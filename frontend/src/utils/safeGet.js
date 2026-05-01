/**
 * @param {unknown} object
 * @param {string} path dot-separated keys
 * @param {unknown} defaultValue
 */
export function safeGet(object, path, defaultValue = undefined) {
  if (object == null || typeof object !== "object") {
    return defaultValue;
  }
  const parts = path.split(".");
  let cur = object;
  for (const p of parts) {
    if (cur == null || typeof cur !== "object" || !(p in cur)) {
      return defaultValue;
    }
    cur = cur[p];
  }
  return cur === undefined ? defaultValue : cur;
}
