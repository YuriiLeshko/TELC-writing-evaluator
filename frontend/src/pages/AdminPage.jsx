import { useCallback, useEffect, useState } from "react";
import Card from "../components/Card.jsx";
import Button from "../components/Button.jsx";
import Badge from "../components/Badge.jsx";
import Textarea from "../components/Textarea.jsx";
import LoadingState from "../components/LoadingState.jsx";
import {
  adminActivateUser,
  adminActivateComplaintTask,
  adminActivateInfoTask,
  adminCreateUser,
  adminCreateComplaintTask,
  adminCreateInfoTask,
  adminDeactivateComplaintTask,
  adminDeactivateUser,
  adminDeactivateInfoTask,
  adminDeleteUser,
  adminDeleteComplaintTask,
  adminDeleteInfoTask,
  adminGetComplaintTasks,
  adminGetInfoTasks,
  adminGetUsers,
  adminUpdateComplaintTask,
  adminUpdateInfoTask,
  adminUpdateUserCounters,
} from "../api/client.js";
import { splitKeyPointsMultiline } from "../utils/text.js";

const TABS = [
  { id: "users", label: "Benutzer" },
  { id: "info", label: "Info-Aufgaben" },
  { id: "complaint", label: "Beschwerde-Aufgaben" },
];
const CURRENT_ADMIN_EMAIL = "admin@example.com";

const emptyTaskForm = () => ({
  source_text: "",
  situation_text: "",
  instruction_text: "",
  expected_key_points: "",
});

const emptyUserCreateForm = () => ({
  username: "",
  email: "",
  password: "",
  role: "user",
  available_sessions: 5,
  available_submissions: 5,
  is_active: true,
});

