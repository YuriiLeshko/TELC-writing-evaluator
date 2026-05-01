import { useCallback, useEffect, useState } from "react";
import Card from "../components/Card.jsx";
import Button from "../components/Button.jsx";
import Textarea from "../components/Textarea.jsx";
import LoadingState from "../components/LoadingState.jsx";
import {
  adminActivateUser,
  adminCreateComplaintTask,
  adminCreateInfoTask,
  adminDeactivateUser,
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

const emptyTaskForm = () => ({
  task_number: 1,
  source_text: "",
  situation_text: "",
  instruction_text: "",
  expected_key_points: "",
  is_active: true,
});

export default function AdminPage() {
  const [tab, setTab] = useState("users");
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  const [users, setUsers] = useState([]);
  const [counterDrafts, setCounterDrafts] = useState({});

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
    try {
      await adminCreateInfoTask({
        task_number: Number(infoForm.task_number),
        source_text: infoForm.source_text,
        situation_text: infoForm.situation_text,
        instruction_text: infoForm.instruction_text,
        expected_key_points: splitKeyPointsMultiline(infoForm.expected_key_points),
        is_active: Boolean(infoForm.is_active),
      });
      setInfoForm(emptyTaskForm());
      await loadInfo();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  };

  const onCreateComplaint = async (e) => {
    e.preventDefault();
    setError(null);
    try {
      await adminCreateComplaintTask({
        task_number: Number(complaintForm.task_number),
        source_text: complaintForm.source_text,
        situation_text: complaintForm.situation_text,
        instruction_text: complaintForm.instruction_text,
        expected_key_points: splitKeyPointsMultiline(complaintForm.expected_key_points),
        is_active: Boolean(complaintForm.is_active),
      });
      setComplaintForm(emptyTaskForm());
      await loadComplaint();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  };

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
      {loading ? <LoadingState /> : null}

      {!loading && tab === "users" ? (
        <Card title="Benutzer">
          <div className="admin-grid">
            {users.map((u) => (
              <div key={u.id} className="admin-user-row">
                <div>
                  <strong>
                    #{u.id} {u.email}
                  </strong>{" "}
                  <span className="metric-card__help">({u.role})</span>
                </div>
                <div className="row" style={{ marginTop: "0.5rem", gap: "0.5rem" }}>
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
                </div>
                <div className="row" style={{ marginTop: "0.5rem" }}>
                  <Button type="button" variant="primary" onClick={() => onSaveCounters(u.id)}>
                    Zähler aktualisieren
                  </Button>
                  <Button
                    type="button"
                    variant="secondary"
                    onClick={async () => {
                      try {
                        await adminActivateUser(u.id);
                        await loadUsers();
                      } catch (err) {
                        setError(err instanceof Error ? err.message : String(err));
                      }
                    }}
                  >
                    Aktivieren
                  </Button>
                  <Button
                    type="button"
                    variant="danger"
                    onClick={async () => {
                      try {
                        await adminDeactivateUser(u.id);
                        await loadUsers();
                      } catch (err) {
                        setError(err instanceof Error ? err.message : String(err));
                      }
                    }}
                  >
                    Deaktivieren
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </Card>
      ) : null}

      {!loading && tab === "info" ? (
        <div className="stack">
          <Card title="Neue Info-Aufgabe">
            <form className="admin-form stack stack--sm" onSubmit={onCreateInfo}>
              <label>
                task_number
                <input
                  type="number"
                  value={infoForm.task_number}
                  onChange={(e) => setInfoForm((f) => ({ ...f, task_number: e.target.value }))}
                />
              </label>
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
              <label style={{ display: "flex", alignItems: "center", gap: "0.35rem" }}>
                <input
                  type="checkbox"
                  checked={infoForm.is_active}
                  onChange={(e) => setInfoForm((f) => ({ ...f, is_active: e.target.checked }))}
                />
                is_active
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
                  onDelete={async () => {
                    try {
                      await adminDeleteInfoTask(t.id);
                      await loadInfo();
                    } catch (err) {
                      setError(err instanceof Error ? err.message : String(err));
                    }
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
                task_number
                <input
                  type="number"
                  value={complaintForm.task_number}
                  onChange={(e) => setComplaintForm((f) => ({ ...f, task_number: e.target.value }))}
                />
              </label>
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
              <label style={{ display: "flex", alignItems: "center", gap: "0.35rem" }}>
                <input
                  type="checkbox"
                  checked={complaintForm.is_active}
                  onChange={(e) => setComplaintForm((f) => ({ ...f, is_active: e.target.checked }))}
                />
                is_active
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
                  onDelete={async () => {
                    try {
                      await adminDeleteComplaintTask(t.id);
                      await loadComplaint();
                    } catch (err) {
                      setError(err instanceof Error ? err.message : String(err));
                    }
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

function TaskInlineEditor({ kind, task, onSaved, onError, onDelete }) {
  const [source_text, setSource] = useState(task.source_text || "");
  const [situation_text, setSituation] = useState(task.situation_text || "");
  const [instruction_text, setInstruction] = useState(task.instruction_text || "");
  const [expected_key_points, setKp] = useState((task.expected_key_points || []).join("\n"));
  const [task_number, setTn] = useState(task.task_number);
  const [is_active, setActive] = useState(task.is_active !== false);

  const save = async () => {
    onError(null);
    const body = {
      task_number: Number(task_number),
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
      <label>
        task_number
        <input type="number" value={task_number} onChange={(e) => setTn(e.target.value)} />
      </label>
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
      <label style={{ display: "flex", alignItems: "center", gap: "0.35rem" }}>
        <input type="checkbox" checked={is_active} onChange={(e) => setActive(e.target.checked)} />
        is_active
      </label>
      <div className="row">
        <Button type="button" variant="primary" onClick={save}>
          Speichern
        </Button>
        <Button type="button" variant="danger" onClick={onDelete}>
          Deaktivieren (DELETE)
        </Button>
      </div>
    </div>
  );
}
