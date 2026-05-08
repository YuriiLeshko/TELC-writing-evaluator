import { Link } from "react-router-dom";
import { CircleHelp } from "lucide-react";

/**
 * Subtle help control: navigates to the assessment guide with a section hash.
 * Stops propagation so parent buttons (e.g. rail tiles) do not receive the click.
 */
export default function InfoLink({ sectionId, title, ariaLabel }) {
  const to = `/assessment-guide#${sectionId}`;
  const defaultLabel = title || "Erläuterung im Bewertungsratgeber öffnen";

  return (
    <Link
      to={to}
      className="info-link"
      aria-label={ariaLabel || defaultLabel}
      title={title || defaultLabel}
      onClick={(e) => {
        e.stopPropagation();
      }}
      onKeyDown={(e) => {
        e.stopPropagation();
      }}
    >
      <CircleHelp size={15} strokeWidth={2} aria-hidden className="info-link__icon" />
    </Link>
  );
}
