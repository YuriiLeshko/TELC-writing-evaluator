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

/** Inhaltsverzeichnis: Reihenfolge = Leselogik */
const toc = [
  ["overview", "Überblick"],
  ["result-overview", "Thema, Situation, Zeit"],
  ["score-interpretation", "Endnote & Kartenfarben"],
  ["scoring", "Noten A–D & Formel"],
  ["word-count", "Wortzahl"],
  ["partial-failed-results", "Teilweise / fehlgeschlagen"],
  ["criterion-i", "Kriterium I (Überblick)"],
  ["task-achievement-fields", "Leitpunkte & Karten"],
  ["criterion-ii", "Kriterium II (Überblick)"],
  ["communication-fields", "E-Mail & Gestaltung"],
  ["criterion-iii", "Kriterium III (Überblick)"],
  ["accuracy-fields", "Sprachliche Teilaspekte"],
  ["error-marking", "Markierte Fehler"],
  ["improved-text", "Verbesserte Version"],
  ["good-letter", "Gute E-Mail & Muster"],
];

function FieldBlock({ title, meaning, conclusion, improve }) {
  return (
    <div className="assessment-guide__field">
      <h4 className="assessment-guide__field-title">{title}</h4>
      <p className="assessment-guide__field-line">
        <strong>Was das ist:</strong> <span className="assessment-guide__field-body">{meaning}</span>
      </p>
      <p className="assessment-guide__field-line">
        <strong>Was Sie daraus schließen:</strong> <span className="assessment-guide__field-body">{conclusion}</span>
      </p>
      <p className="assessment-guide__field-line">
        <strong>Beim nächsten Text:</strong> <span className="assessment-guide__field-body">{improve}</span>
      </p>
    </div>
  );
}

