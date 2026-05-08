import { useLocation, useOutletContext } from "react-router-dom";
import Card from "../components/Card.jsx";

export default function HomePage() {
  const location = useLocation();
  const { disclaimerAccepted, onAcceptDisclaimer } = useOutletContext();

  return (
    <div className="stack">
      <h1 className="page-title">TELC B2 Writing Evaluator</h1>
      <p className="page-subtitle">
        Der TELC B2 Writing Evaluator ist ein KI-gestütztes Trainingstool für schriftliche TELC-B2-Aufgaben. Sie
        üben typische Schreibsituationen, erhalten strukturierte Rückmeldungen und können Ihre Texte gezielt verbessern.
      </p>
      <Card title="Was dieses Tool bietet">
        <div className="stack stack--sm" style={{ color: "var(--muted)", fontSize: "0.94rem" }}>
          <p style={{ margin: 0 }}>
            Das Tool unterstützt Sie beim Training von Schreibaufgaben im Stil der TELC-B2-Prüfung und führt Sie durch
            realistische Aufgabenformate.
          </p>
          <p style={{ margin: 0 }}>
            Nach der Einreichung erhalten Sie eine KI-basierte Auswertung mit Punktzahl, kriteriumsbezogenen Kommentaren,
            markierten Grammatikstellen und einer verbesserten Textversion als Lernhilfe.
          </p>
          <p style={{ margin: 0 }}>
            Ziel ist die Vorbereitung und Selbstreflexion - nicht die Ersetzung einer offiziellen Prüfungsauswertung.
          </p>
        </div>
      </Card>

      {location.state?.disclaimerRequired && !disclaimerAccepted ? (
        <div className="alert alert--warn">
            Bitte bestätigen Sie zuerst den Hinweis auf dieser Startseite, bevor Sie Übungen oder Verlauf öffnen.
        </div>
      ) : null}

      <div className="disclaimer-box">
        <h2 className="disclaimer-box__title">Wichtiger Hinweis</h2>
        <p>
          Dieser Trainer hat keine offizielle Verbindung zu TELC oder zur Organisation, die die Prüfung durchführt.
          Er ist keine offizielle Informationsquelle und kein offizieller Bewerter.
        </p>
        <p>
          Die Ergebnisse werden KI-gestützt erzeugt und können von einer offiziellen Bewertung abweichen. Die App
          versucht, sich möglichst eng am offiziellen TELC-Format zu orientieren, hat jedoch keinen Zugriff auf interne
          Bewertungsinformationen oder interne Prüfungsdaten.
        </p>
        <button
          type="button"
          className="btn btn--danger"
          onClick={onAcceptDisclaimer}
          disabled={disclaimerAccepted}
        >
          {disclaimerAccepted
            ? "Hinweis bereits bestätigt"
            : "Ich habe den Hinweis verstanden und möchte fortfahren"}
        </button>
      </div>
    </div>
  );
}
