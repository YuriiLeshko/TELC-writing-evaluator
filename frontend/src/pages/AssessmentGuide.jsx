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
  ["result-overview", "Thema, Situation und Zeit"],
  ["score-interpretation", "Punkte, Endnote und Wortzahl"],
  ["partial-failed-results", "Teilweise oder fehlgeschlagene Auswertung"],
  ["criterion-i", "Kriterium I: Aufgabenerfüllung"],
  ["criterion-ii", "Kriterium II: Kommunikative Gestaltung"],
  ["criterion-iii", "Kriterium III: Formale Korrektheit"],
  ["error-marking", "Markierte Fehler"],
  ["improved-text", "Verbesserte Version"],
  ["good-letter", "Gute TELC-B2-E-Mail"],
];

function Subheading({ children }) {
  return <h4 className="assessment-guide__subsection-title">{children}</h4>;
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
        <div className="page-subtitle assessment-guide__lead stack stack--sm">
          <p style={{ margin: 0 }}>
            Diese Seite erklärt, wie die Bewertung in dieser App funktioniert und wie Sie aus dem Ergebnis konkrete
            Verbesserungen ableiten können.
          </p>
          <p style={{ margin: 0 }}>
            Die App orientiert sich an TELC-B2-Schreibkriterien. Sie ist ein Trainingstool und ersetzt keine offizielle
            TELC-Bewertung.
          </p>
        </div>
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
            <p style={{ margin: 0 }}>Ihr Text wird in drei Bereichen bewertet:</p>
            <ul className="assessment-guide__list">
              <li>
                <strong>Kriterium I — Aufgabenerfüllung</strong>
                <br />
                Hier geht es um den Inhalt: Haben Sie die Aufgabe verstanden, die Leitpunkte bearbeitet und eine sinnvolle
                eigene Idee ergänzt?
              </li>
              <li>
                <strong>Kriterium II — Kommunikative Gestaltung</strong>
                <br />
                Hier geht es darum, ob Ihr Text als E-Mail gut funktioniert: Aufbau, roter Faden, Verknüpfungen, Register,
                Wortschatz und Satzvielfalt.
              </li>
              <li>
                <strong>Kriterium III — Formale Korrektheit</strong>
                <br />
                Hier geht es um sprachliche Genauigkeit: Grammatik, Satzbau, Wortstellung, Verbformen, Rechtschreibung,
                Zeichensetzung und Verständlichkeit.
              </li>
            </ul>
            <p style={{ margin: 0 }}>
              <strong>Wichtig:</strong> Die Kriterien werden getrennt betrachtet. Ein Text kann inhaltlich gut sein, aber
              sprachlich schwach. Oder er kann sprachlich relativ korrekt sein, aber die Aufgabe nicht vollständig erfüllen.
            </p>
          </div>
        </Card>
      </section>

      <section id="result-overview" className="assessment-guide__anchor assessment-guide-section" tabIndex={-1}>
        <Card title="Thema, Situation und Zeit">
          <div className="stack stack--sm guide-prose">
            <Subheading>Thema passend</Subheading>
            <p style={{ margin: 0 }}>Dieses Feld zeigt, ob Ihr Text grundsätzlich zur Aufgabe passt.</p>
            <p style={{ margin: 0 }}>
              Wenn das Thema verfehlt wurde, bedeutet das: Der Text behandelt nicht die geforderte Aufgabe oder nur sehr
              entfernt. In diesem Fall werden alle drei Kriterien mit D bewertet.
            </p>
            <p style={{ margin: 0 }}>Das ist kein technischer Fehler, sondern eine inhaltliche Bewertung.</p>
            <p style={{ margin: 0 }}>
              <strong>Was Sie daraus lernen können:</strong> Lesen Sie die Aufgabe vor dem Schreiben genau. Markieren Sie,
              worum es wirklich geht: Beschwerde, Bitte, Anfrage, Entschuldigung, Meinung oder Reaktion auf eine konkrete
              Situation.
            </p>

            <Subheading>Situation passend</Subheading>
            <p style={{ margin: 0 }}>Dieses Feld zeigt, ob die kommunikative Situation stimmt.</p>
            <p style={{ margin: 0 }}>
              <strong>Beispiel:</strong> Die Aufgabe verlangt eine formelle Beschwerde an einen Kundenservice. Wenn der Text
              stattdessen wie eine private Nachricht an einen Freund klingt, kann die Situation verfehlt sein.
            </p>
            <p style={{ margin: 0 }}>Wenn die Situation verfehlt wurde, gilt in dieser App:</p>
            <ul className="assessment-guide__list">
              <li>Kriterium I wird mit D bewertet.</li>
              <li>Kriterium II und III werden trotzdem normal bewertet.</li>
            </ul>
            <p style={{ margin: 0 }}>
              <strong>Was Sie daraus lernen können:</strong> Achten Sie auf drei Fragen: Wer schreibt? An wen wird
              geschrieben? Was soll mit dem Text erreicht werden?
            </p>

            <Subheading>Zeit</Subheading>
            <p style={{ margin: 0 }}>Die Zeit ist kein TELC-Bewertungskriterium. Sie beeinflusst die Punkte nicht direkt.</p>
            <p style={{ margin: 0 }}>Sie zeigt nur, wie lange Sie im Training ungefähr gebraucht haben.</p>
            <p style={{ margin: 0 }}>
              Eine sehr kurze Zeit kann bedeuten, dass der Text zu knapp, nicht kontrolliert oder nicht vollständig entwickelt
              ist. Eine lange Zeit garantiert aber keine bessere Bewertung.
            </p>
            <p style={{ margin: 0 }}>
              Für realistisches Training können Sie sich an einem vollständigen Schreibfenster von etwa 30–45 Minuten
              orientieren.
            </p>
          </div>
        </Card>
      </section>

      <section id="score-interpretation" className="assessment-guide__anchor assessment-guide-section" tabIndex={-1}>
        <Card title="Punkte, Endnote und Wortzahl">
          <div className="stack stack--sm guide-prose">
            <Subheading>Endnote</Subheading>
            <p style={{ margin: 0 }}>Die Endnote wird so berechnet:</p>
            <p style={{ margin: 0 }}>
              <strong>
                Endnote = (Kriterium I + Kriterium II + Kriterium III) × 3
              </strong>
            </p>
            <p style={{ margin: 0 }}>Jedes Kriterium bekommt zuerst Rohpunkte:</p>
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
            <p style={{ margin: 0 }}>Maximal sind 45 Punkte möglich.</p>
            <p style={{ margin: 0 }}>
              Steht in der App „—“ oder fehlt die Endnote, wurde keine vollständige Gesamtnote berechnet — zum Beispiel bei
              einer teilweise oder technisch fehlgeschlagenen Auswertung.
            </p>
            <p style={{ margin: 0 }}>
              Neben der Zahl zeigt die App oft eine Ampelfarbe (grob nach Anteil an 45). Das ersetzt keine offizielle
              TELC-Skala.
            </p>

            <span id="word-count" className="assessment-guide__sr-anchor" aria-hidden="true" />
            <Subheading>Punkte pro Kriterium</Subheading>
            <p style={{ margin: 0 }}>In der Ergebnisansicht sehen Sie pro Kriterium oft Werte wie:</p>
            <ul className="assessment-guide__list">
              <li>9 / 15</li>
              <li>3 / 15</li>
              <li>15 / 15</li>
            </ul>
            <p style={{ margin: 0 }}>
              Das sind skalierte Punkte. Ein Kriterium hat maximal 5 Rohpunkte. In der Anzeige werden sie mit 3 multipliziert.
            </p>
            <p style={{ margin: 0 }}>Also:</p>
            <ul className="assessment-guide__list">
              <li>A = 15 / 15</li>
              <li>B = 9 / 15</li>
              <li>C = 3 / 15</li>
              <li>D = 0 / 15</li>
            </ul>
            <p style={{ margin: 0 }}>
              Wenn dort „— / —“ steht, wurde dieses Kriterium nicht numerisch bewertet (z. B. technischer Fehler bei der
              Auswertung — nicht dasselbe wie Note D).
            </p>

            <Subheading>Wortzahl</Subheading>
            <p style={{ margin: 0 }}>Die App prüft, ob Ihr Text mindestens 150 Wörter hat.</p>
            <p style={{ margin: 0 }}>
              <strong>Wichtig:</strong> Mehr Wörter bedeuten nicht automatisch eine bessere Bewertung. Entscheidend ist, ob die
              Wörter sinnvoll sind.
            </p>
            <p style={{ margin: 0 }}>Ein guter Text braucht:</p>
            <ul className="assessment-guide__list">
              <li>entwickelte Leitpunkte;</li>
              <li>klare Beispiele oder Begründungen;</li>
              <li>passende Verknüpfungen;</li>
              <li>eine klare Bitte oder Erwartung;</li>
              <li>eine vollständige E-Mail-Struktur.</li>
            </ul>
            <p style={{ margin: 0 }}>
              Füllsätze helfen nicht. Wenn der Text unter 150 Wörtern bleibt, kann die Bewertung in dieser App stark
              eingeschränkt oder auf 0 gesetzt werden.
            </p>
          </div>
        </Card>
      </section>

      <section id="partial-failed-results" className="assessment-guide__anchor assessment-guide-section" tabIndex={-1}>
        <Card title="Teilweise oder fehlgeschlagene Auswertung">
          <div className="stack stack--sm guide-prose">
            <p style={{ margin: 0 }}>
              Manchmal kann ein Teil der automatischen Analyse technisch nicht abgeschlossen werden. Das ist nicht dasselbe
              wie eine schlechte Note.
            </p>
            <p style={{ margin: 0 }}>Wenn ein Kriterium technisch fehlgeschlagen ist:</p>
            <ul className="assessment-guide__list">
              <li>wird dieses Kriterium nicht bewertet;</li>
              <li>es bekommt keine künstliche D-Note;</li>
              <li>die Endnote kann fehlen;</li>
              <li>Sie sehen eine Fehlermeldung.</li>
            </ul>
            <p style={{ margin: 0 }}>
              <strong>Was Sie tun können:</strong> Reichen Sie den Text später erneut ein. Die gültigen Teile der Auswertung
              können Sie trotzdem zum Lernen verwenden.
            </p>
          </div>
        </Card>
      </section>

      <section id="criterion-i" className="assessment-guide__anchor assessment-guide-section" tabIndex={-1}>
        <Card title="Kriterium I: Aufgabenerfüllung">
          <div className="stack stack--sm guide-prose">
            <p style={{ margin: 0 }}>
              Kriterium I bewertet, ob Sie die Aufgabe inhaltlich erfüllt haben. Dabei geht es nicht nur darum, ob ein
              Leitpunkt irgendwo erwähnt wurde. Ein Leitpunkt zählt erst dann als erfüllt, wenn er wirklich ausgearbeitet ist.
            </p>

            <Subheading>Was ist ein Leitpunkt?</Subheading>
            <p style={{ margin: 0 }}>Ein Leitpunkt ist ein inhaltlicher Punkt, den die Aufgabe von Ihnen erwartet.</p>
            <p style={{ margin: 0 }}>
              <strong>Beispiel bei einer Beschwerde:</strong>
            </p>
            <ul className="assessment-guide__list">
              <li>Problem beschreiben</li>
              <li>Folgen erklären</li>
              <li>Lösung verlangen</li>
            </ul>

            <Subheading>Wann zählt ein Leitpunkt als erfüllt?</Subheading>
            <p style={{ margin: 0 }}>Ein Leitpunkt zählt nur dann als erfüllt, wenn er:</p>
            <ul className="assessment-guide__list">
              <li>direkt zur Aufgabe passt;</li>
              <li>zur Situation passt;</li>
              <li>mehr als nur kurz erwähnt wird;</li>
              <li>ausreichend konkret ist;</li>
              <li>sprachlich ungefähr auf B2-Niveau formuliert ist.</li>
            </ul>
            <p style={{ margin: 0 }}>Ein einzelner Satz reicht oft nicht.</p>
            <p style={{ margin: 0 }}>
              <strong>Schwach:</strong> Das Paket war kaputt.
            </p>
            <p style={{ margin: 0 }}>
              <strong>Besser:</strong> Das Paket kam beschädigt an. Beim Öffnen habe ich gesehen, dass auch das Gerät
              beschädigt war und nicht richtig funktioniert. Deshalb konnte ich es nicht wie geplant benutzen.
            </p>
            <p style={{ margin: 0 }}>
              Der zweite Text erklärt nicht nur das Problem, sondern entwickelt den Leitpunkt.
            </p>

            <Subheading>Unterschied zwischen „erfüllt“, „teilweise erfüllt“ und „nicht erfüllt“</Subheading>
            <ul className="assessment-guide__list">
              <li>
                <strong>Erfüllt</strong> bedeutet: Der Punkt ist klar, relevant, ausreichend entwickelt und passt zur
                Situation.
              </li>
              <li>
                <strong>Teilweise erfüllt</strong> bedeutet: Der Punkt ist erkennbar, aber zu kurz, zu allgemein oder nicht
                klar genug.
              </li>
              <li>
                <strong>Nicht erfüllt</strong> bedeutet: Der Punkt fehlt, passt nicht zur Aufgabe oder ist zu unverständlich.
              </li>
            </ul>
            <p style={{ margin: 0 }}>
              In der Ergebnisleiste zeigen aufklappbare Karten („Punkt 1“, „Punkt 2“, …) pro Leitpunkt Status, Satzzahl,
              Sprachniveau und Kurzkommentar.
            </p>

            <Subheading>Eigener Aspekt</Subheading>
            <p style={{ margin: 0 }}>
              Ein eigener Aspekt ist eine zusätzliche sinnvolle Idee, die zur Aufgabe passt. Er darf nicht einfach den
              Leitpunkt wiederholen. Er sollte die E-Mail besser machen.
            </p>
            <p style={{ margin: 0 }}>Gute eigene Aspekte können sein:</p>
            <ul className="assessment-guide__list">
              <li>eine konkrete Frist;</li>
              <li>eine Bitte um Rückmeldung;</li>
              <li>ein Vorschlag zur Lösung;</li>
              <li>ein Hinweis auf eine Konsequenz;</li>
              <li>eine höfliche Erwartung.</li>
            </ul>
            <p style={{ margin: 0 }}>
              <strong>Beispiel:</strong> Ich bitte Sie, mir innerhalb einer Woche mitzuteilen, ob ich ein Ersatzgerät bekomme
              oder den Kaufpreis zurückerhalte.
            </p>

            <Subheading>Wie verbessern Sie Kriterium I?</Subheading>
            <p style={{ margin: 0 }}>Nutzen Sie für jeden Leitpunkt diese einfache Struktur:</p>
            <ul className="assessment-guide__list">
              <li>Was ist passiert?</li>
              <li>Warum ist das wichtig?</li>
              <li>Was erwarten oder wünschen Sie?</li>
            </ul>
            <p style={{ margin: 0 }}>
              Wenn jeder Leitpunkt 2–3 sinnvolle Sätze bekommt, wird der Inhalt meistens deutlich stärker.
            </p>
          </div>
        </Card>
      </section>

      <section id="criterion-ii" className="assessment-guide__anchor assessment-guide-section" tabIndex={-1}>
        <Card title="Kriterium II: Kommunikative Gestaltung">
          <div className="stack stack--sm guide-prose">
            <p style={{ margin: 0 }}>
              Kriterium II bewertet, ob Ihr Text als E-Mail gut funktioniert. Hier geht es nicht primär um Grammatikfehler.
              Es geht darum, ob der Text klar, logisch, höflich und passend aufgebaut ist.
            </p>

            <Subheading>E-Mail-Elemente</Subheading>
            <p style={{ margin: 0 }}>Hier wird geprüft, ob der Text typische Elemente einer E-Mail enthält:</p>
            <ul className="assessment-guide__list">
              <li>Betreff;</li>
              <li>Anrede;</li>
              <li>Einleitung;</li>
              <li>Hauptteil;</li>
              <li>Schluss;</li>
              <li>Grußformel.</li>
            </ul>
            <p style={{ margin: 0 }}>Für eine hohe Bewertung sollte die E-Mail vollständig und klar erkennbar sein.</p>

            <Subheading>Struktur</Subheading>
            <p style={{ margin: 0 }}>Struktur bedeutet: Der Text ist sinnvoll aufgebaut.</p>
            <p style={{ margin: 0 }}>Eine gute Struktur sieht zum Beispiel so aus:</p>
            <ul className="assessment-guide__list">
              <li>Betreff</li>
              <li>Anrede</li>
              <li>Grund des Schreibens</li>
              <li>Beschreibung des Problems</li>
              <li>Erwartung oder Bitte</li>
              <li>höflicher Schluss</li>
              <li>Grußformel</li>
            </ul>
            <p style={{ margin: 0 }}>
              Schwache Struktur bedeutet: Die Informationen stehen ungeordnet, wirken zufällig oder springen zwischen Themen.
            </p>

            <Subheading>Zusammenhang</Subheading>
            <p style={{ margin: 0 }}>Zusammenhang bedeutet: Der Leser kann dem Gedankengang folgen.</p>
            <p style={{ margin: 0 }}>
              Ein Text mit gutem Zusammenhang hat einen roten Faden. Die Sätze passen logisch zusammen.
            </p>
            <p style={{ margin: 0 }}>
              <strong>Schwach:</strong> Das Paket war kaputt. Ich habe einen Kopfhörer bestellt. Ich will mein Geld. Der Service
              ist wichtig.
            </p>
            <p style={{ margin: 0 }}>
              <strong>Besser:</strong> Ich habe bei Ihnen einen Kopfhörer bestellt. Leider kam das Paket beschädigt an, und das
              Gerät funktioniert nicht richtig. Deshalb bitte ich Sie um eine schnelle Lösung.
            </p>

            <Subheading>Verknüpfungen</Subheading>
            <p style={{ margin: 0 }}>Verknüpfungen sind sprachliche Brücken zwischen Sätzen und Ideen.</p>
            <p style={{ margin: 0 }}>Nützliche Wörter sind zum Beispiel:</p>
            <p style={{ margin: 0 }}>
              außerdem, deshalb, trotzdem, jedoch, aus diesem Grund, zunächst, danach, weil, obwohl, damit, wenn
            </p>
            <p style={{ margin: 0 }}>
              Sie müssen nicht in jedem Satz einen Konnektor verwenden. Aber ohne Verknüpfungen wirkt der Text schnell wie eine
              Liste.
            </p>

            <Subheading>Register und Stil</Subheading>
            <p style={{ margin: 0 }}>Register bedeutet: Der Ton passt zur Situation.</p>
            <p style={{ margin: 0 }}>Bei einer formellen E-Mail sollte der Stil höflich und sachlich sein.</p>
            <p style={{ margin: 0 }}>
              <strong>Gut:</strong> Ich bitte Sie um eine zeitnahe Rückmeldung.
            </p>
            <p style={{ margin: 0 }}>
              <strong>Zu direkt oder unpassend:</strong> Schicken Sie mir sofort mein Geld zurück.
            </p>
            <p style={{ margin: 0 }}>
              Ein falsches oder sehr schwaches Register kann die Bewertung stark verschlechtern.
            </p>

            <Subheading>Wortschatz</Subheading>
            <p style={{ margin: 0 }}>
              Der Wortschatz zeigt, ob Sie passende und ausreichend präzise Wörter verwenden. Für B2 reicht es nicht, nur sehr
              einfache Wörter zu benutzen.
            </p>
            <p style={{ margin: 0 }}>
              <strong>Einfach:</strong> Das Ding ist kaputt.
            </p>
            <p style={{ margin: 0 }}>
              <strong>Besser:</strong> Das Gerät wurde beschädigt geliefert und ist nicht funktionsfähig.
            </p>
            <p style={{ margin: 0 }}>
              B2-Wortschatz bedeutet nicht, dass der Text kompliziert sein muss. Er soll genau, passend und natürlich klingen.
            </p>

            <Subheading>Satzvielfalt</Subheading>
            <p style={{ margin: 0 }}>
              Satzvielfalt bedeutet: Der Text besteht nicht nur aus sehr kurzen und ähnlichen Sätzen.
            </p>
            <p style={{ margin: 0 }}>
              <strong>Schwach:</strong> Ich habe bestellt. Das Paket kam. Es war kaputt. Ich bin nicht zufrieden.
            </p>
            <p style={{ margin: 0 }}>
              <strong>Besser:</strong> Ich habe letzte Woche einen Kopfhörer bestellt, der leider beschädigt angekommen ist. Da
              das Gerät nicht richtig funktioniert, bitte ich Sie um eine schnelle Lösung.
            </p>
            <p style={{ margin: 0 }}>Gute Satzvielfalt entsteht durch:</p>
            <ul className="assessment-guide__list">
              <li>Nebensätze mit weil, dass, obwohl, wenn;</li>
              <li>Infinitivkonstruktionen mit um … zu;</li>
              <li>unterschiedliche Satzanfänge;</li>
              <li>passende Konnektoren.</li>
            </ul>
            <p style={{ margin: 0 }}>
              Der Text soll auf B2-Niveau bleiben. Er muss nicht künstlich kompliziert werden.
            </p>

            <Subheading>Skala in der App (Kriterium II)</Subheading>
            <p style={{ margin: 0 }}>
              Für die einzelnen Bereiche nutzt die App Stufen, die in der Oberfläche oft so erscheinen:
            </p>
            <ul className="assessment-guide__list">
              <li>
                <strong>sehr gut</strong> — vorbildlich für diesen Teil
              </li>
              <li>
                <strong>gut</strong> — klar über dem Minimum
              </li>
              <li>
                <strong>akzeptabel</strong> — es funktioniert grundsätzlich, aber es fehlt noch Feinschliff oder Klarheit
              </li>
              <li>
                <strong>schwach</strong> — deutliche Schwächen
              </li>
              <li>
                <strong>fehlt</strong> — ein wichtiger Teil fehlt (z. B. kein sinnvoller Betreff)
              </li>
            </ul>

            <Subheading>Was bedeutet „akzeptabel“?</Subheading>
            <p style={{ margin: 0 }}>
              „Akzeptabel“ heißt nicht schlecht. Es bedeutet: Der Bereich funktioniert grundsätzlich, ist aber noch nicht stark
              genug für eine hohe Bewertung.
            </p>
            <p style={{ margin: 0 }}>
              Wenn mehrere Bereiche nur „akzeptabel“ oder „schwach“ sind, sinkt Kriterium II deutlich.
            </p>
          </div>
        </Card>
      </section>

      <section id="criterion-iii" className="assessment-guide__anchor assessment-guide-section" tabIndex={-1}>
        <Card title="Kriterium III: Formale Korrektheit">
          <div className="stack stack--sm guide-prose">
            <p style={{ margin: 0 }}>
              Kriterium III bewertet die sprachliche Richtigkeit. Hier geht es um Fehler in Grammatik, Satzbau, Wortstellung,
              Verbformen, Rechtschreibung und Zeichensetzung.
            </p>
            <p style={{ margin: 0 }}>
              Konkret <Link to="/assessment-guide#error-marking">markierte Stellen</Link> im Text sind Beispiele — nicht
              zwangsläufig jeder Fehler.
            </p>

            <Subheading>Bewertungsstufen</Subheading>
            <p style={{ margin: 0 }}>Die App verwendet kurze Einschätzungen (in der Anzeige z. B.):</p>
            <ul className="assessment-guide__list">
              <li>
                <strong>gut</strong> — der Bereich ist sicher; Fehler kommen kaum vor oder stören nicht
              </li>
              <li>
                <strong>ausreichend</strong> — es gibt Fehler, aber der Bereich ist insgesamt noch kontrolliert
              </li>
              <li>
                <strong>schwach</strong> — Fehler treten wiederholt auf und fallen deutlich auf
              </li>
              <li>
                <strong>problematisch</strong> — Fehler sind häufig oder schwer; sie können das Verständnis stören
              </li>
            </ul>

            <Subheading>Grammatik</Subheading>
            <p style={{ margin: 0 }}>Grammatik umfasst zum Beispiel:</p>
            <ul className="assessment-guide__list">
              <li>Artikel;</li>
              <li>Kasus;</li>
              <li>Präpositionen;</li>
              <li>Verbformen;</li>
              <li>Satzglieder.</li>
            </ul>
            <p style={{ margin: 0 }}>
              Wenn Grammatik schwach ist, prüfen Sie zuerst wiederkehrende Muster. Oft sind es nicht zehn verschiedene
              Probleme, sondern ein oder zwei Fehlerarten, die sich wiederholen.
            </p>

            <Subheading>Satzbau</Subheading>
            <p style={{ margin: 0 }}>
              Satzbau bedeutet: Sind die Sätze vollständig, logisch und grammatisch gebaut? Problematisch wird es, wenn Sätze
              abbrechen, zu lang werden oder grammatisch nicht zusammenpassen. Besser ist oft: einen sehr langen Satz in zwei
              klare Sätze teilen.
            </p>

            <Subheading>Wortstellung</Subheading>
            <p style={{ margin: 0 }}>Wortstellung betrifft vor allem die Position des Verbs.</p>
            <p style={{ margin: 0 }}>
              <strong>Wichtige Regeln:</strong> Im Hauptsatz steht das konjugierte Verb meistens auf Position 2. Im Nebensatz
              steht das konjugierte Verb am Ende.
            </p>
            <p style={{ margin: 0 }}>
              <strong>Falsch:</strong> weil ich habe ein Problem — <strong>Richtig:</strong> weil ich ein Problem habe
            </p>

            <Subheading>Verbformen</Subheading>
            <p style={{ margin: 0 }}>Hier geht es um Konjugation, Zeitformen, Modalverben, Partizipien, trennbare Verben.</p>
            <p style={{ margin: 0 }}>
              Wenn Verbformen schwach sind, üben Sie häufige Verben aus typischen TELC-Themen: bestellen, erhalten,
              reklamieren, erwarten, bitten, mitteilen.
            </p>

            <Subheading>Kongruenz</Subheading>
            <p style={{ margin: 0 }}>Kongruenz bedeutet: Wörter passen grammatisch zusammen.</p>
            <p style={{ margin: 0 }}>
              <strong>Falsch:</strong> ein Kopfhörer kaufen — <strong>Richtig:</strong> einen Kopfhörer kaufen
            </p>

            <Subheading>Rechtschreibung</Subheading>
            <p style={{ margin: 0 }}>
              Einzelne Tippfehler sind meist weniger schlimm. Viele wiederholte Rechtschreibfehler wirken aber unsicher und
              erschweren das Lesen.
            </p>

            <Subheading>Zeichensetzung</Subheading>
            <p style={{ margin: 0 }}>
              Besonders wichtig sind Kommas bei Nebensätzen, z. B.: Ich schreibe Ihnen, weil ich ein Problem mit meiner Bestellung
              habe.
            </p>

            <Subheading>Großschreibung</Subheading>
            <p style={{ margin: 0 }}>
              Im Deutschen werden Nomen, Satzanfänge und Eigennamen großgeschrieben. Häufige Fehler in diesem Bereich wirken in
              einer formellen E-Mail schnell unprofessionell.
            </p>

            <Subheading>Verständlichkeit</Subheading>
            <p style={{ margin: 0 }}>Verständlichkeit zeigt, ob die Fehler den Sinn stören.</p>
            <p style={{ margin: 0 }}>
              Wenn Verständlichkeit problematisch ist, sollte der nächste Schritt nicht sein, komplizierter zu schreiben.
              Besser ist: kürzere Sätze, klare Reihenfolge, bekannte Wörter, eindeutige Bezüge.
            </p>
          </div>
        </Card>
      </section>

      <section id="error-marking" className="assessment-guide__anchor assessment-guide-section" tabIndex={-1}>
        <span id="highlighted-errors" className="assessment-guide__sr-anchor" aria-hidden="true" />
        <Card title="Markierte Fehler">
          <div className="stack stack--sm guide-prose">
            <p style={{ margin: 0 }}>
              Die markierten Fehler sind konkrete Beispiele aus Ihrem Originaltext. Sie zeigen den fehlerhaften Ausschnitt,
              eine mögliche Korrektur, den Fehlertyp und eine kurze Erklärung.
            </p>
            <p style={{ margin: 0 }}>
              Die Liste enthält nicht unbedingt alle Fehler. Sie zeigt eine Auswahl wichtiger oder gut erkennbarer Probleme.
            </p>
            <Subheading>Wie nutzen Sie diese Fehler sinnvoll?</Subheading>
            <p style={{ margin: 0 }}>Suchen Sie nach Mustern.</p>
            <ul className="assessment-guide__list">
              <li>Wenn häufig „Wortstellung“ erscheint, üben Sie Verbposition.</li>
              <li>Wenn häufig „Kasus“ oder „Artikel“ erscheint, üben Sie Nomen mit Artikel und Fall.</li>
              <li>Wenn häufig „Großschreibung“ erscheint, machen Sie am Ende einen eigenen Korrekturdurchgang nur für Großbuchstaben.</li>
            </ul>
            <p style={{ margin: 0 }}>
              <strong>Ein guter Lernschritt ist:</strong> Fehler lesen — Korrektur verstehen — Regel notieren — drei neue eigene
              Beispielsätze bilden.
            </p>
          </div>
        </Card>
      </section>

      <section id="improved-text" className="assessment-guide__anchor assessment-guide-section" tabIndex={-1}>
        <Card title="Verbesserte Version">
          <div className="stack stack--sm guide-prose">
            <p style={{ margin: 0 }}>
              Die verbesserte Version ist eine Lernhilfe. Sie zeigt, wie Ihr Text klarer, korrekter und besser strukturiert
              klingen könnte. Sie ändert aber nicht nachträglich Ihre Bewertung.
            </p>
            <p style={{ margin: 0 }}>
              <strong>Wichtig:</strong> Die verbesserte Version soll Ihre ursprüngliche Absicht erhalten. Wenn Sie dort
              konkrete Fakten sehen, die Sie nicht gemeint haben, übernehmen Sie diese nicht.
            </p>
            <p style={{ margin: 0 }}>
              <strong>Nutzen Sie die Version so:</strong> Vergleichen Sie Absatz für Absatz. Markieren Sie gute Wendungen.
              Übernehmen Sie nur Formulierungen, die Sie verstehen. Schreiben Sie danach eine eigene zweite Version.
            </p>
          </div>
        </Card>
      </section>

      <section id="good-letter" className="assessment-guide__anchor assessment-guide-section" tabIndex={-1}>
        <Card title="Gute TELC-B2-E-Mail">
          <div className="stack stack--sm guide-prose">
            <p style={{ margin: 0 }}>
              Eine gute TELC-B2-E-Mail ist nicht perfekt und nicht übertrieben kompliziert. Sie ist vollständig, höflich,
              logisch und verständlich.
            </p>

            <Subheading>Typischer Aufbau</Subheading>
            <ul className="assessment-guide__list">
              <li>
                <strong>Betreff</strong> — kurz und konkret.
              </li>
              <li>
                <strong>Anrede</strong> — z. B.: Sehr geehrte Damen und Herren,
              </li>
              <li>
                <strong>Einleitung</strong> — warum schreiben Sie?
              </li>
              <li>
                <strong>Hauptteil</strong> — Leitpunkte bearbeiten; jeder wichtige Punkt sollte 2–3 sinnvolle Sätze bekommen.
              </li>
              <li>
                <strong>Eigener Aspekt</strong> — wenn passend: zusätzliche Idee, Bitte oder Erwartung.
              </li>
              <li>
                <strong>Klare Bitte oder Erwartung</strong> — was soll die andere Seite tun?
              </li>
              <li>
                <strong>Schluss</strong> — höflich abschließen.
              </li>
              <li>
                <strong>Grußformel</strong> — Mit freundlichen Grüßen, Name
              </li>
            </ul>

            <Subheading>Nützliche Formulierungen</Subheading>
            <ul className="assessment-guide__list">
              <li>Ich wende mich an Sie, weil …</li>
              <li>Ich möchte Sie darüber informieren, dass …</li>
              <li>Leider musste ich feststellen, dass …</li>
              <li>Aus diesem Grund bitte ich Sie um …</li>
              <li>Ich wäre Ihnen dankbar, wenn …</li>
              <li>Bitte teilen Sie mir mit, wie …</li>
              <li>Ich hoffe auf eine schnelle Rückmeldung.</li>
            </ul>

            <Subheading>Kurzes Muster</Subheading>
            <pre className="text-panel assessment-guide__template" role="region" aria-label="Muster-E-Mail B2">
              {`Betreff: Beschwerde wegen beschädigter Lieferung

Sehr geehrte Damen und Herren,

ich wende mich an Sie, weil ich mit meiner letzten Bestellung ein Problem habe. Das Paket ist beschädigt angekommen, und das bestellte Gerät funktioniert nicht richtig.

Zunächst möchte ich erklären, dass ich den Kopfhörer beruflich und privat nutzen wollte. Leider ist dies im aktuellen Zustand nicht möglich, da nur eine Seite Ton wiedergibt. Außerdem war bereits die Verpackung deutlich beschädigt.

Aus diesem Grund bitte ich Sie um eine schnelle Lösung. Ich wäre Ihnen dankbar, wenn Sie mir entweder ein Ersatzgerät schicken oder den Kaufpreis zurückerstatten könnten.

Bitte teilen Sie mir mit, wie ich weiter vorgehen soll.

Mit freundlichen Grüßen
Max Müller`}
            </pre>

            <Subheading>Checkliste vor dem Absenden</Subheading>
            <ul className="assessment-guide__list">
              <li>Habe ich alle Leitpunkte bearbeitet?</li>
              <li>Hat jeder wichtige Leitpunkt mindestens zwei sinnvolle Sätze?</li>
              <li>Ist klar, warum ich schreibe?</li>
              <li>Ist meine Bitte oder Erwartung konkret?</li>
              <li>Gibt es Betreff, Anrede und Grußformel?</li>
              <li>Habe ich passende Verknüpfungen benutzt?</li>
              <li>Ist der Stil höflich und formell?</li>
              <li>Habe ich Verbposition, Artikel, Großschreibung und Kommas geprüft?</li>
            </ul>
            <p style={{ margin: 0 }}>
              Eine starke B2-E-Mail muss nicht wie C1 klingen. Sie muss die Aufgabe vollständig, klar und höflich lösen.
            </p>
          </div>
        </Card>
      </section>
    </div>
  );
}
