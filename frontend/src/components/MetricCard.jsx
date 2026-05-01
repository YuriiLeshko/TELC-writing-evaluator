export default function MetricCard({ label, value, helperText }) {
  return (
    <div className="metric-card">
      <div className="metric-card__label">{label}</div>
      <div className="metric-card__value">{value ?? "—"}</div>
      {helperText ? <div className="metric-card__help">{helperText}</div> : null}
    </div>
  );
}
