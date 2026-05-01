import { useCallback, useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { BookOpen, Loader2, PenLine } from "lucide-react";
import Card from "../components/Card.jsx";
import Button from "../components/Button.jsx";
import Textarea from "../components/Textarea.jsx";
import TaskCard from "../components/TaskCard.jsx";
import Timer from "../components/Timer.jsx";
import LoadingState from "../components/LoadingState.jsx";
import Badge from "../components/Badge.jsx";
import { startTaskSession, submitEvaluation } from "../api/client.js";
import { countWords } from "../utils/text.js";

const EVALUATION_STAGES = [
  "Ihr Text wird an den Server gesendet …",
  "Die Bewertung prüft Inhalt und Aufgabenerfüllung …",
  "Kommunikativer Aufbau und Stil werden analysiert …",
  "Sprachliche Genauigkeit und Grammatik werden geprüft …",
  "Vorschläge zur Verbesserung werden erstellt …",
];

export default function TrainingPage() {
  const navigate = useNavigate();
  const scrollRef = useRef(null);
  const panelARef = useRef(null);
  const panelBRef = useRef(null);

  const [currentSession, setCurrentSession] = useState(null);
  const [displayTitle, setDisplayTitle] = useState("");
  const [startedAt, setStartedAt] = useState(null);
  const [selectedTaskType, setSelectedTaskType] = useState(null);
  const [selectionConfirmed, setSelectionConfirmed] = useState(false);
  const [candidateText, setCandidateText] = useState("");
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [evalStageIndex, setEvalStageIndex] = useState(0);
  const [error, setError] = useState(null);
  const [mobileTab, setMobileTab] = useState("info");

  useEffect(() => {
    if (!submitting) {
      setEvalStageIndex(0);
      return undefined;
    }
    const id = setInterval(() => {
      setEvalStageIndex((i) => (i + 1) % EVALUATION_STAGES.length);
    }, 2800);
    return () => clearInterval(id);
  }, [submitting]);

  const start = useCallback(async () => {
    setError(null);
    setLoading(true);
    try {
      const data = await startTaskSession();
      const session = data?.session;
      setCurrentSession(session);
      setDisplayTitle(data?.display_title || "");
      setStartedAt(session?.started_at || null);
      setSelectedTaskType(null);
      setSelectionConfirmed(false);
      setCandidateText("");
      setMobileTab("info");
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  }, []);

  const onConfirmSelection = () => {
    setSelectionConfirmed(true);
  };

  const onSubmit = async () => {
    setError(null);
    const trimmed = (candidateText || "").trim();
    if (!trimmed) {
      setError("Bitte geben Sie einen Text ein.");
      return;
    }
    if (!currentSession?.id || !selectedTaskType) {
      setError("Sitzung oder Aufgabe fehlt.");
      return;
    }
    setSubmitting(true);
    try {
      const data = await submitEvaluation({
        task_session_id: currentSession.id,
        selected_task_type: selectedTaskType,
        candidate_text: candidateText,
      });
      const task =
        selectedTaskType === "info" ? currentSession.info_task : currentSession.complaint_task;
      navigate("/result", {
        replace: false,
        state: {
          result: data?.result ?? {},
          candidateText,
          session: currentSession,
          selectedTaskType,
          selectedTask: task,
          submissionId: data?.submission_id,
        },
      });
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setSubmitting(false);
    }
  };

  const scrollToPanel = (type) => {
    const el = type === "info" ? panelARef.current : panelBRef.current;
    el?.scrollIntoView({ behavior: "smooth", inline: "nearest", block: "nearest" });
  };

  const words = countWords(candidateText);
  const showWordWarn = words > 0 && words < 150;

  const infoTask = currentSession?.info_task;
  const complaintTask = currentSession?.complaint_task;
  const selectionLocked = selectionConfirmed;
  const showInfoCard = !selectionLocked || selectedTaskType === "info";
  const showComplaintCard = !selectionLocked || selectedTaskType === "complaint";

  return (
    <div className="stack">
      <h1 className="page-title">Training</h1>
      <p className="page-subtitle">
        Starten Sie eine neue Einheit, wählen Sie eine Aufgabe und schreiben Sie Ihren Text. Der Timer läuft ab
        Sitzungsbeginn (30 Minuten Zielspanne).
      </p>

      <Card title="Was erwartet Sie?">
        <div className="stack stack--sm" style={{ color: "var(--muted)", fontSize: "0.93rem" }}>
          <p style={{ margin: 0 }}>
            Sie erhalten zwei Aufgaben:
            <br />
            <strong>Aufgabe A:</strong> Informations-/Anfrageschreiben
            <br />
            <strong>Aufgabe B:</strong> Beschwerdeschreiben
          </p>
          <p style={{ margin: 0 }}>
            Sie wählen eine der beiden Aufgaben aus. Der Timer startet sofort beim Beginn der Sitzung; die Zielzeit
            beträgt 30 Minuten.
          </p>
          <p style={{ margin: 0 }}>
            Ihr Text sollte mindestens 150 Wörter enthalten. Nach der Einreichung sehen Sie Punktzahl,
            Kriterien-Kommentare, Wortanzahl, markierte Grammatikstellen und eine verbesserte Textversion.
          </p>
        </div>
      </Card>

      {error ? (
        <div className="alert alert--error" role="alert">
          {error}
        </div>
      ) : null}

      {!currentSession ? (
        <Card className="start-training-card">
          {loading ? <LoadingState message="Sitzung wird gestartet…" /> : null}
          <Button type="button" variant="primary" onClick={start} disabled={loading}>
            Neue Trainingseinheit starten
          </Button>
        </Card>
      ) : (
        <>
          <Card title={displayTitle || "Aktive Sitzung"}>
            <div className="row" style={{ justifyContent: "space-between", alignItems: "center" }}>
              <Timer startedAt={startedAt} />
              <Badge variant="neutral">Session #{currentSession.id}</Badge>
            </div>
          </Card>

          <div className="task-tabs task-tabs--mobile">
            <button
              type="button"
              className={`task-tabs__btn ${mobileTab === "info" ? "task-tabs__btn--active" : ""}`.trim()}
              onClick={() => {
                setMobileTab("info");
                scrollToPanel("info");
              }}
            >
              Aufgabe A (Info)
            </button>
            <button
              type="button"
              className={`task-tabs__btn ${mobileTab === "complaint" ? "task-tabs__btn--active" : ""}`.trim()}
              onClick={() => {
                setMobileTab("complaint");
                scrollToPanel("complaint");
              }}
            >
              Aufgabe B (Beschwerde)
            </button>
          </div>

          <div ref={scrollRef} className="task-scroll">
            {showInfoCard ? (
              <div ref={panelARef} className="task-scroll__panel">
                <TaskCard
                  label="Aufgabe A"
                  taskType="info"
                  sourceText={infoTask?.source_text}
                  situationText={infoTask?.situation_text}
                  instructionText={infoTask?.instruction_text}
                  expectedKeyPoints={infoTask?.expected_key_points}
                  selected={selectedTaskType === "info"}
                  onSelect={() => setSelectedTaskType("info")}
                  selectionLocked={selectionLocked}
                  lockedSelected={selectionLocked && selectedTaskType === "info"}
                  showConfirm={selectedTaskType === "info"}
                  onConfirm={onConfirmSelection}
                  confirmDisabled={false}
                />
              </div>
            ) : null}
            {showComplaintCard ? (
              <div ref={panelBRef} className="task-scroll__panel">
                <TaskCard
                  label="Aufgabe B"
                  taskType="complaint"
                  sourceText={complaintTask?.source_text}
                  situationText={complaintTask?.situation_text}
                  instructionText={complaintTask?.instruction_text}
                  expectedKeyPoints={complaintTask?.expected_key_points}
                  selected={selectedTaskType === "complaint"}
                  onSelect={() => setSelectedTaskType("complaint")}
                  selectionLocked={selectionLocked}
                  lockedSelected={selectionLocked && selectedTaskType === "complaint"}
                  showConfirm={selectedTaskType === "complaint"}
                  onConfirm={onConfirmSelection}
                  confirmDisabled={false}
                />
              </div>
            ) : null}
          </div>

          {selectionLocked ? (
            <p className="metric-card__help">
              Die Auswahl ist bestätigt. Der Timer läuft seit Beginn der Sitzung.
            </p>
          ) : null}

          {selectionLocked ? (
            <Card title="Ihre Antwort">
              <Textarea
                rows={12}
                mono
                value={candidateText}
                onChange={(e) => setCandidateText(e.target.value)}
                placeholder="Schreiben Sie hier Ihren Text…"
                disabled={submitting}
              />
              <p style={{ margin: "0.5rem 0" }}>
                <strong>Wörter:</strong> {words}
              </p>
              {showWordWarn ? (
                <div className="alert alert--warn" role="status">
                  Weniger als 150 Wörter — Sie können trotzdem einreichen; die Endbewertung erfolgt serverseitig.
                </div>
              ) : null}
              <div className="row row--end" style={{ marginTop: "0.75rem" }}>
                <Button type="button" variant="primary" onClick={onSubmit} disabled={submitting}>
                  {submitting ? "Wird bewertet…" : "Einreichen & bewerten"}
                </Button>
              </div>
              {submitting ? (
                <div className="evaluation-progress" role="status" aria-live="polite" aria-busy="true">
                  <div className="evaluation-progress__visual">
                    <Loader2 className="evaluation-progress__spinner" size={28} aria-hidden />
                    <div className="evaluation-progress__scene" aria-hidden>
                      <div className="evaluation-progress__reader">
                        <span className="evaluation-progress__reader-head" />
                        <BookOpen className="evaluation-progress__book" size={22} />
                        <PenLine className="evaluation-progress__pen" size={16} />
                      </div>
                    </div>
                  </div>
                  <p className="evaluation-progress__text">{EVALUATION_STAGES[evalStageIndex]}</p>
                  <p className="evaluation-progress__hint">
                    Die Bewertung kann einige Sekunden dauern — die Seite reagiert noch.
                  </p>
                </div>
              ) : null}
            </Card>
          ) : (
            <Card>
              <p className="metric-card__help" style={{ margin: 0 }}>
                Bestätigen Sie zuerst eine Aufgabe, um den Schreibbereich freizuschalten.
              </p>
            </Card>
          )}
        </>
      )}
    </div>
  );
}
