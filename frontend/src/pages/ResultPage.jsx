import { Link, useLocation } from "react-router-dom";
import ResultView from "../components/ResultView.jsx";

export default function ResultPage() {
  const location = useLocation();
  const state = location.state || {};
  const { result, candidateText, session, selectedTaskType, selectedTask } = state;

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
          <p>Kein Ergebnis verfügbar. Bitte starten Sie eine Trainingseinheit.</p>
          <Link to="/training" className="btn btn--primary link-btn" style={{ marginTop: "0.75rem" }}>
            Zum Training
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="stack">
      <h1 className="page-title">Ergebnis</h1>
      <div className="row">
        <Link to="/training" className="btn btn--secondary link-btn">
          Neues Training
        </Link>
        <Link to="/archive" className="btn btn--ghost link-btn">
          Archiv
        </Link>
      </div>
      <ResultView result={result} candidateText={candidateText || ""} selectedTask={task} />
    </div>
  );
}
