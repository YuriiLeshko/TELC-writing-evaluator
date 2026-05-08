import { useCallback, useEffect, useRef, useState } from "react";
import { PanelRightClose, PanelRightOpen, X } from "lucide-react";
import ErrorHighlightedText from "./ErrorHighlightedText.jsx";
import InfoLink from "./InfoLink.jsx";
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
  const overallAnalysisStatus = safeGet(r, "analysis_status") || "success";
  const overallAnalysisError = safeGet(r, "analysis_error");
  const finalScoreRaw = r.final_score;
  const maxScoreRaw = r.max_score;
  const finalScore =
    finalScoreRaw === null || finalScoreRaw === undefined || finalScoreRaw === ""
      ? NaN
      : Number(finalScoreRaw);
  const maxScore =
    maxScoreRaw === null || maxScoreRaw === undefined || maxScoreRaw === ""
      ? NaN
      : Number(maxScoreRaw);
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
  const ptsIRaw = safeGet(r, "criterion_I.points");
  const ptsI = ptsIRaw === null || ptsIRaw === undefined || ptsIRaw === "" ? NaN : Number(ptsIRaw);
  const commentI = safeGet(r, "criterion_I.comment");
  const commentII = safeGet(r, "criterion_II.comment");
  const commentIII = safeGet(r, "criterion_III.comment");
  const criterionIScaledPointsRaw = Number(safeGet(r, "criterion_I.scaled_points"));
  const criterionIMaxScaledPointsRaw = Number(safeGet(r, "criterion_I.max_scaled_points"));
  const hasScaledPoints = Number.isFinite(criterionIScaledPointsRaw) && Number.isFinite(criterionIMaxScaledPointsRaw);
  const criterionIScaledPoints = hasScaledPoints
    ? criterionIScaledPointsRaw
    : Number.isFinite(ptsI)
      ? ptsI * 3
      : NaN;
  const criterionIMaxScaledPoints = hasScaledPoints ? criterionIMaxScaledPointsRaw : 15;
  const hasCriterionIScore = Number.isFinite(criterionIScaledPoints) && Number.isFinite(criterionIMaxScaledPoints);
  const criterionIScoreStatusClass = !hasCriterionIScore
    ? ""
    : criterionIScaledPoints >= 12
      ? "status-good"
      : criterionIScaledPoints >= 6
        ? "status-warning"
        : "status-bad";
  const criterionIIRawPointsVal = safeGet(r, "criterion_II.points");
  const criterionIIRawPoints =
    criterionIIRawPointsVal === null || criterionIIRawPointsVal === undefined || criterionIIRawPointsVal === ""
      ? NaN
      : Number(criterionIIRawPointsVal);
  const criterionIIScaledPointsRaw = Number(safeGet(r, "criterion_II.scaled_points"));
  const criterionIIMaxScaledPointsRaw = Number(safeGet(r, "criterion_II.max_scaled_points"));
  const hasCriterionIIScaledPoints = Number.isFinite(criterionIIScaledPointsRaw) && Number.isFinite(criterionIIMaxScaledPointsRaw);
  const criterionIIScaledPoints = hasCriterionIIScaledPoints
    ? criterionIIScaledPointsRaw
    : Number.isFinite(criterionIIRawPoints)
      ? criterionIIRawPoints * 3
      : NaN;
  const criterionIIMaxScaledPoints = hasCriterionIIScaledPoints ? criterionIIMaxScaledPointsRaw : 15;
  const hasCriterionIIScore = Number.isFinite(criterionIIScaledPoints) && Number.isFinite(criterionIIMaxScaledPoints);
  const criterionIIScoreStatusClass = !hasCriterionIIScore
    ? ""
    : criterionIIScaledPoints >= 12
      ? "status-good"
      : criterionIIScaledPoints >= 6
        ? "status-warning"
        : "status-bad";
  const communicationAnalysisStatus = String(safeGet(r, "criterion_II.analysis_status") || "success");
  const communicationAnalysisError = safeGet(r, "criterion_II.analysis_error");
  const keyPointsAnalysisStatus = String(safeGet(r, "criterion_I.analysis_status") || "success");
  const keyPointsAnalysisError = safeGet(r, "criterion_I.analysis_error");
  const communicationIndicatorsRaw = safeGet(r, "criterion_II.communication_indicators");
  const communicationIndicators = Array.isArray(communicationIndicatorsRaw) ? communicationIndicatorsRaw : [];
  const mapCommunicationRating = (rating) => {
    const normalized = String(rating ?? "").trim().toLowerCase();
    if (normalized === "excellent") return "sehr gut";
    if (normalized === "good") return "gut";
    if (normalized === "acceptable") return "akzeptabel";
    if (normalized === "weak") return "schwach";
    if (normalized === "missing") return "fehlt";
    return "—";
  };
  const communicationRatingClass = (rating) => {
    const normalized = String(rating ?? "").trim().toLowerCase();
    if (normalized === "excellent" || normalized === "good") return "status-good";
    if (normalized === "acceptable") return "status-warning";
    if (normalized === "weak" || normalized === "missing") return "status-bad";
    return "";
  };
  const criterionIIIRawVal = safeGet(r, "criterion_III.points");
  const criterionIIIRawPoints =
    criterionIIIRawVal === null || criterionIIIRawVal === undefined || criterionIIIRawVal === ""
      ? NaN
      : Number(criterionIIIRawVal);
  const criterionIIIScaledPointsRaw = Number(safeGet(r, "criterion_III.scaled_points"));
  const criterionIIIMaxScaledPointsRaw = Number(safeGet(r, "criterion_III.max_scaled_points"));
  const hasCriterionIIIScaledPoints = Number.isFinite(criterionIIIScaledPointsRaw) && Number.isFinite(criterionIIIMaxScaledPointsRaw);
  const criterionIIIScaledPoints = hasCriterionIIIScaledPoints
    ? criterionIIIScaledPointsRaw
    : Number.isFinite(criterionIIIRawPoints)
      ? criterionIIIRawPoints * 3
      : NaN;
  const criterionIIIMaxScaledPoints = hasCriterionIIIScaledPoints ? criterionIIIMaxScaledPointsRaw : 15;
  const hasCriterionIIIScore = Number.isFinite(criterionIIIScaledPoints) && Number.isFinite(criterionIIIMaxScaledPoints);
  const criterionIIIScoreStatusClass = !hasCriterionIIIScore
    ? ""
    : criterionIIIScaledPoints >= 12
      ? "status-good"
      : criterionIIIScaledPoints >= 6
        ? "status-warning"
        : "status-bad";
  const accuracyAnalysisStatus = String(safeGet(r, "criterion_III.analysis_status") || "success");
  const accuracyAnalysisError = safeGet(r, "criterion_III.analysis_error");
  const aspectRatingsFlat =
    crit3.aspect_ratings !== null && typeof crit3.aspect_ratings === "object" && !Array.isArray(crit3.aspect_ratings)
      ? crit3.aspect_ratings
      : null;
  const accuracyDetailsLegacy = safeGet(r, "criterion_III.accuracy_details");
  const normalizeAccuracyValue = (value) => String(value ?? "").trim().toLowerCase();
  const extractAccuracyAspect = (aspectKey) => {
    const fromFlat = aspectRatingsFlat?.[aspectKey];
    if (typeof fromFlat === "string" && normalizeAccuracyValue(fromFlat)) return { status: fromFlat };

    const legacy = accuracyDetailsLegacy;
    if (!legacy || typeof legacy !== "object") return null;
    const direct = legacy?.[aspectKey];
    if (direct && typeof direct === "object" && !Array.isArray(direct)) return direct;
    const nested = legacy?.aspects?.[aspectKey];
    if (nested && typeof nested === "object" && !Array.isArray(nested)) return nested;
    if (Array.isArray(legacy)) {
      return legacy.find((entry) => {
        const key = normalizeAccuracyValue(entry?.aspect ?? entry?.name ?? entry?.type ?? entry?.key);
        return key === normalizeAccuracyValue(aspectKey);
      });
    }
    if (Array.isArray(legacy?.aspects)) {
      return legacy.aspects.find((entry) => {
        const key = normalizeAccuracyValue(entry?.aspect ?? entry?.name ?? entry?.type ?? entry?.key);
        return key === normalizeAccuracyValue(aspectKey);
      });
    }
    return null;
  };
  const mapAccuracyStatus = (status) => {
    const normalized = normalizeAccuracyValue(status);
    if (!normalized) return "—";
    if (normalized === "strong") return "gut";
    if (normalized === "adequate") return "ausreichend";
    if (normalized === "weak") return "schwach";
    if (normalized === "problematic") return "problematisch";
    return "—";
  };
  const accuracyStatusClass = (status) => {
    const normalized = normalizeAccuracyValue(status);
    if (normalized === "strong") return "status-good";
    if (normalized === "adequate") return "status-warning";
    if (["weak", "problematic"].includes(normalized)) return "status-bad";
    return "";
  };
  const criterionIIIIndicators = [
    { key: "grammar", label: "Grammatik" },
    { key: "syntax", label: "Satzbau" },
    { key: "word_order", label: "Wortstellung" },
    { key: "verb_forms", label: "Verbformen" },
    { key: "agreement", label: "Kongruenz" },
    { key: "spelling", label: "Rechtschreibung" },
    { key: "punctuation", label: "Zeichensetzung" },
    { key: "capitalization", label: "Großschreibung" },
    { key: "comprehension", label: "Verständlichkeit" },
  ].map((indicator) => {
    const detail = extractAccuracyAspect(indicator.key);
    const rawStatus = detail?.status ?? safeGet(r, `criterion_III.${indicator.key}_quality`);
    const statusLabel = mapAccuracyStatus(rawStatus);
    const statusClass = accuracyStatusClass(rawStatus);
    return { ...indicator, statusLabel, statusClass };
  });
  const keyPointDetails = safeGet(r, "criterion_I.key_point_details");
  const hasKeyPointDetails = Array.isArray(keyPointDetails) && keyPointDetails.length > 0;
  const criterionILevel =
    safeGet(r, "criterion_I.level") ??
    safeGet(r, "criterion_I.overall_level") ??
    safeGet(r, "criterion_I.language_level");
  const keyPointSummary = (() => {
    if (!hasKeyPointDetails) return null;
    let fulfilledCount = 0;
    let bestAvailableLevel = null;
    const levelPriority = { A1: 1, A2: 2, B1: 3, "B1+": 4, B2: 5, "B2+": 6, C1: 7, "C1+": 8, C2: 9 };
    const normalizeLevel = (value) => {
      if (value == null) return null;
      const raw = String(value).trim().toUpperCase();
      return raw || null;
    };

    keyPointDetails.forEach((detail) => {
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

      if (!isOwnIdea && status === "fulfilled") fulfilledCount += 1;
    });

    const summaryLevel =
      safeGet(r, "criterion_I.task_achievement_summary.overall_level") ??
      (criterionILevel != null && criterionILevel !== "" ? String(criterionILevel) : null) ??
      bestAvailableLevel ??
      "—";

    return {
      fulfilledCount,
      overallLevel: summaryLevel,
    };
  })();

  const keyPointDetailCards = (() => {
    if (!hasKeyPointDetails) return [];
    let regularPointNumber = 0;
    const statusToGerman = (status) => {
      const normalized = String(status ?? "").trim().toLowerCase();
      if (normalized === "fulfilled") return "erfüllt";
      if (normalized === "partially_fulfilled") return "teilweise erfüllt";
      if (normalized === "not_fulfilled") return "nicht erfüllt";
      return "—";
    };

    return keyPointDetails.map((detail, idx) => {
      const isOwnIdea =
        detail?.own_idea === true ||
        detail?.is_own_idea === true ||
        String(detail?.type ?? "").trim().toLowerCase() === "own_idea" ||
        String(detail?.point_type ?? "").trim().toLowerCase() === "own_idea";

      const keyPointText = String(detail?.key_point ?? detail?.key_point_text ?? "—").trim() || "—";
      const statusLabel = statusToGerman(detail?.status);
      const sentenceCount = Number(detail?.sentence_count);
      const sentenceCountLabel = Number.isFinite(sentenceCount) ? String(sentenceCount) : "—";
      const languageLevel = String(detail?.language_level ?? "—").trim() || "—";
      const situationAppropriate = detail?.situation_appropriate;
      const situationLabel = situationAppropriate === true ? "Ja" : situationAppropriate === false ? "Nein" : "—";
      const comment = String(detail?.comment ?? "").trim() || "—";

      const title = isOwnIdea ? "Eigener Aspekt" : `Punkt ${++regularPointNumber}`;

      return {
        id: `${isOwnIdea ? "own" : "point"}-${idx}`,
        title,
        keyPointText,
        statusLabel,
        sentenceCountLabel,
        languageLevel,
        situationLabel,
        comment,
      };
    });
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

  const highlightedErrorItems = (Array.isArray(highlighted) ? highlighted : []).map((err, idx) => {
    const errorType = String(err?.error_type ?? "").trim();
    const title = errorType ? `Fehler ${idx + 1} · ${errorType}` : `Fehler ${idx + 1}`;
    return {
      id: `error-${idx}`,
      title,
      text: String(err?.text ?? "").trim() || "—",
      explanation: String(err?.explanation ?? "").trim() || "—",
      correction: String(err?.correction ?? "").trim() || "—",
    };
  });

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
                <div className="text-panel">{improved.improved_text || "—"}</div>
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
            <div className="result-rail-card__head-with-info">
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
            <InfoLink sectionId="score-interpretation" title="Punkte, Endnote und Wortzahl im Ratgeber" />
            </div>
            {railBodyVisible ? (
              <div className="result-rail-card__body">
                {overallAnalysisStatus === "partial" || overallAnalysisStatus === "failed" ? (
                  <p className="alert alert--warn" style={{ marginBottom: "0.5rem" }}>
                    {overallAnalysisStatus === "partial"
                      ? "Teilbewertung: Mindestens ein Kriterium konnte technisch nicht ausgewertet werden. Die Endnote entfällt."
                      : "Die Auswertung ist technisch fehlgeschlagen. Es wurde keine gültige Endnote ermittelt."}
                    {overallAnalysisError ? ` ${overallAnalysisError}` : ""}
                  </p>
                ) : null}
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
            <div className="result-rail-card__head-with-info">
            <button type="button" className="result-rail-card__head" onClick={() => onTileActivate("rail-section-i")}>
              <span className="result-rail-tile__title">Aufgabenerfüllung</span>
              <span className={`result-rail-tile__value ${criterionIScoreStatusClass}`}>
                {hasCriterionIScore ? `${criterionIScaledPoints} / ${criterionIMaxScaledPoints}` : "— / —"}
              </span>
            </button>
            <InfoLink sectionId="criterion-i" title="Kriterium I: Aufgabenerfüllung im Ratgeber" />
            </div>
            {railBodyVisible ? (
              <div className="result-rail-card__body">
                {keyPointsAnalysisStatus === "failed" ? (
                  <p className="alert alert--warn" style={{ marginBottom: "0.4rem" }}>
                    Die Auswertung dieses Kriteriums ist technisch fehlgeschlagen. Es wurde keine Punktzahl für dieses Kriterium
                    ermittelt.
                    {keyPointsAnalysisError ? ` ${keyPointsAnalysisError}` : ""}
                  </p>
                ) : null}
                <div className="result-rail-kp-summary">
                  <p className="result-rail-kp-summary__line">
                    <span>
                      <strong>Erfüllte Punkte:</strong> {keyPointSummary?.fulfilledCount ?? "—"}
                    </span>
                  </p>
                  <p className="result-rail-kp-summary__line">
                    <span>
                      <strong>Sprachniveau:</strong> {keyPointSummary?.overallLevel ?? "—"}
                    </span>
                  </p>
                </div>
                <p style={{ margin: "0.35rem 0 0", color: "var(--muted)", fontSize: "0.82rem", lineHeight: 1.35 }}>
                  {commentI || "Keine Details."}
                </p>
                {keyPointDetailCards.length ? (
                  <div className="result-rail-kp-details">
                    {keyPointDetailCards.map((point) => (
                      <details key={point.id} className="result-rail-kp-item">
                        <summary className="result-rail-kp-item__summary">{point.title}</summary>
                        <div className="result-rail-kp-item__body">
                          <p className="result-rail-kp-item__line">
                            <strong>Inhalt:</strong> {point.keyPointText}
                          </p>
                          <p className="result-rail-kp-item__line">
                            <strong>Status:</strong> {point.statusLabel}
                          </p>
                          <p className="result-rail-kp-item__line">
                            <strong>Sätze:</strong> {point.sentenceCountLabel}
                          </p>
                          <p className="result-rail-kp-item__line">
                            <strong>Sprachniveau:</strong> {point.languageLevel}
                          </p>
                          <p className="result-rail-kp-item__line">
                            <strong>Zur Situation passend:</strong> {point.situationLabel}
                          </p>
                          <p className="result-rail-kp-item__line">
                            <strong>Kommentar:</strong> {point.comment}
                          </p>
                        </div>
                      </details>
                    ))}
                  </div>
                ) : null}
              </div>
            ) : null}
          </div>

          <div
            id="rail-section-ii"
            className={`result-rail-card ${activeSection === "rail-section-ii" ? "result-rail-card--active" : ""}`}
          >
            <div className="result-rail-card__head-with-info">
            <button type="button" className="result-rail-card__head" onClick={() => onTileActivate("rail-section-ii")}>
              <span className="result-rail-tile__title">Kommunikative Gestaltung</span>
              <span className={`result-rail-tile__value ${criterionIIScoreStatusClass}`}>
                {hasCriterionIIScore ? `${criterionIIScaledPoints} / ${criterionIIMaxScaledPoints}` : "— / —"}
              </span>
            </button>
            <InfoLink sectionId="criterion-ii" title="Kriterium II: Kommunikative Gestaltung im Ratgeber" />
            </div>
            {railBodyVisible ? (
              <div className="result-rail-card__body">
                <p className="metric-card__help" style={{ margin: "0 0 0.35rem" }}>
                  Struktur, Stil und Wortschatz
                </p>
                <p style={{ margin: "0.35rem 0 0", color: "var(--muted)", fontSize: "0.82rem", lineHeight: 1.35 }}>
                  {commentII || "Keine Details."}
                </p>
                {communicationAnalysisStatus === "failed" ? (
                  <p className="alert alert--warn" style={{ marginTop: "0.4rem" }}>
                    Die Auswertung dieses Kriteriums ist technisch fehlgeschlagen. Es wurde keine Bewertung für dieses Kriterium
                    ermittelt.
                    {communicationAnalysisError ? ` ${communicationAnalysisError}` : ""}
                  </p>
                ) : (
                  <div className="result-rail-kp-details">
                    {communicationIndicators.map((item, idx) => (
                      <div key={`${item?.aspect || "aspect"}-${idx}`} className="result-rail-kp-detail">
                        <p className="result-rail-kp-detail__line">
                          <strong>{item?.label || "Aspekt"}:</strong>{" "}
                          <span className={communicationRatingClass(item?.rating)}>{mapCommunicationRating(item?.rating)}</span>
                        </p>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ) : null}
          </div>

          <div
            id="rail-section-iii"
            className={`result-rail-card ${activeSection === "rail-section-iii" ? "result-rail-card--active" : ""}`}
          >
            <div className="result-rail-card__head-with-info">
            <button
              type="button"
              className="result-rail-card__head"
              onClick={() => onTileActivate("rail-section-iii")}
            >
              <span className="result-rail-tile__title">Formale Korrektheit</span>
              <span className={`result-rail-tile__value ${criterionIIIScoreStatusClass}`}>
                {hasCriterionIIIScore ? `${criterionIIIScaledPoints} / ${criterionIIIMaxScaledPoints}` : "— / —"}
              </span>
            </button>
            <InfoLink sectionId="criterion-iii" title="Kriterium III: Formale Korrektheit im Ratgeber" />
            </div>
            {railBodyVisible ? (
              <div className="result-rail-card__body">
                <p className="metric-card__help" style={{ margin: "0 0 0.35rem" }}>
                  Grammatik, Satzbau und Rechtschreibung
                </p>
                <div className="result-rail-kp-summary">
                  {accuracyAnalysisStatus === "failed" ? (
                    <p className="alert alert--warn" style={{ margin: "0 0 0.5rem" }}>
                      Die Auswertung dieses Kriteriums ist technisch fehlgeschlagen. Es wurde keine Bewertung für dieses Kriterium
                      ermittelt.
                      {accuracyAnalysisError ? ` ${accuracyAnalysisError}` : ""}
                    </p>
                  ) : null}
                  {accuracyAnalysisStatus !== "failed"
                    ? criterionIIIIndicators.map((indicator) => (
                        <p key={indicator.key} className="result-rail-kp-summary__line">
                          <strong>{indicator.label}:</strong>{" "}
                          <span className={indicator.statusClass}>{indicator.statusLabel}</span>
                        </p>
                      ))
                    : null}
                </div>
                <p style={{ margin: "0.35rem 0 0", color: "var(--muted)", fontSize: "0.82rem", lineHeight: 1.35 }}>
                  {commentIII || "Keine Details."}
                </p>
              </div>
            ) : null}
          </div>

          <div
            id="rail-section-errors"
            className={`result-rail-card ${activeSection === "rail-section-errors" ? "result-rail-card--active" : ""}`}
          >
            <div className="result-rail-card__head-with-info">
            <button
              type="button"
              className="result-rail-card__head"
              onClick={() => onTileActivate("rail-section-errors")}
            >
              <span className="result-rail-tile__title">Markierte Fehler</span>
              <span className="result-rail-tile__value">{errorCount}</span>
            </button>
            <InfoLink sectionId="error-marking" title="Markierte Fehler im Ratgeber" />
            </div>
            {railBodyVisible ? (
              <div className="result-rail-card__body">
                {highlightedErrorItems.length ? (
                  <div className="result-rail-kp-details">
                    {highlightedErrorItems.map((error) => (
                      <details key={error.id} className="result-rail-error-item">
                        <summary className="result-rail-error-item__summary">{error.title}</summary>
                        <div className="result-rail-error-item__body">
                          <p className="result-rail-error-item__line result-rail-error-item__line--error">
                            <strong>Fehler:</strong> {error.text}
                          </p>
                          <p className="result-rail-error-item__line">
                            <strong>Erklärung:</strong> {error.explanation}
                          </p>
                          <p className="result-rail-error-item__line result-rail-error-item__line--correction">
                            <strong>Korrektur:</strong> {error.correction}
                          </p>
                        </div>
                      </details>
                    ))}
                  </div>
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
