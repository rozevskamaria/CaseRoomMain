from __future__ import annotations

import uuid

import pytest

from app.models.cohort import CohortAuditAction
from app.models.user import UserRole, UserStatus
from app.repositories.assignment_repo import AssignmentRepository
from app.repositories.case_repo import CaseRepository
from app.repositories.cohort_repo import AddMemberError, CohortRepository
from app.repositories.user_repo import UserRepository
from app.services.cohort import CohortService

pytestmark = pytest.mark.dbintegration


async def _student(users: UserRepository, login: str):
    user = await users.create_student(login, login)
    await users.set_status(user.id, UserStatus.active)
    return user


async def _staff(users: UserRepository, login: str, role=UserRole.staff):
    user = await users.create_staff(login, f"{login}@rsu.edu.lv", login, role)
    await users.set_status(user.id, UserStatus.active)
    return user


def _service(db_session) -> CohortService:
    return CohortService(
        CohortRepository(db_session),
        AssignmentRepository(db_session),
        CaseRepository(db_session),
    )


async def test_add_member_invalid_format(db_session):
    users = UserRepository(db_session)
    staff = await _staff(users, "aaaaaa")
    svc = _service(db_session)
    cohort = await svc.create_cohort(
        name="C", academic_year=None, created_by=str(staff.id)
    )
    with pytest.raises(AddMemberError) as exc:
        await svc.add_member(
            cohort_id=str(cohort.id), login_name="12345", actor_id=str(staff.id)
        )
    assert exc.value.status == "invalid_format"


async def test_add_member_not_found(db_session):
    users = UserRepository(db_session)
    staff = await _staff(users, "aaaaaa")
    svc = _service(db_session)
    cohort = await svc.create_cohort(
        name="C", academic_year=None, created_by=str(staff.id)
    )
    with pytest.raises(AddMemberError) as exc:
        await svc.add_member(
            cohort_id=str(cohort.id), login_name="999999", actor_id=str(staff.id)
        )
    assert exc.value.status == "not_found"


async def test_add_member_not_a_student(db_session):
    users = UserRepository(db_session)
    staff = await _staff(users, "aaaaaa")
    other_staff = await _staff(users, "777777")
    del other_staff
    svc = _service(db_session)
    cohort = await svc.create_cohort(
        name="C", academic_year=None, created_by=str(staff.id)
    )
    with pytest.raises(AddMemberError) as exc:
        await svc.add_member(
            cohort_id=str(cohort.id), login_name="777777", actor_id=str(staff.id)
        )
    assert exc.value.status == "not_a_student"


async def test_add_member_already_enrolled(db_session):
    users = UserRepository(db_session)
    staff = await _staff(users, "aaaaaa")
    await _student(users, "100100")
    svc = _service(db_session)
    cohort = await svc.create_cohort(
        name="C", academic_year=None, created_by=str(staff.id)
    )
    await svc.add_member(
        cohort_id=str(cohort.id), login_name="100100", actor_id=str(staff.id)
    )
    with pytest.raises(AddMemberError) as exc:
        await svc.add_member(
            cohort_id=str(cohort.id), login_name="100100", actor_id=str(staff.id)
        )
    assert exc.value.status == "already_enrolled"


async def test_add_member_success_and_audit(db_session):
    users = UserRepository(db_session)
    staff = await _staff(users, "aaaaaa")
    await _student(users, "100100")
    svc = _service(db_session)
    cohort = await svc.create_cohort(
        name="C", academic_year=None, created_by=str(staff.id)
    )
    outcome = await svc.add_member(
        cohort_id=str(cohort.id), login_name="100100", actor_id=str(staff.id)
    )
    assert outcome.student is not None

    entries = await svc.audit_for_cohort(str(cohort.id))
    actions = [e.action for e in entries]
    assert CohortAuditAction.staff_assigned in actions
    assert CohortAuditAction.enrolled in actions


async def test_remove_then_reactivate_audited(db_session):
    users = UserRepository(db_session)
    staff = await _staff(users, "aaaaaa")
    student = await _student(users, "100100")
    svc = _service(db_session)
    cohort = await svc.create_cohort(
        name="C", academic_year=None, created_by=str(staff.id)
    )
    await svc.add_member(
        cohort_id=str(cohort.id), login_name="100100", actor_id=str(staff.id)
    )
    await svc.remove_member(
        cohort_id=str(cohort.id),
        student_id=str(student.id),
        actor_id=str(staff.id),
    )
    assert await svc.member_active(str(cohort.id), str(student.id)) is False

    outcome = await svc.add_member(
        cohort_id=str(cohort.id), login_name="100100", actor_id=str(staff.id)
    )
    assert outcome.student is not None
    assert await svc.member_active(str(cohort.id), str(student.id)) is True

    entries = await svc.audit_for_cohort(str(cohort.id))
    actions = [e.action for e in entries]
    assert CohortAuditAction.removed in actions
    assert CohortAuditAction.reactivated in actions


async def test_lookup_student_states(db_session):
    users = UserRepository(db_session)
    staff = await _staff(users, "aaaaaa")
    await _student(users, "100100")
    await _staff(users, "777777")
    svc = _service(db_session)
    cohort = await svc.create_cohort(
        name="C", academic_year=None, created_by=str(staff.id)
    )

    assert (
        await svc.lookup_student(cohort_id=str(cohort.id), login_name="12345")
    ).status == "not_found"
    assert (
        await svc.lookup_student(cohort_id=str(cohort.id), login_name="999999")
    ).status == "not_found"
    assert (
        await svc.lookup_student(cohort_id=str(cohort.id), login_name="777777")
    ).status == "not_a_student"
    assert (
        await svc.lookup_student(cohort_id=str(cohort.id), login_name="100100")
    ).status == "enrollable"

    await svc.add_member(
        cohort_id=str(cohort.id), login_name="100100", actor_id=str(staff.id)
    )
    assert (
        await svc.lookup_student(cohort_id=str(cohort.id), login_name="100100")
    ).status == "already_enrolled"


async def test_staff_teaches_cohort_authz(db_session):
    users = UserRepository(db_session)
    staff_a = await _staff(users, "aaaaaa")
    staff_b = await _staff(users, "bbbbbb")
    svc = _service(db_session)
    cohort_b = await svc.create_cohort(
        name="B", academic_year=None, created_by=str(staff_b.id)
    )
    assert await svc.staff_teaches_cohort(str(staff_b.id), str(cohort_b.id)) is True
    assert (
        await svc.staff_teaches_cohort(str(staff_a.id), str(cohort_b.id)) is False
    )


async def test_assign_staff_requires_staff_role(db_session):
    users = UserRepository(db_session)
    admin = await _staff(users, "admin1", role=UserRole.admin)
    student = await _student(users, "100100")
    svc = _service(db_session)
    cohort = await svc.create_cohort(
        name="C", academic_year=None, created_by=str(admin.id)
    )
    from app.repositories.cohort_repo import CohortAccessError

    with pytest.raises(CohortAccessError):
        await svc.assign_staff(
            cohort_id=str(cohort.id),
            staff_id=str(student.id),
            actor_id=str(admin.id),
        )


async def test_unknown_cohort_add_member(db_session):
    users = UserRepository(db_session)
    staff = await _staff(users, "aaaaaa")
    await _student(users, "100100")
    svc = _service(db_session)
    with pytest.raises(AddMemberError) as exc:
        await svc.add_member(
            cohort_id=str(uuid.uuid4()),
            login_name="100100",
            actor_id=str(staff.id),
        )
    assert exc.value.status == "not_found"
