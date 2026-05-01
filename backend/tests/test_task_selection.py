from __future__ import annotations

from backend.models import TaskSession
from backend.services.task_selection import (
    pick_random_unseen_complaint_task,
    pick_random_unseen_info_task,
)


def test_pick_random_excludes_tasks_from_prior_sessions(db_session, seeded_users, seeded_tasks) -> None:
    user = seeded_users["user"]
    info = seeded_tasks["info_task"]
    complaint = seeded_tasks["complaint_task"]

    db_session.add(
        TaskSession(
            user_id=user.id,
            info_task_id=info.id,
            complaint_task_id=complaint.id,
            status="started",
        )
    )
    db_session.commit()

    assert pick_random_unseen_info_task(db_session, user.id) is None
    assert pick_random_unseen_complaint_task(db_session, user.id) is None


def test_pick_random_returns_task_when_unused(db_session, seeded_users, seeded_tasks) -> None:
    user = seeded_users["user"]
    picked_info = pick_random_unseen_info_task(db_session, user.id)
    picked_complaint = pick_random_unseen_complaint_task(db_session, user.id)
    assert picked_info is not None and picked_info.id == seeded_tasks["info_task"].id
    assert picked_complaint is not None and picked_complaint.id == seeded_tasks["complaint_task"].id


def test_second_info_task_available_after_first_used(db_session, seeded_users) -> None:
    from backend.models import ComplaintTask, InfoTask

    user = seeded_users["user"]
    i1 = InfoTask(
        task_number=1,
        source_text="s1",
        situation_text="si1",
        instruction_text="i1",
        expected_key_points_json=["a"],
        is_active=True,
    )
    i2 = InfoTask(
        task_number=2,
        source_text="s2",
        situation_text="si2",
        instruction_text="i2",
        expected_key_points_json=["b"],
        is_active=True,
    )
    c1 = ComplaintTask(
        task_number=1,
        source_text="c1",
        situation_text="cs1",
        instruction_text="ci1",
        expected_key_points_json=["x"],
        is_active=True,
    )
    c2 = ComplaintTask(
        task_number=2,
        source_text="c2",
        situation_text="cs2",
        instruction_text="ci2",
        expected_key_points_json=["y"],
        is_active=True,
    )
    db_session.add_all([i1, i2, c1, c2])
    db_session.commit()

    db_session.add(
        TaskSession(user_id=user.id, info_task_id=i1.id, complaint_task_id=c1.id, status="started")
    )
    db_session.commit()

    info_pick = pick_random_unseen_info_task(db_session, user.id)
    complaint_pick = pick_random_unseen_complaint_task(db_session, user.id)
    assert info_pick is not None and info_pick.id == i2.id
    assert complaint_pick is not None and complaint_pick.id == c2.id
