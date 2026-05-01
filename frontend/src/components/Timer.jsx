import { useEffect, useState } from "react";
import { formatElapsed, getElapsedSeconds } from "../utils/date.js";

const TARGET_MINUTES = 30;
const TARGET_SECONDS = TARGET_MINUTES * 60;

export default function Timer({ startedAt }) {
  const [, tick] = useState(0);
  useEffect(() => {
    const id = setInterval(() => tick((n) => n + 1), 1000);
    return () => clearInterval(id);
  }, [startedAt]);

  const elapsed = getElapsedSeconds(startedAt);
  const over = elapsed > TARGET_SECONDS;
  const elapsedFmt = formatElapsed(elapsed);
  const targetFmt = `${TARGET_MINUTES}:00`;

  return (
    <span className={`timer ${over ? "timer--warn" : ""}`.trim()}>
      Zeit: {elapsedFmt} / {targetFmt}
      {over ? " (über 30 Min.)" : ""}
    </span>
  );
}
