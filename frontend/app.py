from __future__ import annotations

from typing import Any

import streamlit as st

from api_client import (
    ApiError,
    admin_activate_user,
    admin_create_complaint_task,
    admin_create_info_task,
    admin_deactivate_user,
    admin_delete_complaint_task,
    admin_delete_info_task,
    admin_get_complaint_tasks,
    admin_get_info_tasks,
    admin_get_users,
    admin_update_complaint_task,
    admin_update_info_task,
    admin_update_user_counters,
    delete_submission,
    delete_task_session,
    get_active_sessions,
    get_current_user,
    get_my_submissions,
    health_check,
    start_task_session,
    submit_evaluation,
)
from ui_helpers import (
    count_words,
    format_datetime,
    format_elapsed_time,
    key_points_to_multiline,
    parse_key_points_multiline,
    render_criterion_card,
    render_error_highlighted_text,
    render_metric_card,
    render_word_count_badge,
    safe_get,
)

st.set_page_config(page_title="TELC B2 Writing Evaluator", page_icon="📝", layout="wide")

st.markdown(
    """
    <style>
    .block-container { max-width: 1200px; padding-top: 1.2rem; }
    .card { border: 1px solid #e5e7eb; border-radius: 14px; padding: 16px; margin-bottom: 12px; background: #fff; }
    .card-selected { border: 2px solid #1d4ed8; box-shadow: 0 0 0 1px #93c5fd; }
    .metric-card { border: 1px solid #e5e7eb; border-radius: 12px; padding: 10px 12px; background: #fafafa; margin-bottom: 8px; }
    .metric-label { font-size: 0.9rem; color: #666; }
    .metric-value { font-size: 1.2rem; font-weight: 700; }
    .metric-help { font-size: 0.8rem; color: #777; }
    .criterion-card { border: 1px solid #ddd; border-radius: 10px; padding: 12px; background: #fcfcff; margin-bottom: 10px; }
    .criterion-title { font-weight: 700; margin-bottom: 6px; }
    .muted { color: #666; font-size: 0.9rem; }
    .task-scroll { display: flex; overflow-x: auto; gap: 10px; padding-bottom: 6px; scroll-snap-type: x mandatory; }
    .task-panel { min-width: 320px; width: calc(50% - 8px); scroll-snap-align: start; }
    @media (max-width: 860px) { .task-panel { min-width: 88%; width: 88%; } }
    .error-highlight { background-color: #ffd6d6; border-bottom: 2px solid #d00000; padding: 1px 3px; border-radius: 4px; }
    .text-panel { border: 1px solid #eee; border-radius: 10px; padding: 10px; white-space: pre-wrap; line-height: 1.45; background: #fff; }
    .dot-nav { color: #888; font-size: 0.9rem; margin-top: 2px; }
    .top-nav { border: 1px solid #e5e7eb; border-radius: 12px; padding: 10px; margin-bottom: 14px; background: #fff; position: sticky; top: 0.5rem; z-index: 50; }
    .left-active-panel { border: 2px solid #1d4ed8; border-radius: 12px; padding: 12px; background: #f8fbff; margin-bottom: 10px; }
    </style>
    """,
    unsafe_allow_html=True,
)


def init_state() -> None:
    defaults = {
        "current_page": "🏠 Main",
        "current_session": None,
        "selected_task_type": None,
        "selection_confirmed": False,
        "session_started_at": None,
        "candidate_text": "",
        "last_result": None,
        "last_submission": None,
        "role_mode": "User",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def get_task_by_type(session: dict[str, Any], task_type: str) -> dict[str, Any] | None:
    return session.get("info_task") if task_type == "info" else session.get("complaint_task")


def render_nav() -> None:
    st.markdown("<div class='top-nav'>", unsafe_allow_html=True)
    top_left, top_right = st.columns([4, 1])
    with top_left:
        st.markdown("**TELC Frontend MVP**")
        st.caption("Demo Auth aktiv: Rollenwahl nur fuer UI-Flow.")
    with top_right:
        st.session_state.role_mode = st.selectbox(
            "Rolle",
            ["User", "Admin"],
            index=0 if st.session_state.role_mode == "User" else 1,
            key="role_mode_select",
            label_visibility="collapsed",
        )

    pages = ["🏠 Main", "📝 Training", "📚 Archive", "👤 Profile"]
    if st.session_state.role_mode == "Admin":
        pages.append("⚙️ Admin")
    if st.session_state.current_page not in pages:
        st.session_state.current_page = "🏠 Main"

    nav_cols = st.columns(len(pages))
    for idx, page in enumerate(pages):
        with nav_cols[idx]:
            if st.button(page, key=f"top-nav-{page}", use_container_width=True):
                st.session_state.current_page = page
                st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)


