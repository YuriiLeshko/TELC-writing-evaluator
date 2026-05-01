import CriterionCard from "./CriterionCard.jsx";
import ErrorHighlightedText from "./ErrorHighlightedText.jsx";
import Badge from "./Badge.jsx";
import { safeGet } from "../utils/safeGet.js";

export default function ResultView({ result, candidateText, selectedTask }) {
  const r = result && typeof result === "object" ? result : {};
  const crit3 = r.criterion_III || {};
  const highlighted = crit3.highlighted_errors || [];

  const wc = r.word_count;
  const improved = r.improved_text;

  return (
    <div className="stack">
      <section className="card">
        <h2 className="card__title">Gesamtergebnis</h2>
        <p style={{ margin: "0.25rem 0" }}>
          <strong>Endnote (skaliert):</strong> {r.final_score ?? "—"} / {r.max_score ?? "—"}
        </p>
        <p style={{ margin: "0.25rem 0" }}>
          <strong>Rohpunkte:</strong> {r.raw_score ?? "—"}
        </p>
        <div className="row" style={{ marginTop: "0.5rem", gap: "0.35rem" }}>
          {r.topic_mismatch ? <Badge variant="warning">Themenabweichung</Badge> : null}
          {r.situation_mismatch ? <Badge variant="warning">Situationsabweichung</Badge> : null}
        </div>
      </section>

      <section>
        <h3 className="card__title" style={{ marginBottom: "0.5rem" }}>
          Kriterien
        </h3>
        <CriterionCard
          title="Kriterium I"
          subtitle="Task Achievement"
          grade={safeGet(r, "criterion_I.grade")}
          points={safeGet(r, "criterion_I.points")}
          comment={safeGet(r, "criterion_I.comment")}
        />
        <CriterionCard
          title="Kriterium II"
          subtitle="Communicative Design"
          grade={safeGet(r, "criterion_II.grade")}
          points={safeGet(r, "criterion_II.points")}
          comment={safeGet(r, "criterion_II.comment")}
        />
        <CriterionCard
          title="Kriterium III"
          subtitle="Formal Accuracy"
          grade={safeGet(r, "criterion_III.grade")}
          points={safeGet(r, "criterion_III.points")}
          comment={safeGet(r, "criterion_III.comment")}
        />
      </section>

      <section className="card">
        <h2 className="card__title">Wortanzahl</h2>
        {wc ? (
          <>
            <p style={{ margin: "0.25rem 0" }}>
              <strong>Anzahl:</strong> {wc.value ?? "—"}
            </p>
            <p style={{ margin: "0.25rem 0" }}>
              <strong>Minimum:</strong> {wc.minimum_required ?? "—"}
            </p>
            <p style={{ margin: "0.25rem 0" }}>
              <strong>Anforderung erfüllt:</strong>{" "}
              {wc.meets_requirement ? (
                <Badge variant="success">Ja</Badge>
              ) : (
                <Badge variant="warning">Nein</Badge>
              )}
            </p>
          </>
        ) : (
          <p className="metric-card__help">Keine Wortanzahl-Daten.</p>
        )}
      </section>

      <section className="card">
        <h2 className="card__title">Ihre Antwort (Grammatik-Hervorhebungen)</h2>
        <ErrorHighlightedText text={candidateText || ""} highlightedErrors={highlighted} />
      </section>

      <details className="summary-block">
        <summary>Aufgabentext anzeigen</summary>
        <div className="stack stack--sm" style={{ marginTop: "0.65rem" }}>
          <div>
            <strong>Ausgangstext</strong>
            <div className="text-panel" style={{ marginTop: "0.35rem" }}>
              {selectedTask?.source_text || "—"}
            </div>
          </div>
          <div>
            <strong>Situation</strong>
            <div className="text-panel" style={{ marginTop: "0.35rem" }}>
              {selectedTask?.situation_text || "—"}
            </div>
          </div>
          <div>
            <strong>Aufgabenstellung</strong>
            <div className="text-panel" style={{ marginTop: "0.35rem" }}>
              {selectedTask?.instruction_text || "—"}
            </div>
          </div>
        </div>
      </details>

      <details className="summary-block">
        <summary>Verbesserte Version anzeigen</summary>
        {improved ? (
          <div className="stack stack--sm" style={{ marginTop: "0.65rem" }}>
            <div className="text-panel">{improved.improved_text || "—"}</div>
            {Array.isArray(improved.changes_summary) && improved.changes_summary.length ? (
              <ul style={{ margin: 0, paddingLeft: "1.2rem" }}>
                {improved.changes_summary.map((line, i) => (
                  <li key={i}>{line}</li>
                ))}
              </ul>
            ) : (
              <p className="metric-card__help">Keine Änderungszusammenfassung.</p>
            )}
          </div>
        ) : (
          <p className="metric-card__help" style={{ marginTop: "0.5rem" }}>
            Keine verbesserte Version vorhanden.
          </p>
        )}
      </details>

      <details className="summary-block">
        <summary>Analyse-Details anzeigen</summary>
        <div className="stack stack--sm" style={{ marginTop: "0.65rem", fontSize: "0.9rem" }}>
          <div>
            <strong>topic_mismatch:</strong> {String(r.topic_mismatch ?? "—")}
          </div>
          <div>
            <strong>situation_mismatch:</strong> {String(r.situation_mismatch ?? "—")}
          </div>
          <div>
            <strong>highlighted_errors (Liste)</strong>
            {Array.isArray(highlighted) && highlighted.length ? (
              <ul>
                {highlighted.map((err, i) => (
                  <li key={i}>
                    {typeof err === "object"
                      ? `${err.text || "?"} — ${err.error_type || ""}: ${err.explanation || ""}`
                      : String(err)}
                  </li>
                ))}
              </ul>
            ) : (
              <span className="metric-card__help"> Keine Einträge</span>
            )}
          </div>
          <p className="metric-card__help">
            Weitere technische Felder können in späteren Versionen ergänzt werden. Rohdaten siehe ggf. Archiv.
          </p>
        </div>
      </details>
    </div>
  );
}
