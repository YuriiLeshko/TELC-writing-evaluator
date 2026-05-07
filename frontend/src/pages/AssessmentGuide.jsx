import { useEffect } from "react";
import { Link, useLocation } from "react-router-dom";
import Card from "../components/Card.jsx";

function useScrollToHash() {
  const location = useLocation();

  useEffect(() => {
    const raw = location.hash?.replace(/^#/, "") || "";
    if (!raw) {
      return undefined;
    }

    const scroll = () => {
      const el = document.getElementById(raw);
      if (el) {
        el.scrollIntoView({ behavior: "smooth", block: "start" });
      }
    };

    const t = window.setTimeout(scroll, 50);
    return () => window.clearTimeout(t);
  }, [location.pathname, location.hash]);
}

const toc = [
  ["overview", "Überblick"],
  ["scoring", "Punkte & Endnote"],
  ["criterion-i", "Kriterium I"],
  ["criterion-ii", "Kriterium II"],
  ["criterion-iii", "Kriterium III"],
  ["word-count", "Mindest-Wortzahl"],
  ["highlighted-errors", "Markierte Fehler"],
  ["improved-text", "Verbesserte Version"],
  ["partial-failed-results", "Teilweise / fehlgeschlagen"],
  ["good-letter", "Guter Aufbau & Muster"],
];

export default function AssessmentGuide() {
  useScrollToHash();

  return (
    <div className="stack assessment-guide">
      <div>
        <Link to="/" className="page-back-link">
          ← Zur Startseite
        </Link>
        <h1 className="page-title">Ratgeber zur TELC-B2-Schriftbewertung</h1>
        <p className="page-subtitle">
          So liest und versteht man die Auswertung in dieser App. Die App orientiert sich am üblichen Bewertungsrahmen
          für schriftliche Aufgaben auf B2-Niveau (drei Kriterien, Notenstufen A–D). Es handelt sich um ein
          Trainingstool — keine offizielle TELC-Bewertung.
        </p>
      </div>

      <Card title="In diesem Ratgeber">
        <nav aria-label="Abschnitte">
          <ul className="assessment-guide__toc">
            {toc.map(([id, label]) => (
              <li key={id}>
                <Link to={`/assessment-guide#${id}`}>{label}</Link>
              </li>
            ))}
          </ul>
        </nav>
      </Card>

      <section id="overview" className="assessment-guide__anchor" tabIndex={-1}>
        <Card title="Überblick">
          <div className="stack stack--sm" style={{ fontSize: "0.94rem", lineHeight: 1.55 }}>
            <p style={{ margin: 0 }}>
              Die App bewertet Ihren Text nach dem Muster der TELC-B2-Schriftprüfung:{" "}
              <strong>drei Kriterien</strong>, die jeweils mit einer Stufe von A bis D und einer Punktzahl zusammengefasst
              werden. Daraus ergibt sich die <strong>Endnote</strong> (skaliert, maximal 45 Punkte).
            </p>
            <ul style={{ margin: "0.25rem 0 0", paddingLeft: "1.25rem" }}>
              <li>
                <strong>Kriterium I — Inhalt / Aufgabenerfüllung:</strong> Werden die geforderten{" "}
                <em>Leitpunkte</em> sinnvoll und ausreichend ausgearbeitet? Gibt es eine passende <em>eigene Idee</em>?
              </li>
              <li style={{ marginTop: "0.35rem" }}>
                <strong>Kriterium II — Kommunikative Gestaltung:</strong> Passt der Text als E-Mail/Brief? Ist er
                strukturiert, zusammenhängend, stilistisch angemessen und sprachlich variiert?
              </li>
              <li style={{ marginTop: "0.35rem" }}>
                <strong>Kriterium III — Sprachrichtigkeit:</strong> Grammatik, Rechtschreibung, Zeichensetzung — beeinflusst
                der Gesamteindruck das Verständnis?
              </li>
            </ul>
            <p style={{ margin: 0 }}>
              In der Ergebnisansicht sehen Sie pro Kriterium eine <strong>Kurzkommentierung</strong>, Punkte/Notenstufe,
              und — sofern vorhanden — Zusatzinformationen (Leitpunkte-Details, Hinweise zur Gestaltung,
              Einzelfehler-Beispiele).
            </p>
          </div>
        </Card>
      </section>

      <section id="scoring" className="assessment-guide__anchor" tabIndex={-1}>
        <Card title="Punkte, Notenstufen und Endnote">
          <div className="stack stack--sm" style={{ fontSize: "0.94rem", lineHeight: 1.55 }}>
            <p style={{ margin: 0 }}>Pro Kriterium wird eine Stufe vergeben. In der App gilt vereinfacht:</p>
            <ul style={{ margin: 0, paddingLeft: "1.25rem" }}>
              <li>
                <strong>A</strong> = 5 Punkte (sehr gut erfüllt)
              </li>
              <li>
                <strong>B</strong> = 3 Punkte (überwiegend erfüllt)
              </li>
              <li>
                <strong>C</strong> = 1 Punkt (teilweise / knapp erfüllt)
              </li>
              <li>
                <strong>D</strong> = 0 Punkte (nicht erfüllt / sehr schwach)
              </li>
            </ul>
            <p style={{ margin: 0 }}>
              <strong>Endnote (angezeigt):</strong> ( Punkte<sub>I</sub> + Punkte<sub>II</sub> + Punkte<sub>III</sub> ) ×
              3. Beispiel: 3 + 3 + 3 = 9 → Endnote <strong>27</strong>.
            </p>
            <p style={{ margin: 0 }}>
              <strong>Höchstwert:</strong> 45 Punkte (alle drei Kriterien mit jeweils 5 Punkten).
            </p>
            <p style={{ margin: 0 }}>
              <strong>Themenfehl („topic mismatch“)</strong>: Wenn der Text das gestellte Thema klar verfehlt, ist das in der
              TELC-Logik eine <em> echte Bewertungsentscheidung</em> — oft mit D-Stufen und einer berechneten Endnote nach
              den obigen Regeln. Das ist etwas anderes als ein <strong>technischer Ausfall</strong>.
            </p>
            <p style={{ margin: 0 }}>
              <strong>Technischer Fehler bei der Auswertung</strong>: Wenn eine Teilprüfung (z. B. Analyse eines
              Kriteriums) nicht zuverlässig laufen konnte, gilt dieses Kriterium als{" "}
              <strong>nicht ausgewertet</strong> — dort gibt es keine Note D „automatisch“, sondern keine Punktzahl. Die{" "}
              <strong>Endnote</strong> kann dann ausfallen oder fehlen (siehe Abschnitt „Teilweise / fehlgeschlagen“).
            </p>
          </div>
        </Card>
      </section>

      <section id="criterion-i" className="assessment-guide__anchor" tabIndex={-1}>
        <Card title="Kriterium I — Aufgabenerfüllung / Leitpunkte">
          <div className="stack stack--sm" style={{ fontSize: "0.94rem", lineHeight: 1.55 }}>
            <p style={{ margin: 0 }}>
              Die <strong>Leitpunkte</strong> beschreiben, was Sie inhaltlich bearbeiten sollen (meist drei vorgegebene
              Punkte). Zusätzlich wird oft eine <strong>eigene Idee</strong> („own idea“) erwartet: ein eigener,
              zur Situation passender Gedanke oder Vorschlag — nicht nur Wiederholung der Aufgabenstellung.
            </p>
            <p style={{ margin: 0 }}>Damit ein Leitpunkt als <strong>erfüllt</strong> gilt, wird typischerweise geprüft:</p>
            <ul style={{ margin: 0, paddingLeft: "1.25rem" }}>
              <li>Bezug zur Aufgabe und zur Situation (relevant, situationstauglich).</li>
              <li>Inhaltliche <strong>Ausarbeitung mit mehreren Sätzen</strong>, nicht nur Stichwortliste.</li>
              <li>Ausreichende <strong>Detailliertheit</strong> (konkrete Infos statt sehr allgemeiner Formulierungen).</li>
              <li>Sprache ungefähres <strong>B2-Niveau</strong> für diesen Teil (nicht nur sehr einfache Sätze).</li>
            </ul>
            <p style={{ margin: 0 }}>
              Die Noten helfen beim groben Einordnen—vereinfacht: <strong>A</strong> sehr starke Aufgabenlösung,{" "}
              <strong>B</strong> solide mit kleinen Lücken, <strong>C</strong> Teilaspekte dünn oder wenig konkret,{" "}
              <strong>D</strong> Inhalt entspricht der Aufgabe kaum oder sehr oberflächlich.
            </p>
          </div>
        </Card>
      </section>

      <section id="criterion-ii" className="assessment-guide__anchor" tabIndex={-1}>
        <Card title="Kriterium II — Kommunikative Gestaltung">
          <div className="stack stack--sm" style={{ fontSize: "0.94rem", lineHeight: 1.55 }}>
            <p style={{ margin: 0 }}>Es geht darum, ob Ihr Schreiben als <strong>E-Mail oder Brief zum Thema passt</strong>:</p>
            <ul style={{ margin: 0, paddingLeft: "1.25rem" }}>
              <li>
                <strong>Struktur</strong>: Betreff, Anrede, sinnvolle Absätze, Schluss/Gruß.
              </li>
              <li>
                <strong>Kohäsion/Kohärenz</strong>: Aufbau ist nachvollziehbar, Verknüpfungen („deshalb“, „außerdem“…) helfen dem Leser.
              </li>
              <li>
                <strong>Register & Stil</strong>: höflicher, situativ angemessener Ton („Sie“-Form, keine SMS-Sprache in der Bewerbung/E-Mail ans Amt oder den Service).
              </li>
              <li>
                <strong>Wortschatzniveau</strong>: angepasst an B2, nicht durchweg sehr einfach und nicht wirr übersetzt wirkend.
              </li>
              <li>
                <strong>Satzvielfalt</strong>: Versuch, verschiedene Satzmuster zu nutzen, nicht nur kürzeste Hauptsatz-Ketten.
              </li>
            </ul>
            <p style={{ margin: 0 }}>
              Fehlen <strong>kernige E-Mail-Elemente</strong> oder wirkt das Register klar falsch für die Aufgabenstellung,
              sinkt das Kriterium häufig deutlich. Die App beschreibt solche Punkte häufig in kurzen Hinweisen und
              Aspekt-Bewertungen.
            </p>
          </div>
        </Card>
      </section>

      <section id="criterion-iii" className="assessment-guide__anchor" tabIndex={-1}>
        <Card title="Kriterium III — Sprachrichtigkeit">
          <div className="stack stack--sm" style={{ fontSize: "0.94rem", lineHeight: 1.55 }}>
            <p style={{ margin: 0 }}>
              Bewertet werden u. a. folgende Teilbereiche (als Status je Aspekt, nicht als einzelner Grammatiktest):
            </p>
            <ul style={{ margin: 0, paddingLeft: "1.25rem" }}>
              <li>Grammatik, Syntax, Wortstellung, Verbformen, Kongruenz</li>
              <li>Rechtschreibung, Zeichensetzung, Großschreibung</li>
              <li>
                <strong>Einfluss auf das Verständnis</strong> („comprehension“): Sind Fehler „schönheitshalber“, oder wird der Inhalt für den Leser unklar oder riskant falsch interpretiert?
              </li>
            </ul>
            <p style={{ margin: 0 }}>
              Typische Statuswerte (vereinfachte Bedeutung für Lernzwecke):
            </p>
            <ul style={{ margin: 0, paddingLeft: "1.25rem" }}>
              <li>
                <strong>strong</strong> — sehr solide / kaum störend
              </li>
              <li>
                <strong>adequate</strong> — insgesamt brauchbar, gelegentliche Mängel
              </li>
              <li>
                <strong>weak</strong> — häufiger auffällig, beeinträchtigt den Lesefluss merklich
              </li>
              <li>
                <strong>problematic</strong> — oft schwer oder riskant falsch lesbar / stark eingeschränkte Kontrolle
              </li>
            </ul>
          </div>
        </Card>
      </section>

      <section id="word-count" className="assessment-guide__anchor" tabIndex={-1}>
        <Card title="Wortzahl (Mindestmaß)">
          <div className="stack stack--sm" style={{ fontSize: "0.94rem", lineHeight: 1.55 }}>
            <p style={{ margin: 0 }}>
              Für diese App gilt eine <strong>Mindestwortzahl von 150 Wörtern</strong> (wie in vielen Aufgabenformulierungen zu
              B2-Schreibteil). Unterhalb dieser Grenze kann die angezeigte Bewertungslogik die{" "}
              <strong>Endnote besonders berücksichtigen oder zurücksetzen</strong> — genau wie in den internen Projektregeln
              dokumentiert („harte Untergrenze“). Bitte berücksichtigen Sie diese Anzeige ernst, auch wenn kurze Texte
              inhaltlich „fast passen“ würden.
            </p>
          </div>
        </Card>
      </section>

      <section id="highlighted-errors" className="assessment-guide__anchor" tabIndex={-1}>
        <Card title="Markierte Fehler (Beispiele)">
          <div className="stack stack--sm" style={{ fontSize: "0.94rem", lineHeight: 1.55 }}>
            <p style={{ margin: 0 }}>
              Die App markiert <strong>einige konkrete Stellen</strong> in Ihrem Originaltext als Beispiele. Pro Eintrag
              finden Sie typischerweise:
            </p>
            <ul style={{ margin: 0, paddingLeft: "1.25rem" }}>
              <li>das <strong>Originalfragment</strong> (ein kurzes Stück wie im Text),</li>
              <li>einen <strong>Korrekturvorschlag</strong>,</li>
              <li>eine <strong>Fehlerart</strong> (z. B. Kasus, Verb),</li>
              <li>eine kurze <strong>Erläuterung</strong>.</li>
            </ul>
            <p style={{ margin: 0 }}>
              Die Liste ist begrenzt (z. B. nicht jeder kleine Punkt kann gezeigt werden). Fehlende Markierung{" "}
              <strong>beweist nicht</strong>, dass keine weiteren Verbesserungen nötig wären.
            </p>
          </div>
        </Card>
      </section>

      <section id="improved-text" className="assessment-guide__anchor" tabIndex={-1}>
        <Card title="Verbesserte Textversion („improved_text“)">
          <div className="stack stack--sm" style={{ fontSize: "0.94rem", lineHeight: 1.55 }}>
            <p style={{ margin: 0 }}>
              Die verbesserte Fassung ist eine <strong>reine Lernhilfe</strong>. Sie fließt <strong>nicht</strong> in die
              Bewertungsrechnung ein.
            </p>
            <p style={{ margin: 0 }}>
              Sie soll denselben Sachinhalt möglichst wahren, <strong>keine neuen konkreten Fakten erfinden</strong> und
              den Text höflicher, klarer und sprachlich sicherer machen — kein anderer Brief an eine andere Adresse als in
              Ihrer Aufgabe vorgegeben.
            </p>
            <p style={{ margin: 0 }}>
              Bei technisch unvollständiger Auswertung kann diese Version durch den <strong>Ursprungstext als Platzhalter</strong>{" "}
              ersetzt werden — das ist ebenfalls keine „Note“, sondern ein Hinweis auf den Trainingsbetrieb der App.
            </p>
          </div>
        </Card>
      </section>

      <section id="partial-failed-results" className="assessment-guide__anchor" tabIndex={-1}>
        <Card title="Teilauswertung oder technisch fehlgeschlagen">
          <div className="stack stack--sm" style={{ fontSize: "0.94rem", lineHeight: 1.55 }}>
            <p style={{ margin: 0 }}>
              Schlägt eine automatische Teilprüfung fehl (z. B. Überlastung eines Dienstes, Schemafehler beim Modell), wird
              ein Kriterium in der Ansicht oft als <strong>nicht ausgewertet</strong> gekennzeichnet — dort fehlen dann
              bewusst gültige <strong>Note und Punkte</strong>.
            </p>
            <p style={{ margin: 0 }}>
              Das ist <strong>nicht dasselbe</strong> wie „Note D“. Eine echte Note D beschreibt sprachliche/inhaltliche
              Qualität nach den Kriterien; ein technisches „failed“ beschreibt, dass keine zuverlässige Bewertung für dieses
              Kriterium angeboten werden konnte.
            </p>
            <p style={{ margin: 0 }}>
              In diesen Fällen kann die <strong>Endnote fehlen</strong> oder leer angezeigt werden (<code>null</code>), weil keine
              vollständige Gesamtrechnung sinnvoll wäre. Bitte werfen Sie den Text später erneut ein oder kontaktieren Sie die
              Betreiber, wenn das wiederholt passiert.
            </p>
          </div>
        </Card>
      </section>

      <section id="good-letter" className="assessment-guide__anchor" tabIndex={-1}>
        <Card title="Guter Aufbau — E-Mail/Brief nach TELC-B2-Art">
          <div className="stack stack--sm" style={{ fontSize: "0.94rem", lineHeight: 1.55 }}>
            <p style={{ margin: 0 }}>Eine gut strukturierte Bewerbungs- oder Reklamations-E-Mail enthält typischerweise:</p>
            <ol style={{ margin: 0, paddingLeft: "1.25rem" }}>
              <li>
                einen <strong>Betreff</strong>,
              </li>
              <li>
                eine <strong>höfliche Anrede</strong>,
              </li>
              <li>
                eine kurze <strong>Einleitung</strong>, die das Anliegen nennt,
              </li>
              <li>
                einen <strong>Hauptteil</strong>: Leitpunkte ausführlich, logisch verteilt über Absätze,
              </li>
              <li>
                eine klare <strong>Aufforderung / Erwartung</strong> („Ich bitte um …“, „Ich erwarte …“),
              </li>
              <li>
                einen <strong>Schlusssatz</strong>,
              </li>
              <li>
                eine passende <strong>Grußformel</strong> und Ihren <strong>Namen</strong>.
              </li>
            </ol>
            <p style={{ margin: 0 }}>
              <strong>Kurzvorlage (Platzhalter — bitte Ihre Daten einsetzen):</strong>
            </p>
            <pre className="text-panel assessment-guide__template" role="region" aria-label="Muster-E-Mail">
{`Betreff: Bitte um …

Sehr geehrte Damen und Herren,

ich wende mich an Sie, weil …
Zunächst möchte ich … darstellen.
Außerdem …
Aus diesem Grund bitte ich Sie um …


Mit freundlichen Grüßen
[Ihr Vor- und Nachname]`}
            </pre>
            <p style={{ margin: 0 }}>
              <strong>Tipps für B2-Prüfungs-/Trainingsstress:</strong>
            </p>
            <ul style={{ margin: 0, paddingLeft: "1.25rem" }}>
              <li>Jeden Leitpunkt <strong>eigenständig ausformulieren</strong>, nicht nur abhaken.</li>
              <li>Verbindungen nutzen: <em>außerdem</em>, <em>deshalb</em>, <em>trotzdem</em>, <em>jedoch</em> — aber nicht übertreiben.</li>
              <li>Höfliches Sie-Register und sachlicher Ton, keine Umgangssprache in formellen E-Mails.</li>
              <li>Sehr kurze oder rein stichpunktartige Antworten vermeiden — Prüfer erwarten Fließtext.</li>
              <li>Letzter Check: Grammatik, Kommas, Großschreibung (Nomen!), einmal laut lesen.</li>
            </ul>
          </div>
        </Card>
      </section>
    </div>
  );
}
