/**
 * Normalize whitespace and typographic quotes for fuzzy matching (aligned with Streamlit helper).
 * @param {string} text
 */
function canonicalizeWithMap(text) {
  const translation = {
    "\u2018": "'",
    "\u2019": "'",
    "\u201c": '"',
    "\u201d": '"',
    "\u2013": "-",
    "\u2014": "-",
    "\u00a0": " ",
  };
  const canonicalChars = [];
  const indexMap = [];
  let prevSpace = false;
  for (let idx = 0; idx < text.length; idx++) {
    const char = text[idx];
    const mapped = translation[char] ?? char;
    for (const piece of mapped) {
      if (/\s/.test(piece)) {
        if (prevSpace) continue;
        canonicalChars.push(" ");
        indexMap.push(idx);
        prevSpace = true;
      } else {
        canonicalChars.push(piece);
        indexMap.push(idx);
        prevSpace = false;
      }
    }
  }
  return { canonical: canonicalChars.join(""), indexMap };
}

function canonicalizeFragment(fragment) {
  const { canonical } = canonicalizeWithMap(fragment);
  return canonical.trim();
}

/**
 * @param {unknown[]} highlightedErrors GrammarErrorSpan-like { text } or raw strings
 */
function collectFragments(highlightedErrors) {
  if (!Array.isArray(highlightedErrors)) return [];
  const out = [];
  for (const item of highlightedErrors) {
    if (typeof item === "string") {
      const t = item.trim();
      if (t) out.push(t);
    } else if (item && typeof item === "object" && typeof item.text === "string") {
      const t = item.text.trim();
      if (t) out.push(t);
    }
  }
  return out;
}

/**
 * Build merged highlight spans in original string indices using canonical matching.
 * @param {string} text
 * @param {string[]} fragments
 * @returns {{ spans: [number, number][], missing: string[] }}
 */
function findSpans(text, fragments) {
  const { canonical: cText, indexMap } = canonicalizeWithMap(text);
  const lowered = cText.toLowerCase();
  const spans = [];
  const missing = [];
  const seen = new Set();

  for (const fragment of fragments) {
    if (seen.has(fragment)) continue;
    seen.add(fragment);
    const canonFrag = canonicalizeFragment(fragment);
    if (!canonFrag) continue;
    const escaped = canonFrag.replace(/[.*+?^${}()|[\]\\]/g, "\\$&").replace(/\\\s+/g, "\\s+");
    let found = false;
    const re = new RegExp(escaped, "giu");
    let m;
    while ((m = re.exec(lowered)) !== null) {
      const startC = m.index;
      const endC = m.index + m[0].length;
      if (startC >= indexMap.length || endC <= 0) continue;
      const startOriginal = indexMap[startC];
      const endOriginal = indexMap[endC - 1] + 1;
      if (endOriginal > startOriginal) {
        spans.push([startOriginal, endOriginal]);
        found = true;
        break;
      }
    }
    if (!found) missing.push(fragment);
  }

  spans.sort((a, b) => a[0] - b[0] || a[1] - b[1]);
  const merged = [];
  for (const [start, end] of spans) {
    if (!merged.length || start > merged[merged.length - 1][1]) {
      merged.push([start, end]);
    } else {
      const last = merged[merged.length - 1];
      merged[merged.length - 1] = [last[0], Math.max(last[1], end)];
    }
  }
  return { spans: merged, missing };
}

/**
 * @param {string} text
 * @param {unknown[]} highlightedErrors
 */
export default function ErrorHighlightedText({ text, highlightedErrors }) {
  const original = text || "";
  const fragments = collectFragments(highlightedErrors || []);

  if (!original) {
    return <p className="metric-card__help">Kein Originaltext verfügbar.</p>;
  }

  if (!fragments.length) {
    return <div className="text-panel">{original}</div>;
  }

  const { spans, missing } = findSpans(original, fragments);
  if (!spans.length) {
    return (
      <>
        <div className="text-panel">{original}</div>
        {missing.length ? (
          <div className="missing-markers">
            <p className="missing-markers__title">Nicht gefundene Markierungen</p>
            <ul className="missing-markers__list">
              {missing.map((item, index) => (
                <li key={`missing-only-${index}`}>{item}</li>
              ))}
            </ul>
          </div>
        ) : null}
      </>
    );
  }

  const parts = [];
  let cursor = 0;
  for (const [start, end] of spans) {
    parts.push(
      <span key={`t-${cursor}-${start}`}>{original.slice(cursor, start)}</span>,
    );
    parts.push(
      <mark key={`h-${start}-${end}`} className="error-highlight">
        {original.slice(start, end)}
      </mark>,
    );
    cursor = end;
  }
  parts.push(<span key={`t-end-${cursor}`}>{original.slice(cursor)}</span>);

  return (
    <>
      <div className="text-panel">{parts}</div>
      {missing.length ? (
        <div className="missing-markers">
          <p className="missing-markers__title">Nicht gefundene Markierungen</p>
          <ul className="missing-markers__list">
            {missing.map((item, index) => (
              <li key={`missing-${index}`}>{item}</li>
            ))}
          </ul>
        </div>
      ) : null}
    </>
  );
}
