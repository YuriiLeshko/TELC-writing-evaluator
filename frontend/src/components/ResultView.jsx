import { useState } from "react";
import CriterionCard from "./CriterionCard.jsx";
import ErrorHighlightedText from "./ErrorHighlightedText.jsx";
import Badge from "./Badge.jsx";
import { safeGet } from "../utils/safeGet.js";

function toGradeLetter(value) {
  const letter = (value && String(value).trim().toUpperCase()) || "—";
  return ["A", "B", "C", "D"].includes(letter) ? letter : "—";
}

function gradeToneClass(letter) {
  if (letter === "A") return "result-grade-chip--a";
  if (letter === "B") return "result-grade-chip--b";
  if (letter === "C" || letter === "D") return "result-grade-chip--cd";
  return "result-grade-chip--neutral";
}

function scoreToneClass(finalScore, maxScore) {
  const finalNum = Number(finalScore);
  const maxNum = Number(maxScore);
  if (!Number.isFinite(finalNum) || !Number.isFinite(maxNum) || maxNum <= 0) {
    return "result-score-chip--neutral";
  }
  const ratio = (finalNum / maxNum) * 100;
  if (ratio > 80) return "result-score-chip--good";
  if (ratio >= 60) return "result-score-chip--mid";
  return "result-score-chip--low";
}