def render_landing() -> None:
    st.title("TELC B2 Writing Evaluator")
    st.markdown(
        """
        Dieses Tool ist fuer das Training gedacht.  
        Die Bewertung ist AI-unterstuetzt und ersetzt keine offizielle TELC-Prueferbewertung.
        """
    )
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("📝 Training")
        st.write("Neue Sitzung starten, Aufgabe waehlen, Text schreiben, Feedback erhalten.")
        if st.button("TRAINING", use_container_width=True):
            st.session_state.current_page = "📝 Training"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
    with col2:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("📚 Archive")
        st.write("Vorherige Einreichungen und aktive Sitzungen einsehen oder loeschen.")
        if st.button("ARCHIVE", use_container_width=True):
            st.session_state.current_page = "📚 Archive"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)


def render_task_card(title: str, task: dict[str, Any], task_type: str) -> None:
    selected = st.session_state.selected_task_type == task_type
    css = "card card-selected task-panel" if selected else "card task-panel"
    st.markdown(f"<div class='{css}'>", unsafe_allow_html=True)
    st.markdown(f"#### {title}")
    st.caption(f"Typ: {task_type}")
    st.write("**Ausgangstext**")
    st.write(task.get("source_text") or "-")
    st.write("**Situation**")
    st.write(task.get("situation_text") or "-")
    st.write("**Aufgabe**")
    st.write(task.get("instruction_text") or "-")
    points = task.get("expected_key_points") or []
    if points:
        st.write("**Erwartete Schwerpunkte**")
        for item in points:
            st.write(f"- {item}")
    if not st.session_state.selection_confirmed:
        if st.button("Auswaehlen", key=f"pick-{task_type}", use_container_width=True):
            st.session_state.selected_task_type = task_type
            st.rerun()
        if selected and st.button("Auswahl bestaetigen", key=f"confirm-{task_type}", use_container_width=True):
            st.session_state.selection_confirmed = True
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)


