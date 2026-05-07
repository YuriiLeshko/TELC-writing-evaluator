import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import Card from "../components/Card.jsx";
import Button from "../components/Button.jsx";
import LoadingState from "../components/LoadingState.jsx";
import { deleteCurrentUser, getCurrentUser, updateCurrentUser } from "../api/client.js";

export default function ProfilePage() {
  const navigate = useNavigate();
  const [user, setUser] = useState(null);
  const [form, setForm] = useState({ username: "", email: "", password: "" });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [confirmSave, setConfirmSave] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      setError(null);
      setLoading(true);
      try {
        const u = await getCurrentUser();
        if (!cancelled) {
          setUser(u);
          setForm({
            username: u?.username ?? "",
            email: u?.email ?? "",
            password: "",
          });
        }
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

  const hasProfileChanges = useMemo(() => {
    if (!user) return false;
    return (form.username ?? "") !== (user.username ?? "") || (form.email ?? "") !== (user.email ?? "") || Boolean(form.password);
  }, [form, user]);

  const requestSave = () => {
    setSuccess(null);
    setError(null);
    setConfirmDelete(false);
    setConfirmSave(true);
  };

  const cancelSave = () => {
    setConfirmSave(false);
  };

  const confirmAndSave = async () => {
    if (!user) return;
    setSaving(true);
    setError(null);
    setSuccess(null);
    try {
      const payload = {
        username: form.username,
        email: form.email,
      };
      if ((form.password || "").trim()) {
        payload.password = form.password;
      }
      const updated = await updateCurrentUser(payload);
      setUser(updated);
      setForm((prev) => ({
        ...prev,
        username: updated?.username ?? "",
        email: updated?.email ?? "",
        password: "",
      }));
      setSuccess("Profil erfolgreich aktualisiert.");
      setConfirmSave(false);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setSaving(false);
    }
  };

  const requestDelete = () => {
    setSuccess(null);
    setError(null);
    setConfirmSave(false);
    setConfirmDelete(true);
  };

  const cancelDelete = () => {
    setConfirmDelete(false);
  };

  const confirmAndDelete = async () => {
    setDeleting(true);
    setError(null);
    setSuccess(null);
    try {
      await deleteCurrentUser();
      setSuccess("Account wurde gelöscht.");
      setConfirmDelete(false);
      window.setTimeout(() => navigate("/", { replace: true }), 900);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setDeleting(false);
    }
  };

  return (
    <div className="stack">
      <h1 className="page-title">Profil</h1>
      {error ? <div className="alert alert--error">{error}</div> : null}
      {success ? <div className="alert">{success}</div> : null}
      {loading ? <LoadingState /> : null}
      {!loading && user ? (
        <>
          <Card title="Profil bearbeiten">
            <div className="profile-form">
              <label className="profile-form__label">
                Benutzername
                <input
                  type="text"
                  value={form.username}
                  onChange={(e) => setForm((prev) => ({ ...prev, username: e.target.value }))}
                  className="input-like"
                  autoComplete="username"
                />
              </label>
              <label className="profile-form__label">
                E-Mail
                <input
                  type="email"
                  value={form.email}
                  onChange={(e) => setForm((prev) => ({ ...prev, email: e.target.value }))}
                  className="input-like"
                  autoComplete="email"
                />
              </label>
              <label className="profile-form__label">
                Passwort
                <input
                  type="password"
                  value={form.password}
                  onChange={(e) => setForm((prev) => ({ ...prev, password: e.target.value }))}
                  className="input-like"
                  autoComplete="new-password"
                  placeholder="Leer lassen, um Passwort nicht zu ändern"
                />
              </label>
            </div>
            {confirmSave ? (
              <div className="profile-confirm">
                <p className="metric-card__help profile-confirm__text">Änderungen wirklich speichern?</p>
                <div className="row" style={{ marginTop: "0.45rem" }}>
                  <Button type="button" variant="primary" onClick={confirmAndSave} disabled={saving}>
                    Ja, speichern
                  </Button>
                  <Button type="button" variant="secondary" onClick={cancelSave} disabled={saving}>
                    Abbrechen
                  </Button>
                </div>
              </div>
            ) : (
              <div className="row" style={{ marginTop: "0.75rem" }}>
                <Button type="button" variant="primary" onClick={requestSave} disabled={!hasProfileChanges || saving}>
                  Änderungen speichern
                </Button>
              </div>
            )}
          </Card>
          <Card title="Account löschen" className="profile-danger-card">
            {confirmDelete ? (
              <div className="profile-confirm">
                <p className="metric-card__help profile-confirm__text">
                  Account wirklich löschen? Diese Aktion kann nicht rückgängig gemacht werden.
                </p>
                <div className="row" style={{ marginTop: "0.45rem" }}>
                  <Button type="button" variant="danger" onClick={confirmAndDelete} disabled={deleting}>
                    Ja, löschen
                  </Button>
                  <Button type="button" variant="secondary" onClick={cancelDelete} disabled={deleting}>
                    Abbrechen
                  </Button>
                </div>
              </div>
            ) : (
              <div className="row">
                <Button type="button" variant="danger" onClick={requestDelete} disabled={deleting}>
                  Account löschen
                </Button>
              </div>
            )}
          </Card>
        </>
      ) : null}
    </div>
  );
}
