const gradeClass = {
  A: "criterion-card--a",
  B: "criterion-card--b",
  C: "criterion-card--c",
  D: "criterion-card--d",
};

export default function CriterionCard({ title, subtitle, grade, points, comment, useTone = true }) {
  const g = grade && String(grade).toUpperCase();
  const tone = useTone ? gradeClass[g] || "" : "";
  return (
    <div className={`criterion-card ${tone}`.trim()}>
      <div className="criterion-card__title">{title}</div>
      {subtitle ? <div className="metric-card__help" style={{ marginBottom: "0.35rem" }}>{subtitle}</div> : null}
      <div>
        <strong>Stufe:</strong> {grade ?? "—"} &nbsp;|&nbsp; <strong>Punkte:</strong> {points ?? "—"}
      </div>
      <p style={{ margin: "0.5rem 0 0", color: "var(--muted)", fontSize: "0.92rem" }}>
        {comment || "Keine Details."}
      </p>
    </div>
  );
}