def render_training() -> None:
    st.title("📝 Training")
    st.markdown("<div class='dot-nav'>Aufgabe A | Aufgabe B | Swipe auf Mobile moeglich</div>", unsafe_allow_html=True)

    if st.button("Start new training", type="primary"):
        try:
            started = start_task_session()
            session = started.get("session")
            st.session_state.current_session = session
            st.session_state.session_started_at = safe_get(session, "started_at")
            st.session_state.selected_task_type = None
            st.session_state.selection_confirmed = False
            st.session_state.candidate_text = ""
            st.session_state.last_result = None
            st.session_state.last_submission = None
            st.success("Neue Sitzung gestartet.")
        except ApiError as exc:
            st.error(f"Konnte Sitzung nicht starten: {exc}")

    session = st.session_state.current_session
    if not session:
        st.info("Noch keine aktive Sitzung in diesem Frontend-Tab.")
        return

    timer_label, elapsed_seconds = format_elapsed_time(st.session_state.session_started_at)
    if elapsed_seconds > 1800:
        st.warning(f"⚠️ {timer_label} (Zielzeit ueberschritten)")
    else:
        st.info(f"⏱️ {timer_label}")

    nav_col1, nav_col2 = st.columns(2)
    with nav_col1:
        if st.button("← Aufgabe A", use_container_width=True):
            st.session_state.selected_task_type = "info"
    with nav_col2:
        if st.button("Aufgabe B →", use_container_width=True):
            st.session_state.selected_task_type = "complaint"

    main_left, main_right = st.columns([1, 2])
    with main_left:
        st.markdown("#### Aktive Auswahl")
        if st.session_state.selected_task_type:
            active_task = get_task_by_type(session, st.session_state.selected_task_type) or {}
            st.markdown("<div class='left-active-panel'>", unsafe_allow_html=True)
            st.write(f"**Typ:** {st.session_state.selected_task_type}")
            st.write("**Ausgangstext**")
            st.write(active_task.get("source_text") or "-")
            st.write("**Situation**")
            st.write(active_task.get("situation_text") or "-")
            st.write("**Aufgabe**")
            st.write(active_task.get("instruction_text") or "-")
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.info("Noch keine Aufgabe ausgewaehlt.")

    with main_right:
        left, right = st.columns(2)
        with left:
            render_task_card("Aufgabe A (Info)", session.get("info_task", {}), "info")
        with right:
            render_task_card("Aufgabe B (Complaint)", session.get("complaint_task", {}), "complaint")

    if st.session_state.selection_confirmed:
        st.warning("Die Auswahl ist bestaetigt. Der Timer laeuft seit Beginn der Sitzung.")
    else:
        st.info("Bitte zuerst eine Aufgabe auswaehlen und unten bestaetigen.")

    disabled = not st.session_state.selection_confirmed
    st.session_state.candidate_text = st.text_area(
        "Deine Antwort",
        value=st.session_state.candidate_text,
        height=240,
        disabled=disabled,
        placeholder="Schreibe hier deinen Text ...",
    )
    word_count = count_words(st.session_state.candidate_text)
    render_word_count_badge(word_count)

    if st.button("Antwort abschicken", type="primary", disabled=disabled):
        selected = st.session_state.selected_task_type
        if not selected:
            st.error("Bitte zuerst eine Aufgabe waehlen.")
            return
        if not st.session_state.candidate_text.strip():
            st.error("Bitte Text eingeben.")
            return
        try:
            with st.spinner("Bewertung laeuft ..."):
                result_payload = submit_evaluation(
                    task_session_id=session["id"],
                    selected_task_type=selected,
                    candidate_text=st.session_state.candidate_text,
                )
            st.session_state.last_result = result_payload.get("result", {})
            st.session_state.last_submission = result_payload
            st.success("Bewertung erfolgreich.")
        except ApiError as exc:
            st.error(f"Bewertung fehlgeschlagen: {exc}")

    if st.session_state.last_result:
        render_result_view(
            result=st.session_state.last_result,
            selected_task_type=st.session_state.selected_task_type or "-",
            source_session=session,
            candidate_text=st.session_state.candidate_text,
        )


