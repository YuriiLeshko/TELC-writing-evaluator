import { useCallback, useEffect, useRef, useState } from "react";
import { PanelRightClose, PanelRightOpen, X } from "lucide-react";
import ErrorHighlightedText from "./ErrorHighlightedText.jsx";
import Badge from "./Badge.jsx";
import { safeGet } from "../utils/safeGet.js";

const RAIL_SECTION_IDS = ["rail-section-score", "rail-section-i", "rail-section-ii", "rail-section-iii", "rail-section-errors"];

const ERR_PREVIEW_MAX = 8;

export default function ResultView({ result, candidateText, selectedTask }) {
  const [railCollapsed, setRailCollapsed] = useState(false);
  const [railMobileOpen, setRailMobileOpen] = useState(false);
  const [activeSection, setActiveSection] = useState(RAIL_SECTION_IDS[0]);
  const [pendingScrollId, setPendingScrollId] = useState(null);
  const railTilesRef = useRef(null);

  const [layoutWide, setLayoutWide] = useState(
    () => typeof window !== "undefined" && window.matchMedia("(min-width: 1201px)").matches,
  );

  useEffect(() => {
    const mq = window.matchMedia("(min-width: 1201px)");
    const onChange = () => setLayoutWide(mq.matches);
    onChange();
    mq.addEventListener("change", onChange);
    return () => mq.removeEventListener("change", onChange);
  }, []);

  const railBodyVisible = (!railCollapsed && layoutWide) || (!layoutWide && railMobileOpen);

  const r = result && typeof result === "object" ? result : {};
  const crit3 = r.criterion_III || {};
  const highlighted = crit3.highlighted_errors || [];
  const expectedKeyPoints = Array.isArray(selectedTask?.expected_key_points) ? selectedTask.expected_key_points : [];

  const wc = r.word_count;
  const improved = r.improved_text;

  const errorCount = Array.isArray(highlighted) ? highlighted.length : 0;
  const gradeI = safeGet(r, "criterion_I.grade");
  const ptsI = safeGet(r, "criterion_I.points");
  const gradeII = safeGet(r, "criterion_II.grade");
  const ptsII = safeGet(r, "criterion_II.points");
  const gradeIII = safeGet(r, "criterion_III.grade");
  const ptsIII = safeGet(r, "criterion_III.points");
  const commentI = safeGet(r, "criterion_I.comment");
  const commentII = safeGet(r, "criterion_II.comment");
  const commentIII = safeGet(r, "criterion_III.comment");

  const scrollRailTo = useCallback((id) => {
    const root = railTilesRef.current;
    const el = root?.querySelector(`#${id}`) ?? null;
    el?.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }, []);

  const onTileActivate = useCallback(
    (id) => {
      if (!layoutWide && !railMobileOpen) {
        setPendingScrollId(id);
        setRailMobileOpen(true);
        return;
      }
      if (railCollapsed) {
        setPendingScrollId(id);
        setRailCollapsed(false);
        return;
      }
      scrollRailTo(id);
    },
    [layoutWide, railMobileOpen, railCollapsed, scrollRailTo],
  );

  useEffect(() => {
    if (!pendingScrollId || !railBodyVisible) return undefined;
    const id = pendingScrollId;
    let cancelled = false;
    const t = window.setTimeout(() => {
      if (cancelled) return;
      scrollRailTo(id);
      setPendingScrollId(null);
    }, 0);
    return () => {
      cancelled = true;
      window.clearTimeout(t);
    };
  }, [pendingScrollId, railBodyVisible, scrollRailTo]);

  useEffect(() => {
    const root = railTilesRef.current;
    if (!root) return undefined;

    const elements = RAIL_SECTION_IDS.map((id) => root.querySelector(`#${id}`)).filter(Boolean);
    if (!elements.length) return undefined;

    const observer = new IntersectionObserver(
      (entries) => {
        const visible = entries
          .filter((e) => e.isIntersecting)
          .sort((a, b) => b.intersectionRatio - a.intersectionRatio);
        const id = visible[0]?.target?.id;
        if (id) setActiveSection(id);
      },
      { root, rootMargin: "-5% 0px -40% 0px", threshold: [0, 0.1, 0.25, 0.5, 0.75, 1] },
    );

    elements.forEach((el) => observer.observe(el));
    return () => observer.disconnect();
  }, [result, railBodyVisible]);

  const railAsideCls = [
    "result-rail-sidebar",
    railCollapsed ? "result-rail-sidebar--collapsed" : "",
    railMobileOpen ? "result-rail-sidebar--mobile-open" : "",
  ]
    .filter(Boolean)
    .join(" ");

  const fmtGradePts = (g, p) => {
    const gStr = g != null && g !== "" ? String(g) : "—";
    const pStr = p ?? "—";
    return `${gStr} · ${pStr}`;
  };

  const formatErrLine = (err) =>
    typeof err === "object" ? `${err.text || "?"} — ${err.error_type || ""}: ${err.explanation || ""}` : String(err);

  const errPreview = Array.isArray(highlighted) ? highlighted.slice(0, ERR_PREVIEW_MAX) : [];
  const errMore = Math.max(0, (highlighted?.length ?? 0) - ERR_PREVIEW_MAX);

  const criterionBody = (subtitle, grade, pts, comment) => (
    <div className="result-rail-card__body">
      {subtitle ? (
        <p className="metric-card__help" style={{ margin: "0 0 0.4rem" }}>
          {subtitle}
        </p>
      ) : null}
      <p style={{ margin: 0, fontSize: "0.86rem" }}>
        <strong>Note:</strong> {grade ?? "—"} &nbsp;|&nbsp; <strong>Punkte:</strong> {pts ?? "—"}
      </p>
      <p style={{ margin: "0.45rem 0 0", color: "var(--muted)", fontSize: "0.86rem", lineHeight: 1.45 }}>
        {comment || "Keine Details."}
      </p>
    </div>
  );

  return (
    <div
      className="result-layout"
      style={{
        "--result-rail-width": railCollapsed ? "64px" : "280px",
      }}
    >
      {railMobileOpen ? (
        <button
          type="button"
          className="result-rail-backdrop"
          onClick={() => setRailMobileOpen(false)}
          aria-label="Ergebnisanalyse schließen"
        />
      ) : null}

      <div className="result-page-shell">
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
      </div>

      <aside className={railAsideCls} aria-label="Ergebnisanalyse">
        <button
          type="button"
          className="result-rail-mobile-toggle"
          onClick={() => setRailMobileOpen(true)}
          aria-label="Ergebnisanalyse öffnen"
        >
          <PanelRightOpen size={20} aria-hidden />
        </button>
        <button
          type="button"
          className="sidebar__collapse"
          onClick={() => setRailCollapsed((v) => !v)}
          aria-label={railCollapsed ? "Analyse-Leiste erweitern" : "Analyse-Leiste einklappen"}
        >
          {railCollapsed ? <PanelRightOpen size={18} aria-hidden /> : <PanelRightClose size={18} aria-hidden />}
        </button>
        <button
          type="button"
          className="result-rail-sidebar__close-mobile"
          onClick={() => setRailMobileOpen(false)}
          aria-label="Ergebnisanalyse schließen"
        >
          <X size={18} aria-hidden />
        </button>

        <div ref={railTilesRef} className="result-rail-sidebar__tiles">
          <div
            id="rail-section-score"
            className={`result-rail-card ${activeSection === "rail-section-score" ? "result-rail-card--active" : ""}`}
          >
            <button
              type="button"
              className="result-rail-card__head"
              onClick={() => onTileActivate("rail-section-score")}
            >
              <span className="result-rail-tile__title">Endnote</span>
              <span className="result-rail-tile__value">
                {r.final_score ?? "—"}/{r.max_score ?? "—"}
              </span>
            </button>
            {railBodyVisible ? (
              <div className="result-rail-card__body">
                <p style={{ margin: "0.15rem 0", fontSize: "0.84rem" }}>
                  <strong>Rohpunkte:</strong> {r.raw_score ?? "—"}
                </p>
                <p style={{ margin: "0.15rem 0", fontSize: "0.84rem" }}>
                  <strong>Wortanzahl:</strong> {wc?.value ?? "—"}
                  {wc?.minimum_required != null ? ` (Min. ${wc.minimum_required})` : ""}
                </p>
                <p style={{ margin: "0.15rem 0", fontSize: "0.84rem" }}>
                  <strong>Topic mismatch:</strong> {String(r.topic_mismatch ?? "—")}
                </p>
                <p style={{ margin: "0.15rem 0", fontSize: "0.84rem" }}>
                  <strong>Situation mismatch:</strong> {String(r.situation_mismatch ?? "—")}
                </p>
                <div className="row" style={{ gap: "0.3rem", marginTop: "0.35rem" }}>
                  {r.topic_mismatch ? <Badge variant="warning">Themenabweichung</Badge> : null}
                  {r.situation_mismatch ? <Badge variant="warning">Situationsabweichung</Badge> : null}
                  {wc && wc.meets_requirement === true ? <Badge variant="success">Wortanzahl erfüllt</Badge> : null}
                  {wc && wc.meets_requirement === false ? <Badge variant="warning">Wortanzahl zu kurz</Badge> : null}
                </div>
              </div>
            ) : null}
          </div>

          <div
            id="rail-section-i"
            className={`result-rail-card ${activeSection === "rail-section-i" ? "result-rail-card--active" : ""}`}
          >
            <button type="button" className="result-rail-card__head" onClick={() => onTileActivate("rail-section-i")}>
              <span className="result-rail-tile__title">Kriterium I</span>
              <span className="result-rail-tile__value">{fmtGradePts(gradeI, ptsI)}</span>
            </button>
            {railBodyVisible ? criterionBody("Task Achievement", gradeI, ptsI, commentI) : null}
          </div>

          <div
            id="rail-section-ii"
            className={`result-rail-card ${activeSection === "rail-section-ii" ? "result-rail-card--active" : ""}`}
          >
            <button type="button" className="result-rail-card__head" onClick={() => onTileActivate("rail-section-ii")}>
              <span className="result-rail-tile__title">Kriterium II</span>
              <span className="result-rail-tile__value">{fmtGradePts(gradeII, ptsII)}</span>
            </button>
            {railBodyVisible ? criterionBody("Communicative Design", gradeII, ptsII, commentII) : null}
          </div>

          <div
            id="rail-section-iii"
            className={`result-rail-card ${activeSection === "rail-section-iii" ? "result-rail-card--active" : ""}`}
          >
            <button
              type="button"
              className="result-rail-card__head"
              onClick={() => onTileActivate("rail-section-iii")}
            >
              <span className="result-rail-tile__title">Kriterium III</span>
              <span className="result-rail-tile__value">{fmtGradePts(gradeIII, ptsIII)}</span>
            </button>
            {railBodyVisible ? criterionBody("Formal Accuracy", gradeIII, ptsIII, commentIII) : null}
          </div>

          <div
            id="rail-section-errors"
            className={`result-rail-card ${activeSection === "rail-section-errors" ? "result-rail-card--active" : ""}`}
          >
            <button
              type="button"
              className="result-rail-card__head"
              onClick={() => onTileActivate("rail-section-errors")}
            >
              <span className="result-rail-tile__title">Fehler</span>
              <span className="result-rail-tile__value">{errorCount}</span>
            </button>
            {railBodyVisible ? (
              <div className="result-rail-card__body">
                {errPreview.length ? (
                  <>
                    <ul className="analysis-errors-list result-rail-card__err-list">
                      {errPreview.map((err, i) => (
                        <li key={i}>{formatErrLine(err)}</li>
                      ))}
                    </ul>
                    {errMore > 0 ? (
                      <p className="metric-card__help" style={{ margin: "0.35rem 0 0" }}>
                        +{errMore} weitere
                      </p>
                    ) : null}
                  </>
                ) : (
                  <p className="metric-card__help" style={{ margin: 0 }}>
                    Keine markierten Fehler.
                  </p>
                )}
              </div>
            ) : null}
          </div>
        </div>
      </aside>
    </div>
  );
}
