import { useCallback, useEffect, useRef, useState } from "react";
import { PanelRightClose, PanelRightOpen, X } from "lucide-react";
import ErrorHighlightedText from "./ErrorHighlightedText.jsx";
import { safeGet } from "../utils/safeGet.js";

const RAIL_SECTION_IDS = ["rail-section-score", "rail-section-i", "rail-section-ii", "rail-section-iii", "rail-section-errors"];

export default function ResultView({ result, candidateText, selectedTask, submission }) {
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
  const rawExpectedKeyPoints = selectedTask?.expected_key_points;
  const normalizePointText = (value) =>
    String(value ?? "")
      .trim()
      .replace(/^\s*\d+[\).\-\s:]+/, "")
      .replace(/\s+/g, " ")
      .toLowerCase();
  const expectedKeyPoints = (() => {
    if (Array.isArray(rawExpectedKeyPoints)) {
      return rawExpectedKeyPoints
        .map((point) => String(point ?? "").trim())
        .filter(Boolean)
        .map((point) => point.replace(/^\s*\d+[\).\-\s:]+/, "").trim());
    }
    if (typeof rawExpectedKeyPoints === "string") {
      return rawExpectedKeyPoints
        .split(/\r?\n/)
        .map((line) => line.trim())
        .filter(Boolean)
        .map((line) => line.replace(/^\s*\d+[\).\-\s:]+/, "").trim());
    }
    return [];
  })();
  const expectedPointIndexByText = expectedKeyPoints.reduce((acc, point, index) => {
    const normalized = normalizePointText(point);
    if (normalized && !(normalized in acc)) acc[normalized] = index + 1;
    return acc;
  }, {});

  const wc = r.word_count;
  const improved = r.improved_text;
  const finalScore = Number(r.final_score);
  const maxScore = Number(r.max_score);
  const hasValidScoreRatio = Number.isFinite(finalScore) && Number.isFinite(maxScore) && maxScore > 0;
  const scoreRatio = hasValidScoreRatio ? finalScore / maxScore : null;
  const scoreStatusClass =
    scoreRatio == null ? "" : scoreRatio >= 0.8 ? "status-good" : scoreRatio >= 0.6 ? "status-warning" : "status-bad";
  const wordCountValue = Number(wc?.value);
  const hasWordCount = Number.isFinite(wordCountValue);
  const wordCountMin = 150;
  const wordCountOk = hasWordCount ? wordCountValue >= wordCountMin : null;
  const wordCountStatusClass = wordCountOk == null ? "" : wordCountOk ? "status-good" : "status-bad";
  const topicMismatch = Boolean(r.topic_mismatch);
  const situationMismatch = Boolean(r.situation_mismatch);
  const resultDurationSeconds = Number(r.duration_seconds);
  const submissionDurationSeconds = Number(submission?.duration_seconds);
  const durationSeconds = Number.isFinite(resultDurationSeconds)
    ? resultDurationSeconds
    : Number.isFinite(submissionDurationSeconds)
      ? submissionDurationSeconds
      : null;
  const durationOverTarget = Number.isFinite(durationSeconds) ? durationSeconds > 30 * 60 : null;
  const durationStatusClass = durationOverTarget == null ? "" : durationOverTarget ? "status-bad" : "status-good";
  const durationMinutesLabel = (() => {
    if (!Number.isFinite(durationSeconds)) return "—";
    const safeSeconds = Math.max(0, Math.floor(durationSeconds));
    const totalMinutes = Math.ceil(safeSeconds / 60);
    return String(totalMinutes);
  })();

  const errorCount = Array.isArray(highlighted) ? highlighted.length : 0;
  const ptsI = safeGet(r, "criterion_I.points");
  const gradeII = safeGet(r, "criterion_II.grade");
  const ptsII = safeGet(r, "criterion_II.points");
  const gradeIII = safeGet(r, "criterion_III.grade");
  const ptsIII = safeGet(r, "criterion_III.points");
  const commentI = safeGet(r, "criterion_I.comment");
  const commentII = safeGet(r, "criterion_II.comment");
  const commentIII = safeGet(r, "criterion_III.comment");
  const criterionIScaledPointsRaw = Number(safeGet(r, "criterion_I.scaled_points"));
  const criterionIMaxScaledPointsRaw = Number(safeGet(r, "criterion_I.max_scaled_points"));
  const hasScaledPoints = Number.isFinite(criterionIScaledPointsRaw) && Number.isFinite(criterionIMaxScaledPointsRaw);
  const criterionIScaledPoints = hasScaledPoints ? criterionIScaledPointsRaw : Number(ptsI) * 3;
  const criterionIMaxScaledPoints = hasScaledPoints ? criterionIMaxScaledPointsRaw : 15;
  const hasCriterionIScore = Number.isFinite(criterionIScaledPoints) && Number.isFinite(criterionIMaxScaledPoints);
  const criterionIScoreStatusClass = !hasCriterionIScore
    ? ""
    : criterionIScaledPoints >= 12
      ? "status-good"
      : criterionIScaledPoints >= 6
        ? "status-warning"
        : "status-bad";
  const keyPointDetails = safeGet(r, "criterion_I.key_point_details");
  const hasKeyPointDetails = Array.isArray(keyPointDetails) && keyPointDetails.length > 0;
  const criterionILevel =
    safeGet(r, "criterion_I.level") ??
    safeGet(r, "criterion_I.overall_level") ??
    safeGet(r, "criterion_I.language_level");
  const keyPointSummary = (() => {
    if (!hasKeyPointDetails) return null;
    const fulfilled = [];
    const partiallyFulfilled = [];
    const notFulfilled = [];
    let ownIdeaLabel = "—";
    let bestAvailableLevel = null;
    const levelPriority = { A1: 1, A2: 2, B1: 3, "B1+": 4, B2: 5, "B2+": 6, C1: 7, "C1+": 8, C2: 9 };
    const normalizeLevel = (value) => {
      if (value == null) return null;
      const raw = String(value).trim().toUpperCase();
      return raw || null;
    };

    keyPointDetails.forEach((detail, idx) => {
      const status = String(detail?.status ?? "").trim().toLowerCase();
      const isOwnIdea =
        detail?.own_idea === true ||
        detail?.is_own_idea === true ||
        String(detail?.type ?? "").trim().toLowerCase() === "own_idea" ||
        String(detail?.point_type ?? "").trim().toLowerCase() === "own_idea";
      const normalizedLevel = normalizeLevel(detail?.language_level);
      if (normalizedLevel && (!bestAvailableLevel || (levelPriority[normalizedLevel] ?? 0) > (levelPriority[bestAvailableLevel] ?? 0))) {
        bestAvailableLevel = normalizedLevel;
      }

      if (isOwnIdea) {
        ownIdeaLabel = detail?.key_point_text || detail?.comment || "—";
        return;
      }

      const explicitNumber = Number.isFinite(Number(detail?.number)) ? Number(detail.number) : null;
      const detailKeyPoint = detail?.key_point ?? detail?.key_point_text ?? "";
      const matchedExpectedNumber =
        expectedKeyPoints.length > 0 ? expectedPointIndexByText[normalizePointText(detailKeyPoint)] ?? null : null;
      const fallbackByOrder = expectedKeyPoints.length === 0 ? idx + 1 : null;
      const pointNumber = explicitNumber ?? matchedExpectedNumber ?? fallbackByOrder;
      if (!Number.isFinite(pointNumber)) return;
      if (status === "fulfilled") fulfilled.push(pointNumber);
      if (status === "partially_fulfilled") partiallyFulfilled.push(pointNumber);
      if (status === "not_fulfilled") notFulfilled.push(pointNumber);
    });

    const overallLevel = criterionILevel != null && criterionILevel !== "" ? String(criterionILevel) : bestAvailableLevel || "—";
    return {
      fulfilled: fulfilled.length ? fulfilled.join(", ") : "—",
      partiallyFulfilled: partiallyFulfilled.length ? partiallyFulfilled.join(", ") : "—",
      notFulfilled: notFulfilled.length ? notFulfilled.join(", ") : "—",
      ownIdeaLabel,
      overallLevel,
    };
  })();

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

  const formatValue = (value) => {
    if (value == null || value === "") return "—";
    if (typeof value === "boolean") return value ? "true" : "false";
    if (typeof value === "number" || typeof value === "string") return String(value);
    return null;
  };

  const renderDataTree = (value, depth = 0) => {
    const scalar = formatValue(value);
    if (scalar != null) return <span>{scalar}</span>;
    if (Array.isArray(value)) {
      if (!value.length) return <span>—</span>;
      return (
        <ul className={`result-rail-data-list result-rail-data-list--depth-${Math.min(depth + 1, 3)}`}>
          {value.map((item, idx) => (
            <li key={`${depth}-arr-${idx}`}>
              <span className="result-rail-data-key">[{idx}]</span>: {renderDataTree(item, depth + 1)}
            </li>
          ))}
        </ul>
      );
    }
    if (typeof value === "object") {
      const entries = Object.entries(value);
      if (!entries.length) return <span>—</span>;
      return (
        <ul className={`result-rail-data-list result-rail-data-list--depth-${Math.min(depth + 1, 3)}`}>
          {entries.map(([k, v]) => (
            <li key={`${depth}-obj-${k}`}>
              <span className="result-rail-data-key">{k}</span>: {renderDataTree(v, depth + 1)}
            </li>
          ))}
        </ul>
      );
    }
    return <span>{String(value)}</span>;
  };

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
          <details className="summary-block result-main-card">
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
                    <ol className="changes-list">
                      {expectedKeyPoints.map((point, index) => (
                        <li key={`kp-${index}`}>{point}</li>
                      ))}
                    </ol>
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

          <details className="summary-block result-main-card">
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

        <div ref={railTilesRef} className="result-rail-sidebar__content">
          <div className="result-rail-sidebar__tiles">
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
              <span className={`result-rail-tile__value ${scoreStatusClass}`}>
                {r.final_score ?? "—"}/{r.max_score ?? "—"}
              </span>
            </button>
            {railBodyVisible ? (
              <div className="result-rail-card__body">
                <p style={{ margin: "0.15rem 0", fontSize: "0.84rem" }}>
                  <strong>Wortzahl:</strong>{" "}
                  <span className={wordCountStatusClass}>
                    {wc?.value ?? "—"} / {wordCountMin}
                  </span>
                </p>
                <p style={{ margin: "0.15rem 0", fontSize: "0.84rem" }}>
                  <strong>Zeit:</strong>{" "}
                  <span className={durationStatusClass}>
                    {durationMinutesLabel === "—" ? "—" : `${durationMinutesLabel} Min.`}
                  </span>
                </p>
                <p style={{ margin: "0.15rem 0", fontSize: "0.84rem" }}>
                  <strong>Thema passend:</strong>{" "}
                  <span className={topicMismatch ? "status-bad" : "status-good"}>{topicMismatch ? "Schlecht" : "Gut"}</span>
                </p>
                <p style={{ margin: "0.15rem 0", fontSize: "0.84rem" }}>
                  <strong>Situation passend:</strong>{" "}
                  <span className={situationMismatch ? "status-bad" : "status-good"}>
                    {situationMismatch ? "Schlecht" : "Gut"}
                  </span>
                </p>
              </div>
            ) : null}
          </div>

          <div
            id="rail-section-i"
            className={`result-rail-card ${activeSection === "rail-section-i" ? "result-rail-card--active" : ""}`}
          >
            <button type="button" className="result-rail-card__head" onClick={() => onTileActivate("rail-section-i")}>
              <span className="result-rail-tile__title">Task Achievement</span>
              <span className={`result-rail-tile__value ${criterionIScoreStatusClass}`}>
                {hasCriterionIScore ? `${criterionIScaledPoints} / ${criterionIMaxScaledPoints}` : "— / —"}
              </span>
            </button>
            {railBodyVisible ? (
              <div className="result-rail-card__body">
                <p className="metric-card__help" style={{ margin: "0 0 0.4rem" }}>
                  Aufgabenerfüllung
                </p>
                {keyPointSummary ? (
                  <div className="result-rail-summary-list result-rail-kp-summary">
                    <p className="result-rail-kp-summary__line">
                      <strong>Erfüllte Leitpunkte:</strong> {keyPointSummary.fulfilled}
                    </p>
                    <p className="result-rail-kp-summary__line">
                      <strong>Teilweise erfüllt:</strong> {keyPointSummary.partiallyFulfilled}
                    </p>
                    <p className="result-rail-kp-summary__line">
                      <strong>Nicht erfüllt:</strong> {keyPointSummary.notFulfilled}
                    </p>
                    <p className="result-rail-kp-summary__line">
                      <strong>Eigener Aspekt:</strong> {keyPointSummary.ownIdeaLabel}
                    </p>
                    <p className="result-rail-kp-summary__line">
                      <strong>Niveau:</strong> {keyPointSummary.overallLevel}
                    </p>
                  </div>
                ) : null}
                <p style={{ margin: "0.45rem 0 0", color: "var(--muted)", fontSize: "0.86rem", lineHeight: 1.45 }}>
                  {commentI || "Keine Details."}
                </p>
                <div className="result-rail-summary-list">
                  <p className="result-rail-kp-summary__line">
                    <strong>criterion_I (voll):</strong>
                  </p>
                  {renderDataTree(safeGet(r, "criterion_I"))}
                </div>
              </div>
            ) : null}
          </div>

          <div
            id="rail-section-ii"
            className={`result-rail-card ${activeSection === "rail-section-ii" ? "result-rail-card--active" : ""}`}
          >
            <button type="button" className="result-rail-card__head" onClick={() => onTileActivate("rail-section-ii")}>
              <span className="result-rail-tile__title">Kriterium II</span>
              <span className="result-rail-tile__value">{fmtGradePts(gradeII, ptsII)}</span>
            </button>
            {railBodyVisible ? (
              <div>
                {criterionBody("Communicative Design", gradeII, ptsII, commentII)}
                <div className="result-rail-card__body">
                  <p className="result-rail-kp-summary__line">
                    <strong>criterion_II (voll):</strong>
                  </p>
                  {renderDataTree(safeGet(r, "criterion_II"))}
                </div>
              </div>
            ) : null}
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
            {railBodyVisible ? (
              <div>
                {criterionBody("Formal Accuracy", gradeIII, ptsIII, commentIII)}
                <div className="result-rail-card__body">
                  <p className="result-rail-kp-summary__line">
                    <strong>criterion_III (voll):</strong>
                  </p>
                  {renderDataTree(safeGet(r, "criterion_III"))}
                </div>
              </div>
            ) : null}
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
                {Array.isArray(highlighted) && highlighted.length ? (
                  <>
                    <ul className="analysis-errors-list result-rail-card__err-list">
                      {highlighted.map((err, i) => (
                        <li key={i}>{formatErrLine(err)}</li>
                      ))}
                    </ul>
                    <div className="result-rail-summary-list">
                      <p className="result-rail-kp-summary__line">
                        <strong>highlighted_errors (voll):</strong>
                      </p>
                      {renderDataTree(highlighted)}
                    </div>
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
        </div>
      </aside>
    </div>
  );
}
