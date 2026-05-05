const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

async function parseBody(response) {
  const text = await response.text();
  if (!text) return null;
  try {
    return JSON.parse(text);
  } catch {
    return text;
  }
}

function formatHttpError(status, body) {
  if (body && typeof body === "object" && "detail" in body) {
    const d = body.detail;
    if (typeof d === "string") return d;
    if (Array.isArray(d)) {
      return d
        .map((item) =>
          typeof item === "object" && item?.msg
            ? `${item.loc?.join(".") || "?"}: ${item.msg}`
            : String(item),
        )
        .join("; ");
    }
    return JSON.stringify(d);
  }
  if (typeof body === "string" && body.trim()) return body;
  return `HTTP ${status}`;
}

/**
 * @param {string} path path starting with /
 * @param {RequestInit} [options]
 */
export async function request(path, options = {}) {
  const url = `${API_BASE_URL}${path.startsWith("/") ? path : `/${path}`}`;
  const headers = new Headers(options.headers);
  if (options.body != null && !(options.body instanceof FormData) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  let response;
  try {
    response = await fetch(url, { ...options, headers });
  } catch (e) {
    const msg = e instanceof Error ? e.message : String(e);
    throw new Error(`Netzwerkfehler: ${msg}`);
  }
  const body = await parseBody(response);
  if (!response.ok) {
    throw new Error(formatHttpError(response.status, body));
  }
  return body;
}

export function healthCheck() {
  return request("/health");
}

export function getCurrentUser() {
  return request("/users/me");
}

export function updateCurrentUser(data) {
  return request("/users/me", {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export function deleteCurrentUser() {
  return request("/users/me", { method: "DELETE" });
}

/**
 * TODO: Es gibt keinen dokumentierten GET-/users-Listenendpunkt in docs/api_contract.md
 * (nur GET /users/me). Für Benutzerlisten Admin-Endpunkte verwenden.
 */
export async function getUsers() {
  throw new Error(
    "getUsers(): Kein öffentlicher Endpunkt im API-Vertrag. Nutzen Sie getCurrentUser() oder adminGetUsers().",
  );
}

export function startTaskSession() {
  return request("/task-sessions/start", { method: "POST" });
}

export function getMyTaskSessions() {
  return request("/task-sessions/my");
}

export function getActiveTaskSessions() {
  return request("/task-sessions/active");
}

export function getTaskSession(sessionId) {
  return request(`/task-sessions/${sessionId}`);
}

export function updateTaskSessionSelection(sessionId, selectedTaskType) {
  return request(`/task-sessions/${sessionId}/selection`, {
    method: "PATCH",
    body: JSON.stringify({ selected_task_type: selectedTaskType }),
  });
}

export function deleteTaskSession(sessionId) {
  return request(`/task-sessions/${sessionId}`, { method: "DELETE" });
}

export function submitEvaluation(payload) {
  return request("/submissions/evaluate", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function getMySubmissions() {
  return request("/submissions/my");
}

export function getActiveSubmissions() {
  return request("/submissions/active");
}

export function getSubmission(submissionId) {
  return request(`/submissions/${submissionId}`);
}

export function deleteSubmission(submissionId) {
  return request(`/submissions/${submissionId}`, { method: "DELETE" });
}

export function adminGetUsers() {
  return request("/admin/users");
}

export function adminGetUser(userId) {
  return request(`/admin/users/${userId}`);
}

export function adminCreateUser(data) {
  return request("/admin/users", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function adminUpdateUser(userId, data) {
  return request(`/admin/users/${userId}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export function adminDeleteUser(userId) {
  return request(`/admin/users/${userId}`, { method: "DELETE" });
}

export function adminUpdateUserCounters(userId, data) {
  return request(`/admin/users/${userId}/counters`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export function adminActivateUser(userId) {
  return request(`/admin/users/${userId}/activate`, { method: "PATCH" });
}

export function adminDeactivateUser(userId) {
  return request(`/admin/users/${userId}/deactivate`, { method: "PATCH" });
}

export function adminGetInfoTasks() {
  return request("/admin/info-tasks");
}

export function adminGetInfoTask(taskId) {
  return request(`/admin/info-tasks/${taskId}`);
}

export function adminCreateInfoTask(data) {
  return request("/admin/info-tasks", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function adminUpdateInfoTask(taskId, data) {
  return request(`/admin/info-tasks/${taskId}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export function adminDeleteInfoTask(taskId) {
  return request(`/admin/info-tasks/${taskId}`, { method: "DELETE" });
}

export function adminGetComplaintTasks() {
  return request("/admin/complaint-tasks");
}

export function adminGetComplaintTask(taskId) {
  return request(`/admin/complaint-tasks/${taskId}`);
}

export function adminCreateComplaintTask(data) {
  return request("/admin/complaint-tasks", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function adminUpdateComplaintTask(taskId, data) {
  return request(`/admin/complaint-tasks/${taskId}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export function adminDeleteComplaintTask(taskId) {
  return request(`/admin/complaint-tasks/${taskId}`, { method: "DELETE" });
}
