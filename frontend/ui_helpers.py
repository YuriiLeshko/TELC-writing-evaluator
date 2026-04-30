from __future__ import annotations

import html
import re
from datetime import datetime, timezone
from typing import Any

import streamlit as st


def render_metric_card(label: str, value: Any, help_text: str | None = None) -> None:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">{html.escape(str(label))}</div>
            <div class="metric-value">{html.escape(str(value))}</div>
            <div class="metric-help">{html.escape(help_text) if help_text else ""}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_criterion_card(title: str, criterion: dict[str, Any] | None) -> None:
    criterion = criterion or {}
    grade = criterion.get("grade", "-")
    points = criterion.get("points", "-")
    comment = criterion.get("comment") or criterion.get("short_comment") or "Keine Details."
    st.markdown(
        f"""
        <div class="criterion-card">
            <div class="criterion-title">{html.escape(title)}</div>
            <div><b>Grade:</b> {html.escape(str(grade))}</div>
            <div><b>Points:</b> {html.escape(str(points))}</div>
            <div class="muted">{html.escape(str(comment))}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_word_count_badge(word_count: int) -> None:
    if word_count < 150:
        st.warning(f"Woerter: {word_count} / 150")
    else:
        st.success(f"Woerter: {word_count} / 150")


def count_words(text: str) -> int:
    return len(re.findall(r"\b\w+\b", text or "", flags=re.UNICODE))


def _to_datetime(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        dt = value
    elif isinstance(value, str):
        normalized = value.replace("Z", "+00:00")
        try:
            dt = datetime.fromisoformat(normalized)
        except ValueError:
            return None
    else:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def format_datetime(value: Any) -> str:
    dt = _to_datetime(value)
    if not dt:
        return "-"
    return dt.astimezone().strftime("%Y-%m-%d %H:%M:%S")


def format_elapsed_time(started_at: Any) -> tuple[str, int]:
    dt = _to_datetime(started_at)
    if not dt:
        return "Zeit: --:-- / 30:00", 0
    now = datetime.now(timezone.utc)
    elapsed = max(int((now - dt).total_seconds()), 0)
    minutes, seconds = divmod(elapsed, 60)
    return f"Zeit: {minutes:02d}:{seconds:02d} / 30:00", elapsed


def safe_get(data: Any, path: str, default: Any = None) -> Any:
    if data is None:
        return default
    cur = data
    for part in path.split("."):
        if isinstance(cur, dict):
            cur = cur.get(part, default)
        else:
            return default
    return cur


def parse_key_points_multiline(text: str) -> list[str]:
    return [line.strip() for line in (text or "").splitlines() if line.strip()]


def key_points_to_multiline(points: list[str] | None) -> str:
    return "\n".join(points or [])


def _canonicalize_with_map(text: str) -> tuple[str, list[int]]:
    translation = str.maketrans(
        {
            "\u2018": "'",
            "\u2019": "'",
            "\u201c": '"',
            "\u201d": '"',
            "\u2013": "-",
            "\u2014": "-",
            "\u00a0": " ",
        }
    )
    canonical_chars: list[str] = []
    index_map: list[int] = []
    prev_space = False
    for idx, char in enumerate(text):
        mapped = char.translate(translation)
        for piece in mapped:
            if piece.isspace():
                if prev_space:
                    continue
                canonical_chars.append(" ")
                index_map.append(idx)
                prev_space = True
            else:
                canonical_chars.append(piece)
                index_map.append(idx)
                prev_space = False
    return "".join(canonical_chars), index_map


def _canonicalize(text: str) -> str:
    canonical, _ = _canonicalize_with_map(text)
    return canonical.strip()


def render_error_highlighted_text(original_text: str, highlighted_errors: list[str] | None) -> None:
    text = original_text or ""
    fragments = [str(item).strip() for item in (highlighted_errors or []) if str(item).strip()]
    if not text:
        st.info("Kein Originaltext verfuegbar.")
        return
    if not fragments:
        st.markdown(f"<div class='text-panel'>{html.escape(text)}</div>", unsafe_allow_html=True)
        return

    canonical_text, index_map = _canonicalize_with_map(text)
    lowered_canonical_text = canonical_text.lower()
    spans: list[tuple[int, int]] = []
    missing: list[str] = []
    seen: set[str] = set()

    for fragment in fragments:
        if fragment in seen:
            continue
        seen.add(fragment)
        canonical_fragment = _canonicalize(fragment)
        if not canonical_fragment:
            continue
        escaped_for_regex = re.escape(canonical_fragment.lower())
        pattern = escaped_for_regex.replace(r"\ ", r"\s+")
        found = False
        for match in re.finditer(pattern, lowered_canonical_text):
            start_canonical = match.start()
            end_canonical = match.end()
            if start_canonical >= len(index_map) or end_canonical <= 0:
                continue
            start_original = index_map[start_canonical]
            end_original = index_map[end_canonical - 1] + 1
            if end_original > start_original:
                spans.append((start_original, end_original))
                found = True
        if not found:
            missing.append(fragment)

    if spans:
        spans.sort(key=lambda item: (item[0], item[1]))
        merged: list[tuple[int, int]] = []
        for start, end in spans:
            if not merged or start > merged[-1][1]:
                merged.append((start, end))
            else:
                merged[-1] = (merged[-1][0], max(merged[-1][1], end))

        rendered_parts: list[str] = []
        cursor = 0
        for start, end in merged:
            rendered_parts.append(html.escape(text[cursor:start]))
            rendered_parts.append(f"<span class='error-highlight'>{html.escape(text[start:end])}</span>")
            cursor = end
        rendered_parts.append(html.escape(text[cursor:]))
        rendered_html = "".join(rendered_parts)
    else:
        rendered_html = html.escape(text)

    st.markdown(f"<div class='text-panel'>{rendered_html}</div>", unsafe_allow_html=True)
    if missing:
        st.info("Nicht im Text exakt gefunden: " + ", ".join(missing))