def render_result_view(
    result: dict[str, Any], selected_task_type: str, source_session: dict[str, Any], candidate_text: str
) -> None:
    st.divider()
    st.header("✅ Ergebnis")
    top1, top2, top3 = st.columns(3)
    with top1:
        render_metric_card("Final Score", f"{result.get('final_score', '-')}/{result.get('max_score', '-')}")
    with top2:
        render_metric_card("Raw Score", result.get("raw_score", "-"))
    with top3:
        render_metric_card("Word Count", safe_get(result, "word_count.value", result.get("word_count", "-")))

    c1, c2, c3 = st.columns(3)
    with c1:
        render_criterion_card("Criterion I / Task Achievement", result.get("criterion_I"))
    with c2:
        render_criterion_card("Criterion II / Communicative Design", result.get("criterion_II"))
    with c3:
        render_criterion_card("Criterion III / Formal Accuracy", result.get("criterion_III"))

    st.subheader("Text mit markierten Grammatikfehlern")
    errors = safe_get(result, "criterion_III.highlighted_errors", [])
    render_error_highlighted_text(candidate_text, errors)

    st.subheader("Technische Zusammenfassung")
    t1, t2, t3 = st.columns(3)
    with t1:
        st.write(f"- Woerter: {safe_get(result, 'word_count.value', '-')}")
        st.write(f"- Zeit (s): {result.get('time_seconds', source_session.get('duration_seconds', '-'))}")
    with t2:
        st.write(f"- Topic mismatch: {safe_get(result, 'task_check.topic_mismatch', False)}")
        st.write(f"- Situation mismatch: {safe_get(result, 'task_check.situation_mismatch', False)}")
    with t3:
        st.write(f"- Mindestwoerter erreicht: {safe_get(result, 'word_count.meets_minimum', '-')}")

    selected_task = get_task_by_type(source_session, selected_task_type)
    with st.expander("Aufgabentext", expanded=False):
        st.write(f"Ausgewaehlter Typ: {selected_task_type}")
        st.write("**Ausgangstext**")
        st.write((selected_task or {}).get("source_text", "-"))
        st.write("**Situation**")
        st.write((selected_task or {}).get("situation_text", "-"))
        st.write("**Anweisung**")
        st.write((selected_task or {}).get("instruction_text", "-"))

    with st.expander("Verbesserte Version", expanded=False):
        st.write(safe_get(result, "improved_text.improved_text", "Keine verbesserte Version vorhanden."))
        st.write("**Changes summary**")
        st.write(safe_get(result, "improved_text.changes_summary", "-"))

    with st.expander("Analyse-Details", expanded=False):
        st.write(f"Word count: {safe_get(result, 'word_count.value', '-')}")
        st.write(f"Time: {result.get('time_seconds', '-')}")
        st.write("Highlighted errors:")
        for item in errors or []:
            st.write(f"- {item}")
        st.write("Language level comment:")
        st.write(safe_get(result, "language_level_comment", "-"))
        st.write("Systematic errors:")
        for item in safe_get(result, "systematic_errors", []) or []:
            st.write(f"- {item}")
        st.write("Grammar control:")
        st.write(safe_get(result, "criterion_III.comment", "-"))
        with st.expander("Debug JSON"):
            st.json(result)


def render_archive() -> None:
    st.title("📚 Archive")
    try:
        submissions = get_my_submissions()
    except ApiError as exc:
        st.error(f"Submissions konnten nicht geladen werden: {exc}")
        submissions = []
    try:
        active_sessions = get_active_sessions()
    except ApiError as exc:
        st.error(f"Aktive Sessions konnten nicht geladen werden: {exc}")
        active_sessions = []

    st.subheader("Vorherige Submissions")
    if not submissions:
        st.info("Keine Submissions vorhanden.")
    for item in submissions:
        title = (
            f"#{item.get('id')} | {format_datetime(item.get('submitted_at'))} | "
            f"{item.get('selected_task_type')} | Score {item.get('final_score', '-')}"
        )
        with st.expander(title):
            st.write(f"Status: {item.get('status')}")
            st.write(f"Woerter: {item.get('word_count', '-')}")
            st.write("**Text**")
            st.write(item.get("candidate_text", "-"))
            st.write("**Result summary**")
            st.write(item.get("result", {}))
            improved = safe_get(item, "result.improved_text.improved_text")
            if improved:
                st.write("**Verbesserte Version**")
                st.write(improved)
            errors = safe_get(item, "result.criterion_III.highlighted_errors", [])
            if errors:
                st.write("**Highlight errors**")
                for err in errors:
                    st.write(f"- {err}")
            if st.button("Submission loeschen", key=f"delete-sub-{item['id']}"):
                try:
                    delete_submission(item["id"])
                    st.success("Submission geloescht.")
                    st.rerun()
                except ApiError as exc:
                    st.error(f"Loeschen fehlgeschlagen: {exc}")

    st.subheader("Aktive (unfertige) Sessions")
    if not active_sessions:
        st.info("Keine aktiven Sessions.")
    for session in active_sessions:
        with st.expander(f"Session #{session.get('id')} | {format_datetime(session.get('started_at'))}"):
            st.write(f"Status: {session.get('status')}")
            st.write(f"Selected task: {session.get('selected_task_type')}")
            if st.button("Session loeschen", key=f"delete-sess-{session['id']}"):
                try:
                    delete_task_session(session["id"])
                    st.success("Session geloescht.")
                    st.rerun()
                except ApiError as exc:
                    st.error(f"Loeschen fehlgeschlagen: {exc}")


