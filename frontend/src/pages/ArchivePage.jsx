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
  const [pendingDelete, setPendingDelete] = useState(null);
  const [deletingKey, setDeletingKey] = useState(null);

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
    setError(null);
    setDeletingKey(`session-${id}`);
    try {
      await deleteTaskSession(id);
      setPendingDelete(null);
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setDeletingKey(null);
    }
  };

  const onDeleteSubmission = async (id) => {
    setError(null);
    setDeletingKey(`submission-${id}`);
    try {
      await deleteSubmission(id);
      setPendingDelete(null);
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setDeletingKey(null);
    }
  };

  const onContinueSession = async (session) => {
    setError(null);
    try {
      const fullSession = await getTaskSession(session.id);
      navigate("/training", {
        state: {
          activeSession: fullSession ?? session,
          selectedTaskType:
            fullSession?.selected_task_type ??
            fullSession?.selectedTaskType ??
            session?.selected_task_type ??
            session?.selectedTaskType ??
            null,
        },
      });
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
                  >
                    <div className="archive-row-actions">
                      <span>
                        <strong>#{s.id}</strong> — {formatDateTime(s.started_at)}
                      </span>
                      {statusBadge(s.status)}
                      <Button type="button" variant="secondary" onClick={() => onContinueSession(s)}>
                        Fortsetzen
                      </Button>
                      <div className="archive-row-actions__delete">
                        {pendingDelete?.type === "session" && pendingDelete?.id === s.id ? (
                          <div className="archive-delete-confirm">
                            <span className="archive-delete-confirm__text">Wirklich löschen?</span>
                            <Button
                              type="button"
                              variant="danger"
                              onClick={() => onDeleteSession(s.id)}
                              disabled={deletingKey === `session-${s.id}`}
                            >
                              Ja, löschen
                            </Button>
                            <Button
                              type="button"
                              variant="secondary"
                              onClick={() => setPendingDelete(null)}
                              disabled={deletingKey === `session-${s.id}`}
                            >
                              Abbrechen
                            </Button>
                          </div>
                        ) : (
                          <Button
                            type="button"
                            variant="danger"
                            onClick={() => setPendingDelete({ type: "session", id: s.id })}
                          >
                            Löschen
                          </Button>
                        )}
                      </div>
                    </div>
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
                      <div className="archive-row-actions">
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
                        <div className="archive-row-actions__delete">
                          {pendingDelete?.type === "submission" && pendingDelete?.id === sub.id ? (
                            <div className="archive-delete-confirm">
                              <span className="archive-delete-confirm__text">Wirklich löschen?</span>
                              <Button
                                type="button"
                                variant="danger"
                                onClick={() => onDeleteSubmission(sub.id)}
                                disabled={deletingKey === `submission-${sub.id}`}
                              >
                                Ja, löschen
                              </Button>
                              <Button
                                type="button"
                                variant="secondary"
                                onClick={() => setPendingDelete(null)}
                                disabled={deletingKey === `submission-${sub.id}`}
                              >
                                Abbrechen
                              </Button>
                            </div>
                          ) : (
                            <Button
                              type="button"
                              variant="danger"
                              onClick={() => setPendingDelete({ type: "submission", id: sub.id })}
                            >
                              Löschen
                            </Button>
                          )}
                        </div>
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