export default function ResultView({ result, candidateText, selectedTask }) {
  const [analysisOpen, setAnalysisOpen] = useState(false);
  const r = result && typeof result === "object" ? result : {};
  const crit3 = r.criterion_III || {};
  const highlighted = crit3.highlighted_errors || [];
  const expectedKeyPoints = Array.isArray(selectedTask?.expected_key_points) ? selectedTask.expected_key_points : [];
  const critI = toGradeLetter(safeGet(r, "criterion_I.grade"));
  const critII = toGradeLetter(safeGet(r, "criterion_II.grade"));
  const critIII = toGradeLetter(safeGet(r, "criterion_III.grade"));

  const wc = r.word_count;
  const improved = r.improved_text;

  return (
    <div className="result-layout">
      {!analysisOpen ? (
        <button
          type="button"
          className="result-analysis-tab"
          onClick={() => setAnalysisOpen(true)}
          aria-label="Analyse öffnen"
        >
          <span className="result-analysis-tab__title">Analy</span>
          <span className={`result-score-chip ${scoreToneClass(r.final_score, r.max_score)}`}>
            {r.final_score ?? "—"}
          </span>
          <span className={`result-grade-chip ${gradeToneClass(critI)}`}>I {critI}</span>
          <span className={`result-grade-chip ${gradeToneClass(critII)}`}>II {critII}</span>
          <span className={`result-grade-chip ${gradeToneClass(critIII)}`}>III {critIII}</span>
          <span className="result-analysis-tab__errors">E {highlighted.length}</span>
        </button>
      ) : null}

      {analysisOpen ? (
        <button
          type="button"
          className="result-analysis-backdrop"
          onClick={() => setAnalysisOpen(false)}
          aria-label="Analyse schließen"
        />
      ) : null}

      <main className="result-main stack">
        <details className="summary-block result-main-card" open>
          <summary>Aufgabentext anzeigen</summary>
          <div className="stack stack--sm" style={{ marginTop: "0.65rem" }}>
            <div>
              <strong>Situation</strong>
              <div className="text-panel" style={{ marginTop: "0.35rem" }}>
                {selectedTask?.situation_text || "—"}
              </div>
            </div>
            <div>
              <strong>Aufgabe</strong>
              <div className="text-panel" style={{ marginTop: "0.35rem" }}>
                {selectedTask?.source_text || "—"}
              </div>
            </div>
            <div>
              <strong>Ihre Aufgabe</strong>
              <div className="text-panel" style={{ marginTop: "0.35rem" }}>
                {selectedTask?.instruction_text || "—"}
              </div>
            </div>
            <div>
              <strong>Mögliche Punkte / Erwartete Schwerpunkte</strong>
              <div className="text-panel" style={{ marginTop: "0.35rem" }}>
                {expectedKeyPoints.length ? (
                  <ul className="changes-list">
                    {expectedKeyPoints.map((point, index) => (
                      <li key={`kp-${index}`}>{point}</li>
                    ))}
                  </ul>
                ) : (
                  "—"
                )}
              </div>
            </div>
          </div>
        </details>

        <details className="summary-block result-main-card" open>
          <summary>Ihre Antwort</summary>
          <div style={{ marginTop: "0.65rem" }}>
            <ErrorHighlightedText text={candidateText || ""} highlightedErrors={highlighted} />
          </div>
        </details>

        <details className="summary-block result-main-card" open>
          <summary>Verbesserte Version</summary>
          <div className="stack stack--sm" style={{ marginTop: "0.65rem" }}>
            {improved ? (
              <>
                <div className="text-panel">{improved.improved_text || "—"}</div>
                {Array.isArray(improved.changes_summary) && improved.changes_summary.length ? (
                  <ul className="changes-list">
                    {improved.changes_summary.map((line, i) => (
                      <li key={i}>{line}</li>
                    ))}
                  </ul>
                ) : (
                  <p className="metric-card__help">Keine Änderungszusammenfassung.</p>
                )}
              </>
            ) : (
              <p className="metric-card__help">Keine verbesserte Version vorhanden.</p>
            )}
          </div>
        </details>
      </main>

      <aside className={`card result-analysis ${analysisOpen ? "result-analysis--open" : ""}`}>
        <div className="result-analysis__header">
          <h2 className="card__title" style={{ marginBottom: 0 }}>
            Analyse
          </h2>
          <button
            type="button"
            className="result-analysis__close"
            onClick={() => setAnalysisOpen(false)}
            aria-label="Analyse schließen"
          >
            ✕
          </button>
        </div>

        <details className="summary-block result-summary" open>
          <summary>Punkte und Abweichungen</summary>
          <div className="stack stack--sm result-summary__content">
            <p style={{ margin: "0.15rem 0" }}>
              <strong>Endnote (skaliert):</strong> {r.final_score ?? "—"} / {r.max_score ?? "—"}
            </p>
            <p style={{ margin: "0.15rem 0" }}>
              <strong>Rohpunkte:</strong> {r.raw_score ?? "—"}
            </p>
            <p style={{ margin: "0.15rem 0" }}>
              <strong>Wortanzahl:</strong> {wc?.value ?? "—"}
            </p>
            <p style={{ margin: "0.15rem 0" }}>
              <strong>Topic mismatch:</strong> {String(r.topic_mismatch ?? "—")}
            </p>
            <p style={{ margin: "0.15rem 0" }}>
              <strong>Situation mismatch:</strong> {String(r.situation_mismatch ?? "—")}
            </p>
            <div className="row" style={{ gap: "0.35rem" }}>
              {r.topic_mismatch ? <Badge variant="warning">Themenabweichung</Badge> : null}
              {r.situation_mismatch ? <Badge variant="warning">Situationsabweichung</Badge> : null}
              {wc && wc.meets_requirement === true ? <Badge variant="success">Wortanzahl erfüllt</Badge> : null}
              {wc && wc.meets_requirement === false ? <Badge variant="warning">Wortanzahl zu kurz</Badge> : null}
            </div>
          </div>
        </details>

        <details className="summary-block result-summary" open>
          <summary>Kriterien</summary>
          <div className="result-summary__content">
            <CriterionCard
              title="Kriterium I"
              subtitle="Task Achievement"
              grade={safeGet(r, "criterion_I.grade")}
              points={safeGet(r, "criterion_I.points")}
              comment={safeGet(r, "criterion_I.comment")}
              useTone={false}
            />
            <CriterionCard
              title="Kriterium II"
              subtitle="Communicative Design"
              grade={safeGet(r, "criterion_II.grade")}
              points={safeGet(r, "criterion_II.points")}
              comment={safeGet(r, "criterion_II.comment")}
              useTone={false}
            />
            <CriterionCard
              title="Kriterium III"
              subtitle="Formal Accuracy"
              grade={safeGet(r, "criterion_III.grade")}
              points={safeGet(r, "criterion_III.points")}
              comment={safeGet(r, "criterion_III.comment")}
              useTone={false}
            />
          </div>
        </details>

        <details className="summary-block result-summary">
          <summary>Markierte Fehler (Backend-Liste)</summary>
          <div className="result-summary__content">
            {Array.isArray(highlighted) && highlighted.length ? (
              <ul className="analysis-errors-list">
                {highlighted.map((err, i) => (
                  <li key={i}>
                    {typeof err === "object"
                      ? `${err.text || "?"} — ${err.error_type || ""}: ${err.explanation || ""}`
                      : String(err)}
                  </li>
                ))}
              </ul>
            ) : (
              <p className="metric-card__help">Keine markierten Fehler vorhanden.</p>
            )}
          </div>
        </details>
      </aside>
    </div>
  );
}