def render_profile() -> None:
    st.title("👤 Profile")
    try:
        user = get_current_user()
    except ApiError as exc:
        st.error(f"Profil konnte nicht geladen werden: {exc}")
        return
    col1, col2, col3 = st.columns(3)
    with col1:
        render_metric_card("Email", user.get("email", "-"))
        render_metric_card("Role", user.get("role", "-"))
        render_metric_card("Active", user.get("is_active", "-"))
    with col2:
        render_metric_card("Available sessions", user.get("available_sessions", "-"))
        render_metric_card("Available submissions", user.get("available_submissions", "-"))
    with col3:
        render_metric_card("Next info task index", user.get("next_info_task_index", "-"))
        render_metric_card("Next complaint task index", user.get("next_complaint_task_index", "-"))


def render_task_admin(
    title: str,
    get_items,
    create_item,
    update_item,
    delete_item,
    key_prefix: str,
) -> None:
    st.subheader(title)
    try:
        tasks = get_items()
    except ApiError as exc:
        st.error(f"{title} nicht verfuegbar: {exc}")
        return

    with st.form(f"{key_prefix}-create"):
        st.markdown("**Neuen Task erstellen**")
        task_number = st.number_input("task_number", min_value=1, step=1, key=f"{key_prefix}-num-new")
        source_text = st.text_area("source_text", key=f"{key_prefix}-source-new")
        situation_text = st.text_area("situation_text", key=f"{key_prefix}-situation-new")
        instruction_text = st.text_area("instruction_text", key=f"{key_prefix}-instruction-new")
        expected_key_points_text = st.text_area(
            "expected_key_points (eine Zeile pro Punkt)", key=f"{key_prefix}-points-new"
        )
        is_active = st.checkbox("is_active", value=True, key=f"{key_prefix}-active-new")
        if st.form_submit_button("Erstellen"):
            try:
                create_item(
                    task_number=int(task_number),
                    source_text=source_text,
                    situation_text=situation_text,
                    instruction_text=instruction_text,
                    expected_key_points=parse_key_points_multiline(expected_key_points_text),
                    is_active=is_active,
                )
                st.success("Task erstellt.")
                st.rerun()
            except ApiError as exc:
                st.error(f"Erstellen fehlgeschlagen: {exc}")

    for task in tasks:
        with st.expander(f"Task #{task.get('id')} | Nummer {task.get('task_number')}"):
            with st.form(f"{key_prefix}-edit-{task['id']}"):
                task_number = st.number_input(
                    "task_number",
                    min_value=1,
                    step=1,
                    value=int(task.get("task_number") or 1),
                    key=f"{key_prefix}-num-{task['id']}",
                )
                source_text = st.text_area("source_text", value=task.get("source_text", ""), key=f"{key_prefix}-source-{task['id']}")
                situation_text = st.text_area(
                    "situation_text",
                    value=task.get("situation_text", ""),
                    key=f"{key_prefix}-situation-{task['id']}",
                )
                instruction_text = st.text_area(
                    "instruction_text",
                    value=task.get("instruction_text", ""),
                    key=f"{key_prefix}-instruction-{task['id']}",
                )
                points_multiline = key_points_to_multiline(task.get("expected_key_points"))
                expected_key_points_text = st.text_area(
                    "expected_key_points (eine Zeile pro Punkt)",
                    value=points_multiline,
                    key=f"{key_prefix}-points-{task['id']}",
                )
                is_active = st.checkbox(
                    "is_active",
                    value=bool(task.get("is_active", True)),
                    key=f"{key_prefix}-active-{task['id']}",
                )
                submitted = st.form_submit_button("Speichern")
                if submitted:
                    try:
                        update_item(
                            task["id"],
                            task_number=int(task_number),
                            source_text=source_text,
                            situation_text=situation_text,
                            instruction_text=instruction_text,
                            expected_key_points=parse_key_points_multiline(expected_key_points_text),
                            is_active=is_active,
                        )
                        st.success("Task aktualisiert.")
                        st.rerun()
                    except ApiError as exc:
                        st.error(f"Update fehlgeschlagen: {exc}")
            if st.button("Task deaktivieren/loeschen", key=f"{key_prefix}-delete-{task['id']}"):
                try:
                    delete_item(task["id"])
                    st.success("Task deaktiviert.")
                    st.rerun()
                except ApiError as exc:
                    st.error(f"Loeschen fehlgeschlagen: {exc}")


