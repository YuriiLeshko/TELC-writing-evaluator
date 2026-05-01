import { useEffect, useState } from "react";
import Card from "../components/Card.jsx";
import MetricCard from "../components/MetricCard.jsx";
import LoadingState from "../components/LoadingState.jsx";
import { getCurrentUser } from "../api/client.js";

export default function ProfilePage() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      setError(null);
      setLoading(true);
      try {
        const u = await getCurrentUser();
        if (!cancelled) setUser(u);
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : String(e));
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div className="stack">
      <h1 className="page-title">Profil</h1>
      {error ? <div className="alert alert--error">{error}</div> : null}
      {loading ? <LoadingState /> : null}
      {!loading && user ? (
        <Card title="Demo-Benutzer">
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))",
              gap: "0.65rem",
            }}
          >
            <MetricCard label="E-Mail" value={user.email} />
            <MetricCard label="Benutzername" value={user.username ?? "—"} />
            <MetricCard label="Rolle" value={user.role} />
            <MetricCard label="Aktiv" value={user.is_active ? "Ja" : "Nein"} />
            <MetricCard label="Verfügbare Sitzungen" value={user.available_sessions} />
            <MetricCard label="Verfügbare Einreichungen" value={user.available_submissions} />
            <MetricCard label="Nächster Info-Task" value={user.next_info_task_index} />
            <MetricCard label="Nächster Beschwerde-Task" value={user.next_complaint_task_index} />
          </div>
        </Card>
      ) : null}
    </div>
  );
}
