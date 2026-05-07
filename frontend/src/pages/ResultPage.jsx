import { Link, useLocation } from "react-router-dom";
import ResultView from "../components/ResultView.jsx";

export default function ResultPage() {
  const location = useLocation();
  const state = location.state || {};
  const { result, candidateText, session, selectedTaskType, selectedTask, submission } = state;

  const task =
    selectedTask ||
    (session && selectedTaskType === "info"
      ? session.info_task
      : session && selectedTaskType === "complaint"
        ? session.complaint_task
        : null);

  const hasResult = result && typeof result === "object" && Object.keys(result).length > 0;

  if (!hasResult) {
    return (
      <div className="stack">
        <h1 className="page-title">Ergebnis</h1>
        <div className="card">
          <p>
            Kein Ergebnis ausgewählt. Bitte öffnen Sie ein Ergebnis aus dem Archiv oder starten Sie ein Training.
          </p>
          <div className="row" style={{ marginTop: "0.75rem", flexWrap: "wrap", gap: "0.5rem" }}>
            <Link to="/archive" className="btn btn--secondary link-btn">
              Zum Archiv
            </Link>
            <Link to="/training" className="btn btn--primary link-btn">
              Zum Training
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="stack">
      <h1 className="page-title">Ergebnis</h1>
      <ResultView result={result} candidateText={candidateText || ""} selectedTask={task} submission={submission} />
    </div>
  );
}