def render_admin() -> None:
    st.title("⚙️ Admin")
    st.warning("MVP Demo Auth: nur fuer lokale Demo, keine echte JWT-Auth.")
    tabs = st.tabs(["Users", "Info Tasks", "Complaint Tasks"])

    with tabs[0]:
        try:
            users = admin_get_users()
        except ApiError as exc:
            st.error(f"Admin users nicht verfuegbar: {exc}")
            users = []
        if not users:
            st.info("Keine User gefunden.")
        for user in users:
            with st.expander(f"User #{user.get('id')} | {user.get('email')} | active={user.get('is_active')}"):
                st.write(user)
                c1, c2 = st.columns(2)
                with c1:
                    sessions = st.number_input(
                        "available_sessions",
                        min_value=0,
                        value=int(user.get("available_sessions", 0)),
                        key=f"user-sess-{user['id']}",
                    )
                with c2:
                    submissions = st.number_input(
                        "available_submissions",
                        min_value=0,
                        value=int(user.get("available_submissions", 0)),
                        key=f"user-sub-{user['id']}",
                    )
                if st.button("Counter speichern", key=f"user-save-{user['id']}"):
                    try:
                        admin_update_user_counters(user["id"], int(sessions), int(submissions))
                        st.success("Counter aktualisiert.")
                        st.rerun()
                    except ApiError as exc:
                        st.error(f"Update fehlgeschlagen: {exc}")
                a1, a2 = st.columns(2)
                with a1:
                    if st.button("Aktivieren", key=f"user-act-{user['id']}"):
                        try:
                            admin_activate_user(user["id"])
                            st.success("User aktiviert.")
                            st.rerun()
                        except ApiError as exc:
                            st.error(str(exc))
                with a2:
                    if st.button("Deaktivieren", key=f"user-deact-{user['id']}"):
                        try:
                            admin_deactivate_user(user["id"])
                            st.success("User deaktiviert.")
                            st.rerun()
                        except ApiError as exc:
                            st.error(str(exc))

    with tabs[1]:
        render_task_admin(
            title="Info Tasks",
            get_items=admin_get_info_tasks,
            create_item=admin_create_info_task,
            update_item=admin_update_info_task,
            delete_item=admin_delete_info_task,
            key_prefix="info-task",
        )

    with tabs[2]:
        render_task_admin(
            title="Complaint Tasks",
            get_items=admin_get_complaint_tasks,
            create_item=admin_create_complaint_task,
            update_item=admin_update_complaint_task,
            delete_item=admin_delete_complaint_task,
            key_prefix="complaint-task",
        )


def render_header_status() -> None:
    col1, col2 = st.columns([2, 1])
    with col1:
        st.caption("Frontend kommuniziert ausschliesslich per HTTP API.")
    with col2:
        try:
            health = health_check()
            st.success(f"Backend: {health.get('status', 'ok')}")
        except ApiError:
            st.error("Backend nicht erreichbar")


def main() -> None:
    init_state()
    render_nav()
    render_header_status()
    page = st.session_state.current_page
    if page == "🏠 Main":
        render_landing()
    elif page == "📝 Training":
        render_training()
    elif page == "📚 Archive":
        render_archive()
    elif page == "👤 Profile":
        render_profile()
    elif page == "⚙️ Admin":
        render_admin()
    else:
        st.info("Seite nicht gefunden.")


if __name__ == "__main__":
    main()