export default function AssessmentGuide() {
  useScrollToHash();

  return (
    <div className="stack assessment-guide assessment-guide-page">
      <header className="assessment-guide__hero">
        <Link to="/" className="page-back-link">
          ← Zur Startseite
        </Link>
        <h1 className="page-title assessment-guide__page-title">Ratgeber: Ihr Ergebnis verstehen</h1>
        <p className="page-subtitle assessment-guide__lead">
          Diese Seite erklärt <strong>jedes Feld</strong>, das Sie in der Ergebnisansicht (rechte Leiste und
          „Verbesserte Version“) sehen — in einfachem Deutsch für Lernende auf B1/B2-Niveau. Die App orientiert sich am
          üblichen TELC-B2-Schreibformat; es ist ein Trainingstool, keine offizielle Prüfungsnote.
        </p>
      </header>

      <Card title="Inhaltsverzeichnis" className="assessment-guide__toc-card">
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

      <section id="overview" className="assessment-guide__anchor assessment-guide-section" tabIndex={-1}>
        <Card title="Überblick">
          <div className="stack stack--sm guide-prose">
            <p style={{ margin: 0 }}>
              Ihr Text wird in <strong>drei Kriterien</strong> betrachtet, die in der App klar getrennt angezeigt werden:
            </p>
            <ul className="assessment-guide__list">
              <li>
                <strong>I — Aufgabenerfüllung:</strong> Haben Sie die Leitpunkte und die eigene Idee sinnvoll bearbeitet?
              </li>
              <li>
                <strong>II — Kommunikative Gestaltung:</strong> Passt der Text als formelle E-Mail? Struktur, Ton,
                Verknüpfungen, Wortschatz, Satzvielfalt.
              </li>
              <li>
                <strong>III — Formale Korrektheit / Sprachrichtigkeit:</strong> Grammatik, Rechtschreibung usw. — und ob
                Fehler das Verständnis stören.
              </li>
            </ul>
            <p style={{ margin: 0 }}>
              Rechts sehen Sie pro Kriterium eine <strong>Zahl „X / 15“</strong> (skalierte Teilpunkte) und darunter
              Kommentare, Listen oder Ampelfarben. Unten im Hauptteil stehen Ihr Originaltext (mit Markierungen), die
              Aufgabe und ggf. eine <strong>verbesserte Fassung</strong> nur zum Üben.
            </p>
          </div>
        </Card>
      </section>

      <section id="result-overview" className="assessment-guide__anchor assessment-guide-section" tabIndex={-1}>
        <Card title="Thema passend, Situation passend, Zeit">
          <div className="stack stack--sm guide-prose">
            <FieldBlock
              title="„Thema passend“ (Gut / Schlecht)"
              meaning='Die App prüft, ob Ihr Text zur gestellten Aufgabe und zum erwarteten Thema passt („topic_mismatch“ im Hintergrund). „Schlecht“ bedeutet: Der Inhalt verfehlt das Thema klar — das ist eine echte inhaltliche Bewertung, kein technischer Fehler.'
              conclusion="Bei „Schlecht“ ist oft mit sehr niedrigen Teilnoten zu rechnen; die Endnote kann trotzdem aus den Regeln der App berechnet werden (Themenverfehlung). Bei „Gut“ ist das Thema grundsätzlich getroffen — die Feinbewertung folgt in Kriterium I–III."
              improve="Lesen Sie die Aufgabe und die Situation zweimal. Schreiben Sie nur zu diesem Fall; wechseln Sie nicht zu einem anderen Produkt, Ort oder Problem."
            />
            <FieldBlock
              title="„Situation passend“ (Gut / Schlecht)"
              meaning="Hier geht es darum, ob Ihr Schreiben zur beschriebenen Situation passt (z. B. Reklamation vs. Information). „Schlecht“ kann bedeuten, dass der Text zur Situation nicht passt oder das Szenario ignoriert."
              conclusion="Wenn beides „Gut“ ist, können Sie sich auf Leitpunkte und Sprache konzentrieren. Wenn eines „Schlecht“ ist, lohnt sich ein inhaltlicher Neustart: Weniger generelle Floskeln, mehr Bezug zur Aufgabenstellung."
              improve="Nennen Sie konkret, wer Sie sind, was passiert ist und was Sie von der Gegenstelle erwarten — immer passend zur Aufgabenfigur (Kunde, Mieter, Leser …)."
            />
            <FieldBlock
              title="„Zeit“ (Minuten)"
              meaning={
                <>
                  Das ist die <strong>Schreibzeit in dieser App</strong>: vom Start der Aufgabe bis zur Einreichung
                  (Session). Sie dient Ihrer Selbstkontrolle beim Training, nicht einer offiziellen Prüfungszeit. Ab etwa 30
                  Minuten kann die Anzeige warnend wirken — das ist ein Hinweis, lange Pausen oder sehr langsames Arbeiten
                  zu überdenken.
                </>
              }
              conclusion="Kurze Zeit heißt nicht automatisch schlechte Note; lange Zeit heißt nicht automatisch gute Note. Es ist nur Kontext für Ihr Training."
              improve="Üben Sie einmal mit Timer: zuerst Plan (2–3 Min.), dann Schreiben, zuletzt Korrekturlesen — so wird die Zeit realistischer."
            />
          </div>
        </Card>
      </section>

      <section id="score-interpretation" className="assessment-guide__anchor assessment-guide-section" tabIndex={-1}>
        <Card title="Endnote (Zahl rechts oben)">
          <div className="stack stack--sm guide-prose">
            <FieldBlock
              title="„Endnote“ als „X / 45“ oder Striche"
              meaning={
                <>
                  Die <strong>Endnote</strong> ist die skalierte Gesamtpunktzahl: Summe der drei Rohpunkte (je 0–5) × 3,
                  maximal 45. Steht dort „—“, wurde keine volle Zahl berechnet — z. B. bei technischer Teilauswertung.
                </>
              }
              conclusion="Hohe Werte (z. B. über 36) deuten auf insgesamt solide bis starke Leistung; niedrige Werte zeigen klare Lücken in Inhalt, Gestaltung oder Sprache — je nach Kriterienkarten."
              improve="Vergleichen Sie die drei Karten I/II/III: Wo ist die kleinste Zahl? Dort zuerst trainieren, statt nur an der Endnote zu „drehen“."
            />
            <FieldBlock
              title="Farben neben der Endnote (Ampel)"
              meaning={
                <>
                  Grün / Gelb / Rot fasst nur das <strong>Verhältnis Endnote zu 45</strong> grob zusammen (ca. ≥80 % grün,
                  ≥60 % gelb, sonst rot). Es ersetzt keine offizielle TELC-Skala.
                </>
              }
              conclusion="Gelb bedeutet nicht „durchgefallen“, sondern: Es gibt noch Luft nach oben. Rot heißt: gezielt üben."
              improve="Setzen Sie sich konkrete Teilziele (z. B. erst 150 Wörter stabil, dann Leitpunkte vertiefen)."
            />
            <FieldBlock
              title="„X / 15“ auf den Karten I, II, III"
              meaning={
                <>
                  Pro Kriterium werden bis zu 5 Rohpunkte vergeben; in der Anzeige stehen oft{" "}
                  <strong>skalierte Punkte</strong> (×3), also maximal 15. Entspricht der Note: A=15, B=9, C=3, D=0 in
                  dieser Skala.
                </>
              }
              conclusion="Wenn dort „— / —“ steht, wurde dieses Kriterium nicht numerisch bewertet (z. B. technischer Fehler)."
              improve="Arbeiten Sie Kriterium für Kriterium: Inhalt zuerst stimmig, dann Höflichkeit und Struktur, zuletzt Feinschliff bei Grammatik und Zeichensetzung."
            />
          </div>
        </Card>
      </section>

      <section id="scoring" className="assessment-guide__anchor assessment-guide-section" tabIndex={-1}>
        <Card title="Notenstufen A–D und Formel (Hintergrund)">
          <div className="stack stack--sm guide-prose">
            <p style={{ margin: 0 }}>Pro Kriterium gilt in der App eine Stufe mit Rohpunkten:</p>
            <ul className="assessment-guide__list">
              <li>
                <strong>A</strong> = 5 Punkte
              </li>
              <li>
                <strong>B</strong> = 3 Punkte
              </li>
              <li>
                <strong>C</strong> = 1 Punkt
              </li>
              <li>
                <strong>D</strong> = 0 Punkte
              </li>
            </ul>
            <p style={{ margin: 0 }}>
              <strong>Endnote</strong> = (Punkte<sub>I</sub> + Punkte<sub>II</sub> + Punkte<sub>III</sub>) × 3,{" "}
              <strong>Maximum</strong> 45.
            </p>
            <p style={{ margin: 0 }}>
              <strong>Wichtig:</strong> Eine echte Note D kommt aus der Bewertungslogik (Inhalt/Sprache). Ein{" "}
              <strong>technischer Ausfall</strong> einer Teilprüfung ist <em>keine</em> automatische D-Note — siehe Abschnitt
              „Teilweise / fehlgeschlagen“.
            </p>
            <p style={{ margin: 0 }}>
              <strong>Themenverfehlung:</strong> Wenn das Thema klar nicht zur Aufgabe passt, kann das System inhaltlich mit
              D-Stufen arbeiten — das ist eine inhaltliche Entscheidung, keine Störung der Technik.
            </p>
          </div>
        </Card>
      </section>

      <section id="word-count" className="assessment-guide__anchor assessment-guide-section" tabIndex={-1}>
        <Card title="Wortzahl (150)">
          <div className="stack stack--sm guide-prose">
            <FieldBlock
              title="„Wortzahl: … / 150“"
              meaning={
                <>
                  Die App zählt Wörter im eingereichten Text und vergleicht mit der{" "}
                  <strong>Mindestgrenze 150</strong>. Die Farbe zeigt, ob die Grenze erreicht ist.
                </>
              }
              conclusion="Unter 150 Wörtern kann die Bewertung in dieser App die Endnote besonders behandeln oder auf 0 setzen (Projektregel zur Mindestlänge). Das ist eine Trainingsregel, damit Sie realistische Prüfungslängen üben."
              improve="Schreiben Sie zuerst den Hauptteil, zählen Sie, ergänzen Sie begründende Sätze (nicht nur Füllwörter), und prüfen Sie die Grenze vor dem Absenden."
            />
          </div>
        </Card>
      </section>

      <section id="partial-failed-results" className="assessment-guide__anchor assessment-guide-section" tabIndex={-1}>
        <Card title="Warnhinweise: Teilbewertung, analysis_status, analysis_error">
          <div className="stack stack--sm guide-prose">
            <FieldBlock
              title="Gelber Kasten mit längerem Text"
              meaning={
                <>
                  Wenn die Auswertung <strong>teilweise</strong> oder <strong>technisch fehlgeschlagen</strong> ist, zeigt die
                  App eine Meldung. Im Hintergrund stehen Felder wie <code className="assessment-guide__code">analysis_status</code>{" "}
                  (z. B. „partial“ oder „failed“) und{" "}
                  <code className="assessment-guide__code">analysis_error</code> (kurze technische oder zusammengefasste
                  Erklärung).
                </>
              }
              conclusion={
                <>
                  Das bedeutet: Mindestens ein Teil der KI-Auswertung konnte nicht zuverlässig fertiggestellt werden. Ihre
                  Note ist dann <strong>keine vollständige Prüfungsnote</strong>; die Endnote kann fehlen.
                </>
              }
              improve="Text erneut einreichen oder später versuchen. Wenn es oft passiert, Verbindung oder Dienst prüfen — die Bewertungsregeln selbst haben Sie damit nicht „verschlechtert“."
            />
            <FieldBlock
              title="Einzelkriterium „technisch fehlgeschlagen“"
              meaning={
                <>
                  Steht bei einem Kriterium keine Punktzahl und eine Fehlermeldung, wurde{" "}
                  <strong>nur dieses Kriterium</strong> nicht ausgewertet — nicht dasselbe wie Note D.
                </>
              }
              conclusion="Sie sehen ehrlich: „Hier fehlen Daten.“ Das ist transparenter, als eine erfundene Note einzusetzen."
              improve="Kriterien mit gültiger Bewertung trotzdem lesen und daraus lernen; fehlendes Kriterium später erneut versuchen."
            />
          </div>
        </Card>
      </section>

      <section id="criterion-i" className="assessment-guide__anchor assessment-guide-section" tabIndex={-1}>
        <Card title="Kriterium I — Aufgabenerfüllung (Karte & Kommentar)">
          <div className="stack stack--sm guide-prose">
            <FieldBlock
              title="Überschrift „Aufgabenerfüllung“ und „X / 15“"
              meaning={
                <>
                  Das ist Ihre Bewertung für <strong>Inhalt und Leitpunkte</strong>. Die Zahl ist wie oben beschrieben
                  skaliert (max. 15).
                </>
              }
              conclusion="Niedrige Werte zeigen: Leitpunkte fehlen, sind zu oberflächlich oder passen nicht zur Aufgabe."
              improve="Planen Sie vor dem Schreiben: ein Absatz oder Abschnitt pro Leitpunkt plus eine eigene sinnvolle Idee."
            />
            <FieldBlock
              title="Fließtext-Kommentar unter der Überschrift"
              meaning="Kurze Zusammenfassung der KI: Was ist gut gelaufen, wo fehlt Tiefe oder Bezug?"
              conclusion="Lesen Sie den Kommentar als Checkliste, nicht als persönliche Kritik."
              improve="Übernehmen Sie 1–2 konkrete Verbesserungsideen direkt in eine zweite Version Ihres Textes."
            />
          </div>
        </Card>
      </section>

      <section id="task-achievement-fields" className="assessment-guide__anchor assessment-guide-section" tabIndex={-1}>
        <Card title="Erfüllte Punkte, Sprachniveau, Punkt 1–4, Eigener Aspekt">
          <div className="stack stack--sm guide-prose">
            <FieldBlock
              title="„Erfüllte Punkte“"
              meaning={
                <>
                  Zählt, wie viele <strong>vorgegebene Leitpunkte</strong> den Status „erfüllt“ haben (nicht die eigene Idee).
                </>
              }
              conclusion="Eine kleine Zahl heißt: Mehrere geforderte Inhaltspunkte sind noch nicht ausreichend ausgearbeitet."
              improve={
                <>
                  Jeden Leitpunkt mit mindestens <strong>2–3 vollständigen Sätzen</strong> belegen — Einleitung, Beispiel,
                  Folge oder Bitte im Kontext.
                </>
              }
            />
            <FieldBlock
              title="„Sprachniveau“ (z. B. B2, B1+ …)"
              meaning={
                <>
                  Einschätzung, auf welchem Niveau die <strong>inhaltlichen Leitpunkt-Texte</strong> wirken (Wortschatz und
                  Satzbau in den relevanten Stellen), orientiert an B2.
                </>
              }
              conclusion="B1 oder A2 bei Inhalten bedeutet: zu einfach oder zu unsicher für eine starke B2-Aufgabenlösung — unabhängig von Grammatik in Kriterium III."
              improve="Verwenden Sie präzisere Verben und Nomen (z. B. statt „Problem“: „Lieferverzug“, „beschädigte Ware“), verknüpfen Sie Sätze mit weil, damit, obwohl."
            />
            <FieldBlock
              title="„Mehr als ein Satz“ pro Leitpunkt"
              meaning={
                <>
                  Ein einziger kurzer Satz reicht selten, um einen Leitpunkt als inhaltlich „erfüllt“ zu zeigen. Die
                  Prüfungslogik erwartet <strong>Ausarbeitung</strong>.
                </>
              }
              conclusion="Wenn die App „teilweise erfüllt“ oder „nicht erfüllt“ meldet, liegt es oft an zu wenig Text pro Punkt."
              improve="Muster: (1) Sachverhalt nennen, (2) näher erklären oder begründen, (3) Folge oder Bitte formulieren."
            />
            <FieldBlock
              title="„B2-Niveau“ beim Inhalt"
              meaning="Gemeint ist: Sinnvoller Wortschatz und Satzbau, mit dem man in einem realen B2-Alltag oder in einer Prüfung dieselbe Aufgabe bewältigen könnte — nicht perfekte Fehlerfreiheit, aber tragfähige Sprache."
              conclusion="Zu einfache Ketten („Ich bin traurig. Ich schreibe Brief. Ich will Hilfe.“) reichen selten für „erfüllt“."
              improve="Nebensätze üben, feste Wendungen nutzen (ich möchte darauf hinweisen, ich wäre Ihnen dankbar, ich erwarte)."
            />
            <FieldBlock
              title="„Punkt 1“, „Punkt 2“, … (aufklappbare Karten)"
              meaning={
                <>
                  Jeder Eintrag gehört zu einem <strong>geforderten Leitpunkt</strong> aus der Aufgabe. Dort sehen Sie
                  Kurzkommentar, Status, Satzzahl, Niveau, ob es zur Situation passt.
                </>
              }
              conclusion="„Erfüllt“ = der Punkt ist inhaltlich und sprachlich tragfähig bearbeitet. „Teilweise erfüllt“ = angefangen, aber zu dünn oder unscharf. „Nicht erfüllt“ = fehlt oder verfehlt die Aufgabe."
              improve="Arbeiten Sie genau die roten/schwachen Felder zuerst: mehr Beispiele, Zahlen, Daten, klare Erwartung."
            />
            <FieldBlock
              title="„Eigener Aspekt“"
              meaning={
                <>
                  Eine <strong>eigene, sinnvolle Idee</strong> zur Situation (nicht nur Abschrift der Aufgabe). Sie zeigt,
                  dass Sie selbst denken.
                </>
              }
              conclusion="Fehlt sie oft, sinkt Kriterium I — auch wenn die drei Pflichtpunkte halb okay sind."
              improve="Formulieren Sie eine konkrete, höfliche Forderung oder Alternative (z. B. Ersatzlieferung, Termin, Kulanz), die zur Rolle passt."
            />
          </div>
        </Card>
      </section>

      <section id="criterion-ii" className="assessment-guide__anchor assessment-guide-section" tabIndex={-1}>
        <Card title="Kriterium II — Kommunikative Gestaltung (Karte)">
          <div className="stack stack--sm guide-prose">
            <FieldBlock
              title="Karte „Kommunikative Gestaltung“"
              meaning={
                <>
                  Hier geht es nicht um einzelne Rechtschreibfehler, sondern um <strong>E-Mail-Tauglichkeit</strong>: Aufbau,
                  Logik, Ton, Wortschatz, Abwechslung der Sätze.
                </>
              }
              conclusion="Hohe Teilpunktzahl = der Text wirkt wie eine überzeugende, höfliche E-Mail; niedrige = Struktur oder Ton sind schwach oder unpassend."
              improve="Lesen Sie eine echte E-Mail eines Dienstes als Vorbild: kurze Absätze, eine klare Bitte, höfliche Sie-Anrede, keine Umgangssprache."
            />
          </div>
        </Card>
      </section>

      <section id="communication-fields" className="assessment-guide__anchor assessment-guide-section" tabIndex={-1}>
        <Card title="Felder unter Kriterium II (Indikatoren & Skala)">
          <div className="stack stack--sm guide-prose">
            <p style={{ margin: 0 }}>
              Unter der Überschrift zeigt die App eine Liste von <strong>Hinweisen mit deutscher Bezeichnung</strong>. Die
              App nutzt englische Schlüsselwörter im Hintergrund; typische Labels in der Oberfläche sind z. B.:
            </p>
            <ul className="assessment-guide__list">
              <li>
                <strong>E-Mail-Elemente</strong> — Betreff, Anrede, Gruß, klare Anredeform usw.
              </li>
              <li>
                <strong>Struktur</strong> — logischer Aufbau in Absätzen, erkennbare Teile (Einleitung – Hauptteil – Schluss).
              </li>
              <li>
                <strong>Zusammenhang</strong> — die Ideenfolge ist für den Leser nachvollziehbar.
              </li>
              <li>
                <strong>Verknüpfungen</strong> — Konnektoren und Pronomen verbinden Sätze (deshalb, außerdem, trotzdem …).
              </li>
              <li>
                <strong>Register und Stil</strong> — formell, höflich, zur Situation passend (kein Du zu einer Behörde).
              </li>
              <li>
                <strong>Wortschatz</strong> — Niveau und Passung der Wortwahl.
              </li>
              <li>
                <strong>Satzvielfalt</strong> — Wechsel zwischen kurzen und längeren Sätzen, nicht nur monotone Hauptsätze.
              </li>
            </ul>
            <h4 className="assessment-guide__subsection-title">Bewertungsstufen (englisch → deutsch in der App)</h4>
            <ul className="assessment-guide__list">
              <li>
                <strong>excellent</strong> → „sehr gut“: vorbildlich für diese Teilaufgabe.
              </li>
              <li>
                <strong>good</strong> → „gut“: klar über dem Minimum.
              </li>
              <li>
                <strong>acceptable</strong> → „akzeptabel“: es geht, aber genau hier lohnt Übung — oft fehlt Feinschliff
                oder Klarheit.
              </li>
              <li>
                <strong>weak</strong> → „schwach“: der Leser merkt deutliche Schwächen.
              </li>
              <li>
                <strong>missing</strong> → „fehlt“: wichtiger Teil fehlt (z. B. kein sinnvoller Betreff).
              </li>
            </ul>
            <FieldBlock
              title="„Wortschatz“ mit Niveau B2 / B1+ / B1 / A2"
              meaning={
                <>
                  Das ist eine <strong>globale Einschätzung</strong> des Wortschatzes in Ihrer E-Mail, nicht einzelne Wörter
                  zählen.
                </>
              }
              conclusion="A2/B1 signalisiert: für die erwartete B2-Aufgabe noch zu einfach oder zu unsicher."
              improve="Themenwortschatz sammeln (Reklamation: Lieferung, Beschädigung, Ersatz, Kulanz …) und in Sätzen üben, nicht nur isoliert."
            />
            <FieldBlock
              title="Wenn „Verknüpfungen“ oder „Satzvielfalt“ schwach sind"
              meaning="Der Text wirkt holprig oder monoton; der Leser muss mehr raten."
              conclusion="Das senkt Kriterium II, auch wenn Grammatik „okay“ wirkt."
              improve="Pro Absatz mindestens einen Konnektor setzen; bewusst einen Nebensatz mit obwohl/weil/damit einbauen; Satzlängen wechseln."
            />
          </div>
        </Card>
      </section>

      <section id="criterion-iii" className="assessment-guide__anchor assessment-guide-section" tabIndex={-1}>
        <Card title="Kriterium III — Formale Korrektheit (Karte)">
          <div className="stack stack--sm guide-prose">
            <FieldBlock
              title="Karte „Formale Korrektheit“"
              meaning="Hier werden sprachliche Teilbereiche und deren Einfluss aufs Verständnis betrachtet — zusammen mit der Gesamtnote des Kriteriums."
              conclusion="Viele „schwach“ oder „problematisch“-Felder führen fast immer zu schlechteren Teilnoten — auch wenn der Inhalt gut gemeint ist."
              improve="Erst häufige Fehlerarten angehen (Artikel, Verb an zweiter Stelle, Kommas bei Nebensätzen), dann Feinschliff."
            />
          </div>
        </Card>
      </section>

      <section id="accuracy-fields" className="assessment-guide__anchor assessment-guide-section" tabIndex={-1}>
        <Card title="Teilaspekte & Anzeige gut / ausreichend / schwach / problematisch">
          <div className="stack stack--sm guide-prose">
            <p style={{ margin: 0 }}>
              In der App werden technische Stufen (strong, adequate, weak, problematic) mit deutschen Kurzlabels
              angezeigt:
            </p>
            <ul className="assessment-guide__list">
              <li>
                <strong>strong</strong> → „gut“
              </li>
              <li>
                <strong>adequate</strong> → „ausreichend“
              </li>
              <li>
                <strong>weak</strong> → „schwach“
              </li>
              <li>
                <strong>problematic</strong> → „problematisch“
              </li>
            </ul>
            <FieldBlock
              title="Grammatik"
              meaning="Verbformen, Kasus, Satzstruktur — ob Sätze verständlich und regelkonform gebaut sind."
              conclusion="„Problematisch“: Fehler stören oft den Sinn oder häufen sich stark."
              improve="Satz für Satz langsam lesen; typische Muster notieren (z. B. Genitiv/Wechselpräpositionen)."
            />
            <FieldBlock
              title="Satzbau (Syntax)"
              meaning="Passt der Satzbau zur Absicht (Haupt- und Nebensätze, keine Sackgassen)?"
              conclusion="Schwach = der Leser muss umstellen oder rät."
              improve="Lange Sätze in zwei kürzere teilen; Prüfen, ob jedes Verb ein Subjekt hat."
            />
            <FieldBlock
              title="Wortstellung"
              meaning="Verb-Position in Aussage- und Nebensätzen, klare Reihenfolge der Satzteile."
              conclusion="Häufige falsche Verbstellung senkt Verständlichkeit stark."
              improve="Regel „Verb auf Position 2“ und „Verb am Ende im Nebensatz“ gezielt üben."
            />
            <FieldBlock
              title="Verbformen"
              meaning="Zeitform, Konjunktiv/Modalverben, Passiv falls verwendet — korrekt und passend?"
              conclusion="Systematische Verbfehler wirken unsicher und können C oder D begünstigen."
              improve="Liste der unregelmäßigen Verben, die Sie oft brauchen; eine Zeitform pro Absatz nicht wild mischen."
            />
            <FieldBlock
              title="Kongruenz"
              meaning="Artikel, Genus, Numerus, Adjektivendungen passen zusammen."
              conclusion="Viele Kongruenzfehler machen den Text „holprig“ und weniger überzeugend."
              improve="Substantive mit Artikel laut lernen; Adjektivendungen in einer Spalte üben (der/die/das + Adjektiv)."
            />
            <FieldBlock
              title="Rechtschreibung"
              meaning="Wörterbuchnahe Schreibweise; Tippfehler vs. echte Unsicherheit."
              conclusion="Viele Fehler lenken ab, auch wenn der Inhalt stimmt."
              improve="Kurz pause nach jedem Absatz: nur Rechtschreibung scannen; Browser-Rechtschreibprüfung nutzen, aber nicht blind vertrauen."
            />
            <FieldBlock
              title="Zeichensetzung"
              meaning="Kommas, Punkte, Doppelpunkt bei Anrede — helfen dem Leser, Sinngrenzen zu sehen."
              conclusion="Fehlende Kommas bei Nebensätzen sind ein typischer B2-Schwachpunkt."
              improve="Ein Merkmal: nach weil, dass, obwohl … kommt oft das Verb ans Satzende — Komma davor setzen."
            />
            <FieldBlock
              title="Großschreibung"
              meaning="Nomen und Satzanfänge groß; Eigennamen korrekt."
              conclusion="Klein geschriebene Nomen wirken schnell „unsauber“ in formeller E-Mail."
              improve="Beim Korrekturlesen nur nach Großbuchstaben am Wortanfang suchen (Nomen-Scan)."
            />
            <FieldBlock
              title="Verständlichkeit"
              meaning="Ob Fehler den Lesefluss oder sogar den Sinn trüben („comprehension“)."
              conclusion="„Problematisch“ hier ist ein Warnsignal: Inhalt könnte falsch verstanden werden."
              improve="Unklare Sätze umschreiben; Fachbegriffe nur nutzen, wenn sie zur Aufgabe passen und erklärt sind."
            />
          </div>
        </Card>
      </section>

      <section id="error-marking" className="assessment-guide__anchor assessment-guide-section" tabIndex={-1}>
        <span id="highlighted-errors" className="assessment-guide__sr-anchor" aria-hidden="true" />
        <Card title="Markierte Fehler (in „Ihrer Antwort“ und in der Leiste)">
          <div className="stack stack--sm guide-prose">
            <FieldBlock
              title="Was „markiert“ ist"
              meaning={
                <>
                  Die App wählt <strong>konkrete kurze Textfragmente</strong> aus Ihrem Original und hebt sie farblich hervor.
                  Das sind Beispiele, keine vollständige Fehlerliste.
                </>
              }
              conclusion="Nicht jeder Fehler erscheint; die Liste ist begrenzt und priorisiert oft die auffälligsten Stellen."
              improve="Vergleichen Sie jeden markierten Bereich mit der Erklärung und bauen Sie die Korrektur in eine neue Version ein."
            />
            <FieldBlock
              title="„Fehler“ (Originalfragment)"
              meaning="Genau der Ausschnitt aus Ihrem Text, an dem etwas nicht dem Ziel (meist Standarddeutsch in der Aufgabe) entspricht."
              conclusion="Wenn das Fragment sehr lang ist, ist oft eine unsaubere Stelle mitten drin gemeint."
              improve="Formulieren Sie die Stelle neu — kürzer und klarer ist oft besser."
            />
            <FieldBlock
              title="„Korrektur“"
              meaning="Ein Vorschlag, wie der Ausschnitt regelkonformer oder natürlicher klingen könnte."
              conclusion="Es gibt manchmal mehrere richtige Lösungen; der Vorschlag ist eine Lernhilfe."
              improve="Sagen Sie die Korrektur laut; wenn sie unnatürlich klingt, Wörterbuch oder Lehrer:in fragen."
            />
            <FieldBlock
              title="„Erklärung“"
              meaning="Kurze Regel oder Begründung (z. B. Kasus nach Verb, Zeitenfolge)."
              conclusion="Hilft Ihnen, das Muster zu erkennen — nicht nur diese eine Stelle."
              improve="Gleiche Regel an drei selbst gewählten neuen Sätzen üben."
            />
            <FieldBlock
              title="„error_type“ / Fehlerart (z. B. Verbform, Kasus …)"
              meaning="Eine kurze Kategorie, damit Sie Fehler sammeln können (z. B. Artikel/Kasus, Wortstellung, Großschreibung)."
              conclusion="Wiederholt derselbe Typ? Dann gezielt diese Regel lernen, nicht „alles Grammatik“."
              improve="Eigenes Fehler-Tagebuch: Spalten Typ, Beispiel, Korrektur, Regel-Link/Skript."
            />
          </div>
        </Card>
      </section>

      <section id="improved-text" className="assessment-guide__anchor assessment-guide-section" tabIndex={-1}>
        <Card title="Verbesserte Version (Lernhilfe)">
          <div className="stack stack--sm guide-prose">
            <FieldBlock
              title="Block „Verbesserte Version“"
              meaning={
                <>
                  Ein Volltext-Vorschlag, der Ihre Aussagen in der Regel <strong>beibehalten</strong> soll, aber klarer und
                  sprachlich sicherer formuliert.
                </>
              }
              conclusion={
                <>
                  Diese Version ist <strong>nicht</strong> die offizielle Bewertungsgrundlage und ändert{" "}
                  <strong>nicht</strong> Ihre Punkte nachträglich.
                </>
              }
              improve="Vergleichen Sie Absatz für Absatz: Was wurde geglättet? Übernehmen Sie Wendungen, die Sie verstehen und wiederverwenden können."
            />
            <FieldBlock
              title="Keine erfundenen Fakten"
              meaning="Die KI soll keine neuen konkreten Daten (Datum, Betrag, Produktname …) erfinden, die nicht in Ihrer Aufgabe stehen."
              conclusion="Wenn plötzlich Details auftauchen, die Sie nicht geschrieben haben, ignorieren Sie sie beim Lernen oder ersetzen Sie sie durch Ihre echten Angaben."
              improve="Immer mit Ihrer Aufgabenstellung abgleichen; nur Fakten behalten, die Sie selbst gemeint haben."
            />
          </div>
        </Card>
      </section>

      <section id="good-letter" className="assessment-guide__anchor assessment-guide-section" tabIndex={-1}>
        <Card title="Gute TELC-B2-E-Mail — Aufbau, Leitpunkte, Verknüpfungen">
          <div className="stack stack--sm guide-prose">
            <p style={{ margin: 0 }}>
              Eine starke Prüfungs-E-Mail ist <strong>sachlich, höflich und vollständig</strong>. Typischer Aufbau:
            </p>
            <ol className="assessment-guide__list assessment-guide__list--ordered">
              <li>
                <strong>Betreff</strong> — eine Zeile, die das Anliegen nennt.
              </li>
              <li>
                <strong>Anrede</strong> — z. B. „Sehr geehrte Damen und Herren,“ oder konkreter Name, wenn in der Aufgabe
                genannt.
              </li>
              <li>
                <strong>Einleitung</strong> — wer Sie sind und warum Sie schreiben (1–3 Sätze).
              </li>
              <li>
                <strong>Hauptteil</strong> — <strong>jeder Leitpunkt</strong> idealerweise mit <strong>2–3 Sätzen</strong>{" "}
                ausführen (Sachverhalt, Begründung, Konsequenz).
              </li>
              <li>
                <strong>Eigener Aspekt</strong> — wenn gefordert: eine sinnvolle eigene Idee oder Bitte, die zur Rolle passt.
              </li>
              <li>
                <strong>Klare Bitte / Erwartung</strong> — was genau soll die Gegenstelle tun? (Termin, Ersatz, Rückruf …)
              </li>
              <li>
                <strong>Schluss</strong> — ein höflicher Abschlussatz.
              </li>
              <li>
                <strong>Grußformel und Name</strong>.
              </li>
            </ol>
            <p style={{ margin: 0 }}>
              <strong>Nützliche Verknüpfungen und Wendungen</strong> (sparsam, aber wirkungsvoll einsetzen):
            </p>
            <ul className="assessment-guide__list">
              <li>
                <em>Zunächst</em> möchte ich …
              </li>
              <li>
                <em>Außerdem</em> …
              </li>
              <li>
                <em>Deshalb</em> / <em>aus diesem Grund</em> …
              </li>
              <li>
                <em>Trotzdem</em> / <em>jedoch</em> … (Kontrast)
              </li>
              <li>
                <em>Ich bitte Sie</em> (höflich) um … / <em>Ich wäre Ihnen dankbar</em>, wenn …
              </li>
            </ul>
            <p style={{ margin: 0 }}>
              <strong>Kurzvorlage</strong> (Platzhalter anpassen):
            </p>
            <pre className="text-panel assessment-guide__template" role="region" aria-label="Muster-E-Mail">
{`Betreff: [kurz Ihr Anliegen]

Sehr geehrte Damen und Herren,

ich wende mich an Sie, weil [Kernproblem in einem Satz].

Zunächst [Leitpunkt 1 ausführen, 2–3 Sätze].
Außerdem [Leitpunkt 2 ausführen, 2–3 Sätze].
[Optional: eigener sinnvoller Punkt / Vorschlag].

Aus diesem Grund bitte ich Sie, [klare Bitte / Frist / Erwartung].

Mit freundlichen Grüßen
[Ihr Name]`}
            </pre>
            <p style={{ margin: 0 }}>
              <strong>Kurztipps:</strong> formelles „Sie“; keine reine Stichpunktliste als Prüfungstext; Konnektoren nicht
              in jedem Satz wiederholen; am Ende einmal laut vorlesen — Ohr findet holprige Stellen oft schneller als das
              Auge.
            </p>
          </div>
        </Card>
      </section>
    </div>
  );
}
