import Card from "./Card.jsx";
import Button from "./Button.jsx";
import Badge from "./Badge.jsx";

export default function TaskCard({
  label,
  taskType,
  sourceText,
  situationText,
  instructionText,
  expectedKeyPoints,
  selected,
  onSelect,
  selectionLocked,
  showConfirm,
  onConfirm,
  confirmDisabled,
  lockedSelected,
}) {
  return (
    <Card
      className={`task-card ${selected ? "task-card-selected" : ""}`.trim()}
      title={(
        <span className="task-card__header">
          {label}
          <Badge variant={selected ? "success" : "neutral"}>{taskType === "info" ? "Info" : "Beschwerde"}</Badge>
        </span>
      )}
    >
      <div className="task-card__doc">
        <section className="task-card__section">
          <h3 className="task-card__section-title">Situation</h3>
          <p className="task-card__body">{situationText || "—"}</p>
        </section>
        <section className="task-card__section">
          <h3 className="task-card__section-title">Aufgabe</h3>
          <p className="task-card__body">{sourceText || "—"}</p>
        </section>
        <section className="task-card__section">
          <h3 className="task-card__section-title">Ihre Aufgabe</h3>
          <p className="task-card__body">{instructionText || "—"}</p>
        </section>
        <section className="task-card__section">
          <h3 className="task-card__section-title">Mögliche Punkte / Erwartete Schwerpunkte</h3>
          {Array.isArray(expectedKeyPoints) && expectedKeyPoints.length ? (
            <ul className="task-card__points">
              {expectedKeyPoints.map((point, idx) => (
                <li key={`${taskType}-${idx}`}>{point}</li>
              ))}
            </ul>
          ) : (
            <p className="task-card__body">—</p>
          )}
        </section>
      </div>
      {lockedSelected ? (
        <p className="metric-card__help" style={{ marginTop: "0.65rem" }}>
          Diese Aufgabe ist für diese Sitzung festgelegt.
        </p>
      ) : null}
      {!selectionLocked ? (
        <div className="row" style={{ marginTop: "0.75rem" }}>
          {selected ? (
            <p className="task-card__selected-note">Ausgewählt</p>
          ) : (
            <Button type="button" variant="secondary" onClick={() => onSelect?.(taskType)}>
              Diese Aufgabe wählen
            </Button>
          )}
        </div>
      ) : null}
      {showConfirm && selected && !selectionLocked ? (
        <div className="row" style={{ marginTop: "0.65rem" }}>
          <Button type="button" variant="primary" onClick={onConfirm} disabled={confirmDisabled}>
            Auswahl bestätigen
          </Button>
        </div>
      ) : null}
    </Card>
  );
}
