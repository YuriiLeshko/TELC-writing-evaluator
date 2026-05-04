import { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import Card from "../components/Card.jsx";
import Button from "../components/Button.jsx";
import Badge from "../components/Badge.jsx";
import LoadingState from "../components/LoadingState.jsx";
import {
  deleteSubmission,
  deleteTaskSession,
  getActiveTaskSessions,
  getMySubmissions,
  getTaskSession,
} from "../api/client.js";
import { formatDateTime } from "../utils/date.js";

function statusBadge(status) {
  if (status === "success") return <Badge variant="success">{status}</Badge>;
  if (status === "failed") return <Badge variant="danger">{status}</Badge>;
  return <Badge variant="neutral">{status || "—"}</Badge>;
}

function submissionHasResult(sub) {
  const res = sub?.result;
  return res && typeof res === "object" && Object.keys(res).length > 0;
}

export default function ArchivePage() {
  const navigate = useNavigate();
  const [sessions, setSessions] = useState([]);
  const [submissions, setSubmissions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const load = useCallback(async () => {
    setError(null);
    setLoading(true);
    try {
      const [s, sub] = await Promise.all([getActiveTaskSessions(), getMySubmissions()]);
      setSessions(Array.isArray(s) ? s : []);
      setSubmissions(Array.isArray(sub) ? sub : []);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const onShowDetails = async (sub) => {
    setError(null);
    let session = null;
    try {
      session = await getTaskSession(sub.task_session_id);
    } catch {
      session = null;
    }
    const selectedTaskType = sub.selected_task_type;
    const selectedTask =
      session && selectedTaskType === "info"
        ? session.info_task
        : session && selectedTaskType === "complaint"
          ? session.complaint_task
          : null;
    navigate("/result", {
      state: {
        result: sub.result ?? {},
        candidateText: sub.candidate_text ?? "",
        submission: sub,
        session,
        selectedTaskType,
        selectedTask,
        submissionId: sub.id,
      },
    });
  };

  const onDeleteSession = async (id) => {
    if (!window.confirm("Sitzung wirklich löschen?")) return;
    try {
      await deleteTaskSession(id);
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  };

  const onDeleteSubmission = async (id) => {
    if (!window.confirm("Einreichung wirklich löschen?")) return;
    try {
      await deleteSubmission(id);
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  };

  return (
    <div className="stack">
      <h1 className="page-title">Archiv</h1>
      <p className="page-subtitle">Aktive Sitzungen und Ihre Einreichungen.</p>

      {error ? (
        <div className="alert alert--error" role="alert">
          {error}
        </div>
      ) : null}

      {loading ? <LoadingState /> : null}

      {!loading ? (
        <>
          <Card title="Aktive Sitzungen (nicht abgeschlossen)">
            {!sessions.length ? (
              <p className="metric-card__help">Keine aktiven Sitzungen.</p>
            ) : (
              <ul style={{ listStyle: "none", padding: 0, margin: 0 }}>
                {sessions.map((s) => (
                  <li
                    key={s.id}
                    className="admin-user-row"
                    style={{ display: "flex", flexWrap: "wrap", gap: "0.5rem", alignItems: "center" }}
                  >
                    <span>
                      <strong>#{s.id}</strong> — {formatDateTime(s.started_at)}
                    </span>
                    {statusBadge(s.status)}
                    <Button type="button" variant="danger" onClick={() => onDeleteSession(s.id)}>
                      Löschen
                    </Button>
                  </li>
                ))}
              </ul>
            )}
          </Card>

          <Card title="Einreichungen">
            {!submissions.length ? (
              <p className="metric-card__help">Noch keine Einreichungen.</p>
            ) : (
              <ul style={{ listStyle: "none", padding: 0, margin: 0 }}>
                {submissions.map((sub) => {
                  const canOpenResult = submissionHasResult(sub);
                  return (
                    <li key={sub.id} className="admin-user-row">
                      <div style={{ display: "flex", flexWrap: "wrap", gap: "0.5rem", alignItems: "center" }}>
                        <span>
                          <strong>#{sub.id}</strong> {formatDateTime(sub.submitted_at)}
                        </span>
                        <Badge variant="neutral">{sub.selected_task_type || "—"}</Badge>
                        <span>
                          Score: {sub.final_score ?? "—"} / {sub.max_score ?? "—"}
                        </span>
                        <span>Wörter: {sub.word_count ?? "—"}</span>
                        {statusBadge(sub.status)}
                        <Button
                          type="button"
                          variant="secondary"
                          disabled={!canOpenResult}
                          onClick={() => onShowDetails(sub)}
                          title={!canOpenResult ? "Kein auswertbares Ergebnis vorhanden." : undefined}
                        >
                          Details anzeigen
                        </Button>
                        <Button type="button" variant="danger" onClick={() => onDeleteSubmission(sub.id)}>
                          Löschen
                        </Button>
                      </div>
                      {sub.error_message ? (
                        <div className="alert alert--error" style={{ marginTop: "0.5rem" }} role="alert">
                          Fehler: {sub.error_message}
                        </div>
                      ) : null}
                    </li>
                  );
                })}
              </ul>
            )}
          </Card>
        </>
      ) : null}
    </div>
  );
}