export default function AdminPage() {
  const [tab, setTab] = useState("users");
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [loading, setLoading] = useState(false);

  const [users, setUsers] = useState([]);
  const [counterDrafts, setCounterDrafts] = useState({});
  const [pendingDeleteUserId, setPendingDeleteUserId] = useState(null);
  const [pendingUserActionId, setPendingUserActionId] = useState(null);
  const [showCreateUserForm, setShowCreateUserForm] = useState(false);
  const [confirmCreateUser, setConfirmCreateUser] = useState(false);
  const [createUserForm, setCreateUserForm] = useState(() => emptyUserCreateForm());

  const [infoTasks, setInfoTasks] = useState([]);
  const [complaintTasks, setComplaintTasks] = useState([]);
  const [infoForm, setInfoForm] = useState(() => emptyTaskForm());
  const [complaintForm, setComplaintForm] = useState(() => emptyTaskForm());

  const setCountersForUser = (userId, field, value) => {
    setCounterDrafts((d) => ({
      ...d,
      [userId]: { ...d[userId], [field]: value },
    }));
  };

  const loadUsers = useCallback(async () => {
    const list = await adminGetUsers();
    setUsers(Array.isArray(list) ? list : []);
    const drafts = {};
    for (const u of list || []) {
      drafts[u.id] = {
        available_sessions: u.available_sessions,
        available_submissions: u.available_submissions,
      };
    }
    setCounterDrafts(drafts);
  }, []);

  const loadInfo = useCallback(async () => {
    const list = await adminGetInfoTasks();
    setInfoTasks(Array.isArray(list) ? list : []);
  }, []);

  const loadComplaint = useCallback(async () => {
    const list = await adminGetComplaintTasks();
    setComplaintTasks(Array.isArray(list) ? list : []);
  }, []);

  const refreshTab = useCallback(async () => {
    setError(null);
    setLoading(true);
    try {
      if (tab === "users") await loadUsers();
      if (tab === "info") await loadInfo();
      if (tab === "complaint") await loadComplaint();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  }, [tab, loadUsers, loadInfo, loadComplaint]);

  useEffect(() => {
    refreshTab();
  }, [refreshTab]);

  const onSaveCounters = async (userId) => {
    setError(null);
    setSuccess(null);
    const draft = counterDrafts[userId] || {};
    try {
      await adminUpdateUserCounters(userId, {
        available_sessions: Number(draft.available_sessions),
        available_submissions: Number(draft.available_submissions),
      });
      await loadUsers();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  };

  const onCreateInfo = async (e) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);
    const keyPoints = splitKeyPointsMultiline(infoForm.expected_key_points);
    if (!infoForm.source_text.trim() || !infoForm.situation_text.trim() || !infoForm.instruction_text.trim() || keyPoints.length === 0) {
      setError("Bitte alle Pflichtfelder ausfüllen (inkl. mindestens ein erwarteter Punkt).");
      return;
    }
    try {
      await adminCreateInfoTask({
        source_text: infoForm.source_text,
        situation_text: infoForm.situation_text,
        instruction_text: infoForm.instruction_text,
        expected_key_points: keyPoints,
      });
      setInfoForm(emptyTaskForm());
      await loadInfo();
      setSuccess("Aufgabe wurde inaktiv erstellt. Aktivieren Sie sie, wenn sie für Benutzer sichtbar sein soll.");
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  };

  const onCreateComplaint = async (e) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);
    const keyPoints = splitKeyPointsMultiline(complaintForm.expected_key_points);
    if (!complaintForm.source_text.trim() || !complaintForm.situation_text.trim() || !complaintForm.instruction_text.trim() || keyPoints.length === 0) {
      setError("Bitte alle Pflichtfelder ausfüllen (inkl. mindestens ein erwarteter Punkt).");
      return;
    }
    try {
      await adminCreateComplaintTask({
        source_text: complaintForm.source_text,
        situation_text: complaintForm.situation_text,
        instruction_text: complaintForm.instruction_text,
        expected_key_points: keyPoints,
      });
      setComplaintForm(emptyTaskForm());
      await loadComplaint();
      setSuccess("Aufgabe wurde inaktiv erstellt. Aktivieren Sie sie, wenn sie für Benutzer sichtbar sein soll.");
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  };

  const onRequestCreateUser = () => {
    const email = String(createUserForm.email || "").trim();
    const password = String(createUserForm.password || "").trim();
    const role = String(createUserForm.role || "");
    const sessions = Number(createUserForm.available_sessions);
    const submissions = Number(createUserForm.available_submissions);

    if (!email) {
      setError("E-Mail darf nicht leer sein.");
      setConfirmCreateUser(false);
      return;
    }
    if (!password) {
      setError("Passwort darf nicht leer sein.");
      setConfirmCreateUser(false);
      return;
    }
    if (role !== "user" && role !== "admin") {
      setError('Rolle muss "user" oder "admin" sein.');
      setConfirmCreateUser(false);
      return;
    }
    if (!Number.isFinite(sessions) || sessions < 0 || !Number.isFinite(submissions) || submissions < 0) {
      setError("Verfügbare Sitzungen und Einreichungen müssen >= 0 sein.");
      setConfirmCreateUser(false);
      return;
    }

    setError(null);
    setSuccess(null);
    setConfirmCreateUser(true);
  };

  const onConfirmCreateUser = async () => {
    setError(null);
    setSuccess(null);
    try {
      await adminCreateUser({
        username: String(createUserForm.username || "").trim() || undefined,
        email: String(createUserForm.email || "").trim(),
        password: String(createUserForm.password || "").trim(),
        role: createUserForm.role,
        available_sessions: Number(createUserForm.available_sessions),
        available_submissions: Number(createUserForm.available_submissions),
        is_active: Boolean(createUserForm.is_active),
      });
      setCreateUserForm(emptyUserCreateForm());
      setConfirmCreateUser(false);
      setShowCreateUserForm(false);
      await loadUsers();
      setSuccess("Benutzer erfolgreich erstellt.");
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  };

  const adminUsers = users.filter((u) => u.role === "admin");
  const regularUsers = users.filter((u) => u.role === "user");

  const renderUserGroup = (title, list) => (
    <div className="admin-user-group">
      <h3 className="admin-user-group__title">
        {title} ({list.length})
      </h3>
      {list.length === 0 ? (
        <p className="metric-card__help">Keine Einträge in dieser Gruppe.</p>
      ) : (
        <div className="admin-grid">
          {list.map((u) => (
            <div key={u.id} className="admin-user-row">
              {(() => {
                const email = String(u.email || "").toLowerCase();
                const isCurrentAdmin = email === CURRENT_ADMIN_EMAIL;
                const isAdmin = u.role === "admin";
                const canToggleActive = !isCurrentAdmin;
                const canDelete = !isCurrentAdmin && !isAdmin;

                return (
                  <>
                    <div className="admin-user-row__head">
                      <strong>
                        #{u.id} {u.email}
                      </strong>
                      <div className="admin-user-row__badges">
                        <Badge variant={isAdmin ? "warning" : "neutral"}>{isAdmin ? "Admin" : "User"}</Badge>
                        <Badge variant={u.is_active ? "success" : "danger"}>{u.is_active ? "Aktiv" : "Inaktiv"}</Badge>
                      </div>
                    </div>
                    <div className="row admin-user-row__counter-row">
                      <label>
                        Sitzungen
                        <input
                          type="number"
                          className="input-like"
                          style={{ marginTop: "0.2rem", maxWidth: "8rem" }}
                          value={counterDrafts[u.id]?.available_sessions ?? ""}
                          onChange={(e) => setCountersForUser(u.id, "available_sessions", e.target.value)}
                        />
                      </label>
                      <label>
                        Einreichungen
                        <input
                          type="number"
                          className="input-like"
                          style={{ marginTop: "0.2rem", maxWidth: "8rem" }}
                          value={counterDrafts[u.id]?.available_submissions ?? ""}
                          onChange={(e) => setCountersForUser(u.id, "available_submissions", e.target.value)}
                        />
                      </label>
                      <Button type="button" variant="primary" className="admin-user-row__counter-save" onClick={() => onSaveCounters(u.id)}>
                        Zähler aktualisieren
                      </Button>
                    </div>
                    <div className="row admin-user-row__actions">
                      {canToggleActive ? (
                        u.is_active ? (
                          <Button
                            type="button"
                            variant="secondary"
                            disabled={pendingUserActionId === u.id}
                            onClick={async () => {
                              try {
                                setError(null);
                                setSuccess(null);
                                setPendingUserActionId(u.id);
                                const resp = await adminDeactivateUser(u.id);
                                console.log("[admin] deactivate-user", { id: u.id, response: resp });
                                await loadUsers();
                                setSuccess("Benutzer erfolgreich deaktiviert.");
                              } catch (err) {
                                setError(err instanceof Error ? err.message : String(err));
                              } finally {
                                setPendingUserActionId(null);
                              }
                            }}
                          >
                            Deaktivieren
                          </Button>
                        ) : (
                          <Button
                            type="button"
                            variant="secondary"
                            disabled={pendingUserActionId === u.id}
                            onClick={async () => {
                              try {
                                setError(null);
                                setSuccess(null);
                                setPendingUserActionId(u.id);
                                const resp = await adminActivateUser(u.id);
                                console.log("[admin] activate-user", { id: u.id, response: resp });
                                await loadUsers();
                                setSuccess("Benutzer erfolgreich aktiviert.");
                              } catch (err) {
                                setError(err instanceof Error ? err.message : String(err));
                              } finally {
                                setPendingUserActionId(null);
                              }
                            }}
                          >
                            Aktivieren
                          </Button>
                        )
                      ) : null}
                      {canDelete ? (
                        pendingDeleteUserId === u.id ? (
                          <div className="archive-delete-confirm">
                            <span className="archive-delete-confirm__text">Benutzer wirklich löschen?</span>
                            <Button
                              type="button"
                              variant="danger"
                              disabled={pendingUserActionId === u.id}
                              onClick={async () => {
                                try {
                                  setError(null);
                                  setSuccess(null);
                                  setPendingUserActionId(u.id);
                                  const resp = await adminDeleteUser(u.id);
                                  console.log("[admin] delete-user", { id: u.id, response: resp });
                                  setPendingDeleteUserId(null);
                                  await loadUsers();
                                  setSuccess("Benutzer erfolgreich gelöscht.");
                                } catch (err) {
                                  setError(err instanceof Error ? err.message : String(err));
                                } finally {
                                  setPendingUserActionId(null);
                                }
                              }}
                            >
                              Ja, löschen
                            </Button>
                            <Button type="button" variant="secondary" onClick={() => setPendingDeleteUserId(null)}>
                              Abbrechen
                            </Button>
                          </div>
                        ) : (
                          <Button type="button" variant="danger" onClick={() => setPendingDeleteUserId(u.id)}>
                            Benutzer löschen
                          </Button>
                        )
                      ) : null}
                      {isCurrentAdmin ? (
                        <span className="metric-card__help">Eigener Admin-Account kann nicht deaktiviert oder gelöscht werden.</span>
                      ) : null}
                      {isAdmin && !isCurrentAdmin ? (
                        <span className="metric-card__help">Andere Admins können nur deaktiviert werden.</span>
                      ) : null}
                    </div>
                  </>
                );
              })()}
            </div>
          ))}
        </div>
      )}
    </div>
  );

  return (
    <div className="stack">
      <h1 className="page-title">Administration</h1>
      <p className="page-subtitle">MVP-Formulare für Demo-Admin. Fehler vom Backend werden angezeigt.</p>

      <div className="admin-tabs">
        {TABS.map((t) => (
          <button
            key={t.id}
            type="button"
            className={`task-tabs__btn ${tab === t.id ? "task-tabs__btn--active" : ""}`.trim()}
            onClick={() => setTab(t.id)}
          >
            {t.label}
          </button>
        ))}
      </div>

      {error ? <div className="alert alert--error">{error}</div> : null}
      {success ? <div className="alert">{success}</div> : null}
      {loading ? <LoadingState /> : null}

      {!loading && tab === "users" ? (
        <Card title="Benutzer">
          <div className="stack">
            <div className="row">
              <Button
                type="button"
                variant={showCreateUserForm ? "secondary" : "primary"}
                onClick={() => {
                  setError(null);
                  setSuccess(null);
                  setConfirmCreateUser(false);
                  setShowCreateUserForm((v) => !v);
                }}
              >
                Neuen Benutzer erstellen
              </Button>
            </div>
            {showCreateUserForm ? (
              <div className="admin-user-create-card">
                <div className="admin-user-create-grid">
                  <label>
                    Benutzername
                    <input
                      type="text"
                      className="input-like"
                      value={createUserForm.username}
                      onChange={(e) => setCreateUserForm((f) => ({ ...f, username: e.target.value }))}
                    />
                  </label>
                  <label>
                    E-Mail
                    <input
                      type="email"
                      className="input-like"
                      value={createUserForm.email}
                      onChange={(e) => setCreateUserForm((f) => ({ ...f, email: e.target.value }))}
                    />
                  </label>
                  <label>
                    Passwort
                    <input
                      type="password"
                      className="input-like"
                      value={createUserForm.password}
                      onChange={(e) => setCreateUserForm((f) => ({ ...f, password: e.target.value }))}
                    />
                  </label>
                  <label>
                    Rolle
                    <select
                      className="input-like"
                      value={createUserForm.role}
                      onChange={(e) => setCreateUserForm((f) => ({ ...f, role: e.target.value }))}
                    >
                      <option value="user">user</option>
                      <option value="admin">admin</option>
                    </select>
                  </label>
                  <label>
                    Verfügbare Sitzungen
                    <input
                      type="number"
                      min="0"
                      className="input-like"
                      value={createUserForm.available_sessions}
                      onChange={(e) => setCreateUserForm((f) => ({ ...f, available_sessions: e.target.value }))}
                    />
                  </label>
                  <label>
                    Verfügbare Einreichungen
                    <input
                      type="number"
                      min="0"
                      className="input-like"
                      value={createUserForm.available_submissions}
                      onChange={(e) => setCreateUserForm((f) => ({ ...f, available_submissions: e.target.value }))}
                    />
                  </label>
                </div>
                <label className="admin-user-create-active">
                  <input
                    type="checkbox"
                    checked={createUserForm.is_active}
                    onChange={(e) => setCreateUserForm((f) => ({ ...f, is_active: e.target.checked }))}
                  />
                  Aktiv
                </label>
                {confirmCreateUser ? (
                  <div className="archive-delete-confirm" style={{ marginTop: "0.4rem", justifyContent: "flex-start" }}>
                    <span className="archive-delete-confirm__text">Neuen Benutzer wirklich erstellen?</span>
                    <Button type="button" variant="primary" onClick={onConfirmCreateUser}>
                      Ja, erstellen
                    </Button>
                    <Button type="button" variant="secondary" onClick={() => setConfirmCreateUser(false)}>
                      Abbrechen
                    </Button>
                  </div>
                ) : (
                  <div className="row" style={{ marginTop: "0.4rem" }}>
                    <Button type="button" variant="primary" onClick={onRequestCreateUser}>
                      Benutzer erstellen
                    </Button>
                  </div>
                )}
              </div>
            ) : null}
            {renderUserGroup("Administratoren", adminUsers)}
            {renderUserGroup("Benutzer", regularUsers)}
          </div>
        </Card>
      ) : null}

      {!loading && tab === "info" ? (
        <div className="stack">
          <Card title="Neue Info-Aufgabe">
            <form className="admin-form stack stack--sm" onSubmit={onCreateInfo}>
              <label>
                source_text
                <Textarea rows={3} value={infoForm.source_text} onChange={(e) => setInfoForm((f) => ({ ...f, source_text: e.target.value }))} />
              </label>
              <label>
                situation_text
                <Textarea rows={3} value={infoForm.situation_text} onChange={(e) => setInfoForm((f) => ({ ...f, situation_text: e.target.value }))} />
              </label>
              <label>
                instruction_text
                <Textarea rows={3} value={infoForm.instruction_text} onChange={(e) => setInfoForm((f) => ({ ...f, instruction_text: e.target.value }))} />
              </label>
              <label>
                expected_key_points (eine Zeile pro Punkt)
                <Textarea rows={4} value={infoForm.expected_key_points} onChange={(e) => setInfoForm((f) => ({ ...f, expected_key_points: e.target.value }))} />
              </label>
              <Button type="submit" variant="primary">
                Anlegen
              </Button>
            </form>
          </Card>
          <Card title="Bestehende Info-Aufgaben">
            {infoTasks.map((t) => (
              <details key={t.id} className="summary-block" style={{ marginBottom: "0.65rem" }}>
                <summary>
                  #{t.id} — Task {t.task_number}
                </summary>
                <TaskInlineEditor
                  kind="info"
                  task={t}
                  onSaved={loadInfo}
                  onError={setError}
                  onActivate={async () => {
                    const resp = await adminActivateInfoTask(t.id);
                    console.log("[admin] activate-info-task", { id: t.id, response: resp });
                    await loadInfo();
                  }}
                  onDeactivate={async () => {
                    const resp = await adminDeactivateInfoTask(t.id);
                    console.log("[admin] deactivate-info-task", { id: t.id, response: resp });
                    await loadInfo();
                    return resp;
                  }}
                  onDelete={async () => {
                    const resp = await adminDeleteInfoTask(t.id);
                    console.log("[admin] delete-info-task", { id: t.id, response: resp });
                    await loadInfo();
                    return resp;
                  }}
                />
              </details>
            ))}
          </Card>
        </div>
      ) : null}

      {!loading && tab === "complaint" ? (
        <div className="stack">
          <Card title="Neue Beschwerde-Aufgabe">
            <form className="admin-form stack stack--sm" onSubmit={onCreateComplaint}>
              <label>
                source_text
                <Textarea rows={3} value={complaintForm.source_text} onChange={(e) => setComplaintForm((f) => ({ ...f, source_text: e.target.value }))} />
              </label>
              <label>
                situation_text
                <Textarea rows={3} value={complaintForm.situation_text} onChange={(e) => setComplaintForm((f) => ({ ...f, situation_text: e.target.value }))} />
              </label>
              <label>
                instruction_text
                <Textarea rows={3} value={complaintForm.instruction_text} onChange={(e) => setComplaintForm((f) => ({ ...f, instruction_text: e.target.value }))} />
              </label>
              <label>
                expected_key_points (eine Zeile pro Punkt)
                <Textarea rows={4} value={complaintForm.expected_key_points} onChange={(e) => setComplaintForm((f) => ({ ...f, expected_key_points: e.target.value }))} />
              </label>
              <Button type="submit" variant="primary">
                Anlegen
              </Button>
            </form>
          </Card>
          <Card title="Bestehende Beschwerde-Aufgaben">
            {complaintTasks.map((t) => (
              <details key={t.id} className="summary-block" style={{ marginBottom: "0.65rem" }}>
                <summary>
                  #{t.id} — Task {t.task_number}
                </summary>
                <TaskInlineEditor
                  kind="complaint"
                  task={t}
                  onSaved={loadComplaint}
                  onError={setError}
                  onActivate={async () => {
                    const resp = await adminActivateComplaintTask(t.id);
                    console.log("[admin] activate-complaint-task", { id: t.id, response: resp });
                    await loadComplaint();
                  }}
                  onDeactivate={async () => {
                    const resp = await adminDeactivateComplaintTask(t.id);
                    console.log("[admin] deactivate-complaint-task", { id: t.id, response: resp });
                    await loadComplaint();
                    return resp;
                  }}
                  onDelete={async () => {
                    const resp = await adminDeleteComplaintTask(t.id);
                    console.log("[admin] delete-complaint-task", { id: t.id, response: resp });
                    await loadComplaint();
                    return resp;
                  }}
                />
              </details>
            ))}
          </Card>
        </div>
      ) : null}
    </div>
  );
}

function TaskInlineEditor({ kind, task, onSaved, onError, onActivate, onDeactivate, onDelete }) {
  const [source_text, setSource] = useState(task.source_text || "");
  const [situation_text, setSituation] = useState(task.situation_text || "");
  const [instruction_text, setInstruction] = useState(task.instruction_text || "");
  const [expected_key_points, setKp] = useState((task.expected_key_points || []).join("\n"));
  const [is_active, setActive] = useState(Boolean(task.is_active));
  const [confirmSave, setConfirmSave] = useState(false);
  const [confirmAction, setConfirmAction] = useState(null);
  const [actionLoading, setActionLoading] = useState(false);

  useEffect(() => {
    setActive(Boolean(task.is_active));
  }, [task.id, task.is_active]);

  const save = async () => {
    onError(null);
    const body = {
      source_text,
      situation_text,
      instruction_text,
      expected_key_points: splitKeyPointsMultiline(expected_key_points),
      is_active,
    };
    try {
      if (kind === "info") await adminUpdateInfoTask(task.id, body);
      else await adminUpdateComplaintTask(task.id, body);
      await onSaved();
    } catch (e) {
      onError(e instanceof Error ? e.message : String(e));
    }
  };

  return (
    <div className="admin-form stack stack--sm" style={{ marginTop: "0.65rem" }}>
      <p className="metric-card__help">task_number: {task.task_number}</p>
      {!is_active ? <Badge variant="danger">Inaktiv</Badge> : null}
      <label>
        source_text
        <Textarea rows={3} value={source_text} onChange={(e) => setSource(e.target.value)} />
      </label>
      <label>
        situation_text
        <Textarea rows={3} value={situation_text} onChange={(e) => setSituation(e.target.value)} />
      </label>
      <label>
        instruction_text
        <Textarea rows={3} value={instruction_text} onChange={(e) => setInstruction(e.target.value)} />
      </label>
      <label>
        expected_key_points
        <Textarea rows={4} value={expected_key_points} onChange={(e) => setKp(e.target.value)} />
      </label>
      <div className="row">
        {confirmSave ? (
          <div className="archive-delete-confirm">
            <span className="archive-delete-confirm__text">Änderungen wirklich speichern?</span>
            <Button
              type="button"
              variant="primary"
              onClick={async () => {
                await save();
                setConfirmSave(false);
              }}
            >
              Ja, speichern
            </Button>
            <Button type="button" variant="secondary" onClick={() => setConfirmSave(false)}>
              Abbrechen
            </Button>
          </div>
        ) : (
          <Button type="button" variant="primary" onClick={() => setConfirmSave(true)}>
            Aktualisieren
          </Button>
        )}
        {is_active ? (
          <Button type="button" variant="secondary" disabled={actionLoading} onClick={() => setConfirmAction("deactivate")}>
            Deaktivieren
          </Button>
        ) : (
          <Button
            type="button"
            variant="secondary"
            disabled={actionLoading}
            onClick={async () => {
              try {
                setActionLoading(true);
                await onActivate();
                console.log(`[admin] activate-${kind}-task`, { id: task.id });
              } catch (e) {
                onError(e instanceof Error ? e.message : String(e));
              } finally {
                setActionLoading(false);
              }
            }}
          >
            Aktivieren
          </Button>
        )}
        <Button type="button" variant="danger" disabled={actionLoading} onClick={() => setConfirmAction("delete")}>
          Löschen
        </Button>
        {confirmAction ? (
          <div className="archive-delete-confirm">
            <span className="archive-delete-confirm__text">
              {confirmAction === "deactivate"
                ? "Wirklich deaktivieren?"
                : "Wirklich endgültig löschen? Diese Aktion kann nicht rückgängig gemacht werden."}
            </span>
            <Button
              type="button"
              variant="danger"
              disabled={actionLoading}
              onClick={async () => {
                try {
                  setActionLoading(true);
                  const resp = confirmAction === "deactivate" ? await onDeactivate() : await onDelete();
                  console.log(
                    confirmAction === "deactivate" ? `[admin] deactivate-${kind}-task` : `[admin] delete-${kind}-task`,
                    { id: task.id, response: resp },
                  );
                  setConfirmAction(null);
                } catch (e) {
                  onError(e instanceof Error ? e.message : String(e));
                } finally {
                  setActionLoading(false);
                }
              }}
            >
              {confirmAction === "deactivate" ? "Ja, deaktivieren" : "Ja, löschen"}
            </Button>
            <Button type="button" variant="secondary" disabled={actionLoading} onClick={() => setConfirmAction(null)}>
              Abbrechen
            </Button>
          </div>
        ) : null}
      </div>
    </div>
  );
}
