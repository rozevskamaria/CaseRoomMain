from __future__ import annotations

import itertools
import types
import uuid

import pytest

import app.api.runtime as runtime
from app.api.graphql.auth_guards import AuthError
from app.api.graphql.schema import Mutation, Query
from app.models.case import (
    Case as CaseModel,
    CaseLocalizationEN,
    CaseVersion,
    CaseVersionStatus,
    Language,
)
from app.models.user import UserRole, UserStatus
from app.repositories.assignment_repo import AssignmentRepository
from app.repositories.attempt_repo import AttemptRepository
from app.repositories.case_authoring_repo import CaseAuthoringRepository
from app.repositories.case_repo import CaseRepository
from app.repositories.cohort_repo import CohortAccessError, CohortRepository
from app.repositories.user_repo import UserRepository
from app.services.case_authoring_service import (
    CaseAuthoringError,
    CaseAuthoringService,
    LabTestSpec,
    ScalarPatch,
)
from app.services.cohort import CohortService
from app.services.session import SessionService
from app.services.stores import DbAttemptStore, DbCaseSource

pytestmark = pytest.mark.dbintegration


FULL_CONTENT = {
    "title": "Recurrent infections",
    "patient": "5-year-old boy",
    "opening_clinical": "Vignette text.",
    "opening": "Opening line.",
    "red_flags": ["family history"],
    "parent_prompt": "You are the parent.",
    "lab_data": {"CBC": "WBC 12.0 (normal)", "IgG": "IgG 2.1 g/L (low)"},
    "exam_findings": "Pallor, no organomegaly.",
    "model_diagnosis": "XLA",
    "model_management": "IVIG.",
    "model_genetic_counselling": "X-linked.",
    "key_clues": ["absent B cells"],
    "wrong_paths": {"sepsis": "Reconsider — pattern is chronic."},
}


class FakeLLMClient:
    async def generate(self, system, messages, max_tokens):
        return "x"

    async def generate_structured(self, system, messages, schema, max_tokens):
        return {}

    async def stream(self, system, messages, max_tokens):
        yield "x"


def _ids():
    counter = itertools.count(1)
    return lambda: f"id-{next(counter)}"


def _info(user, db_session):
    context = types.SimpleNamespace(current_user=user, db_session=db_session)
    return types.SimpleNamespace(context=context)


def _authoring(db_session) -> CaseAuthoringService:
    return CaseAuthoringService(CaseAuthoringRepository(db_session))


async def _active_staff(db_session, login="staff01"):
    users = UserRepository(db_session)
    staff = await users.create_staff(login, f"{login}@rsu.edu.lv", "S", UserRole.staff)
    await users.set_status(staff.id, UserStatus.active)
    return staff


async def _active_admin(db_session, login="admin01"):
    users = UserRepository(db_session)
    admin = await users.create_staff(login, f"{login}@rsu.edu.lv", "A", UserRole.admin)
    await users.set_status(admin.id, UserStatus.active)
    return admin


async def _active_student(db_session, login="100100"):
    users = UserRepository(db_session)
    student = await users.create_student(login, "Stud")
    await users.set_status(student.id, UserStatus.active)
    return student


async def _seed_published(db_session, slug: str, content=None) -> CaseVersion:
    content = content or FULL_CONTENT
    case = CaseModel(slug=slug)
    db_session.add(case)
    await db_session.flush()
    version = CaseVersion(
        case_id=case.id,
        version_no=1,
        status=CaseVersionStatus.published,
        difficulty="medium",
        target_diagnosis="XLA",
        topic="Antibody deficiency",
        iuis="Predominantly antibody",
        created_by=None,
    )
    db_session.add(version)
    await db_session.flush()
    case.current_version_id = version.id
    db_session.add(
        CaseLocalizationEN(
            case_version_id=version.id,
            language=Language.en,
            content=dict(content),
        )
    )
    await db_session.flush()
    return version


async def _make_complete_draft(svc, created_by) -> str:
    view = await svc.create_case_draft(
        slug="newcase", from_version_id=None, created_by=created_by
    )
    vid = uuid.UUID(view.version_id)
    await svc.set_draft_scalars(
        vid,
        ScalarPatch(
            difficulty="medium",
            target_diagnosis="XLA",
            topic="Antibody",
            iuis="Antibody",
        ),
    )
    await svc.set_draft_localization(vid, "en", dict(FULL_CONTENT))
    return view.version_id


def _tests(db_session):
    cases = CaseRepository(db_session)
    session_service = SessionService(
        FakeLLMClient(),
        store=DbAttemptStore(AttemptRepository(db_session), cases),
        cases=DbCaseSource(cases),
        rng=lambda: 0.0,
        id_factory=_ids(),
    )
    cohort_service = CohortService(
        CohortRepository(db_session), AssignmentRepository(db_session), cases
    )
    return session_service, cohort_service


async def test_create_new_case_draft(db_session):
    staff = await _active_staff(db_session)
    svc = _authoring(db_session)
    view = await svc.create_case_draft(
        slug="brandnew", from_version_id=None, created_by=staff.id
    )
    assert view.status == "draft"
    assert view.version_no == 1
    assert view.slug == "brandnew"


async def test_create_draft_slug_taken(db_session):
    staff = await _active_staff(db_session)
    await _seed_published(db_session, "xla")
    svc = _authoring(db_session)
    with pytest.raises(CaseAuthoringError) as exc:
        await svc.create_case_draft(
            slug="xla", from_version_id=None, created_by=staff.id
        )
    assert exc.value.code == "slug_taken"


async def test_edit_published_forks_draft_and_immutability(db_session):
    staff = await _active_staff(db_session)
    published = await _seed_published(db_session, "xla")
    repo = CaseAuthoringRepository(db_session)
    original_content = dict(
        (await repo.get_localization(published.id, Language.en)).content
    )
    svc = _authoring(db_session)
    draft = await svc.create_case_draft(
        slug=None, from_version_id=published.id, created_by=staff.id
    )
    assert draft.status == "draft"
    assert draft.version_no == 2
    draft_vid = uuid.UUID(draft.version_id)
    new_content = dict(FULL_CONTENT)
    new_content["model_diagnosis"] = "Edited diagnosis"
    await svc.set_draft_localization(draft_vid, "en", new_content)

    published_after = await repo.get_version(published.id)
    assert published_after.status is CaseVersionStatus.published
    pub_content = (await repo.get_localization(published.id, Language.en)).content
    assert pub_content == original_content
    assert pub_content["model_diagnosis"] == "XLA"


async def test_attempt_on_old_version_renders_old_content(db_session):
    staff = await _active_staff(db_session)
    student = await _active_student(db_session)
    published = await _seed_published(db_session, "xla")
    session_service, _ = _tests(db_session)
    attempt = await session_service.start_case(
        "xla", "practice", student_id=str(student.id)
    )
    svc = _authoring(db_session)
    draft = await svc.create_case_draft(
        slug=None, from_version_id=published.id, created_by=staff.id
    )
    draft_vid = uuid.UUID(draft.version_id)
    await svc.set_draft_scalars(
        draft_vid,
        ScalarPatch(
            difficulty="hard",
            target_diagnosis="CVID",
            topic="t",
            iuis="i",
        ),
    )
    await svc.set_draft_localization(draft_vid, "en", dict(FULL_CONTENT))
    await svc.publish_version(draft_vid)

    case = await CaseRepository(db_session).get_published_case("xla")
    assert case.difficulty == "hard"
    attempt_repo = AttemptRepository(db_session)
    attempt_row = await attempt_repo.get_attempt(uuid.UUID(attempt.id))
    assert attempt_row.case_version_id == published.id
    pinned = await CaseAuthoringRepository(db_session).get_version(published.id)
    assert pinned.difficulty == "medium"


async def test_publish_rejected_when_content_key_missing(db_session):
    staff = await _active_staff(db_session)
    svc = _authoring(db_session)
    view = await svc.create_case_draft(
        slug="incomplete", from_version_id=None, created_by=staff.id
    )
    vid = uuid.UUID(view.version_id)
    await svc.set_draft_scalars(
        vid,
        ScalarPatch(
            difficulty="m", target_diagnosis="d", topic="t", iuis="i"
        ),
    )
    partial = dict(FULL_CONTENT)
    del partial["model_management"]
    await svc.set_draft_localization(vid, "en", partial)
    with pytest.raises(CaseAuthoringError) as exc:
        await svc.publish_version(vid)
    assert exc.value.code == "incomplete_localization"
    assert "en.model_management" in exc.value.fields


async def test_publish_rejected_on_empty_lab_value(db_session):
    staff = await _active_staff(db_session)
    svc = _authoring(db_session)
    view = await svc.create_case_draft(
        slug="emptylab", from_version_id=None, created_by=staff.id
    )
    vid = uuid.UUID(view.version_id)
    await svc.set_draft_scalars(
        vid, ScalarPatch(difficulty="m", target_diagnosis="d", topic="t", iuis="i")
    )
    bad = dict(FULL_CONTENT)
    bad["lab_data"] = {"CBC": "WBC 12", "IgG": ""}
    await svc.set_draft_localization(vid, "en", bad)
    with pytest.raises(CaseAuthoringError) as exc:
        await svc.publish_version(vid)
    assert exc.value.code == "incomplete_localization"
    assert any(f.startswith("en.lab_data.value") for f in exc.value.fields)


async def test_complete_draft_publishes_and_flips_current(db_session):
    staff = await _active_staff(db_session)
    svc = _authoring(db_session)
    vid_str = await _make_complete_draft(svc, staff.id)
    vid = uuid.UUID(vid_str)
    result = await svc.publish_version(vid)
    assert result.version.status == "published"
    repo = CaseAuthoringRepository(db_session)
    version = await repo.get_version(vid)
    assert version.status is CaseVersionStatus.published
    case = await repo.get_case(version.case_id)
    assert case.current_version_id == version.id
    case_view = await CaseRepository(db_session).get_published_case("newcase")
    assert case_view is not None
    assert set(case_view.lab_data.keys()) == {"CBC", "IgG"}


async def test_draft_only_case_not_served_to_students(db_session):
    staff = await _active_staff(db_session)
    student = await _active_student(db_session)
    svc = _authoring(db_session)
    await _make_complete_draft(svc, staff.id)
    case_view = await CaseRepository(db_session).get_published_case("newcase")
    assert case_view is None
    session_service, _ = _tests(db_session)
    with pytest.raises(KeyError):
        await session_service.start_case(
            "newcase", "practice", student_id=str(student.id)
        )


async def test_preview_returns_draft_for_staff(db_session):
    staff = await _active_staff(db_session)
    svc = _authoring(db_session)
    vid_str = await _make_complete_draft(svc, staff.id)
    case = await svc.preview(uuid.UUID(vid_str), "en")
    assert case is not None
    assert case.model_diagnosis == "XLA"
    assert list(case.lab_data.keys()) == ["CBC", "IgG"]


async def test_preview_matches_runtime_projection(db_session):
    staff = await _active_staff(db_session)
    svc = _authoring(db_session)
    vid_str = await _make_complete_draft(svc, staff.id)
    vid = uuid.UUID(vid_str)
    preview = await svc.preview(vid, "en")
    await svc.publish_version(vid)
    runtime_case = await CaseRepository(db_session).get_published_case("newcase")
    assert preview.lab_data == runtime_case.lab_data
    assert preview.model_dump() == runtime_case.model_dump()


async def test_create_assignment_rejects_draft_only_case(db_session):
    staff = await _active_staff(db_session)
    svc = _authoring(db_session)
    await _make_complete_draft(svc, staff.id)
    _, cohort_service = _tests(db_session)
    cohort = await cohort_service.create_cohort(
        name="C", academic_year=None, created_by=str(staff.id)
    )
    with pytest.raises(CohortAccessError):
        await cohort_service.create_assignment(
            cohort_id=str(cohort.id),
            case_id="newcase",
            mode="practice",
            language="en",
            title=None,
            opens_at=None,
            due_at=None,
            created_by=str(staff.id),
        )


async def test_discard_blocked_when_referenced_by_attempt(db_session):
    staff = await _active_staff(db_session)
    student = await _active_student(db_session)
    svc = _authoring(db_session)
    vid_str = await _make_complete_draft(svc, staff.id)
    vid = uuid.UUID(vid_str)
    await svc.publish_version(vid)
    session_service, _ = _tests(db_session)
    await session_service.start_case(
        "newcase", "practice", student_id=str(student.id)
    )
    fork = await svc.create_case_draft(
        slug=None, from_version_id=vid, created_by=staff.id
    )
    repo = CaseAuthoringRepository(db_session)
    published_version = await repo.get_version(vid)
    published_version.status = CaseVersionStatus.draft
    await db_session.flush()
    with pytest.raises(CaseAuthoringError) as exc:
        await svc.discard_draft(vid)
    assert exc.value.code == "cannot_discard_referenced"
    published_version.status = CaseVersionStatus.published
    await db_session.flush()
    assert fork.version_no == 2


async def test_discard_blocked_when_referenced_by_assignment(db_session):
    staff = await _active_staff(db_session)
    published = await _seed_published(db_session, "xla")
    svc = _authoring(db_session)
    _, cohort_service = _tests(db_session)
    cohort = await cohort_service.create_cohort(
        name="C", academic_year=None, created_by=str(staff.id)
    )
    assignment = await cohort_service.create_assignment(
        cohort_id=str(cohort.id),
        case_id="xla",
        mode="practice",
        language="en",
        title=None,
        opens_at=None,
        due_at=None,
        created_by=str(staff.id),
    )
    assert assignment.case_version_id == published.id
    repo = CaseAuthoringRepository(db_session)
    version = await repo.get_version(published.id)
    version.status = CaseVersionStatus.draft
    await db_session.flush()
    with pytest.raises(CaseAuthoringError) as exc:
        await svc.discard_draft(published.id)
    assert exc.value.code == "cannot_discard_referenced"


async def test_discard_unreferenced_draft(db_session):
    staff = await _active_staff(db_session)
    svc = _authoring(db_session)
    view = await svc.create_case_draft(
        slug="throwaway", from_version_id=None, created_by=staff.id
    )
    vid = uuid.UUID(view.version_id)
    result = await svc.discard_draft(vid)
    assert result.deleted_case is True
    repo = CaseAuthoringRepository(db_session)
    assert await repo.get_version(vid) is None
    assert await repo.get_case_by_slug("throwaway") is None


async def test_converge_two_drafts_from_same_version(db_session):
    staff = await _active_staff(db_session)
    published = await _seed_published(db_session, "xla")
    svc = _authoring(db_session)
    first = await svc.create_case_draft(
        slug=None, from_version_id=published.id, created_by=staff.id
    )
    second = await svc.create_case_draft(
        slug=None, from_version_id=published.id, created_by=staff.id
    )
    assert first.version_id == second.version_id
    repo = CaseAuthoringRepository(db_session)
    open_draft = await repo.get_open_draft(published.case_id)
    assert str(open_draft.id) == first.version_id


async def test_cross_locale_parity_block(db_session):
    staff = await _active_staff(db_session)
    svc = _authoring(db_session)
    vid_str = await _make_complete_draft(svc, staff.id)
    vid = uuid.UUID(vid_str)
    lv_content = dict(FULL_CONTENT)
    lv_content["lab_data"] = {"CBC": "lv text", "DHR": "different key"}
    await svc.set_draft_localization(vid, "lv", lv_content)
    with pytest.raises(CaseAuthoringError) as exc:
        await svc.publish_version(vid)
    assert exc.value.code == "incomplete_localization"
    assert "lv.lab_data.keys" in exc.value.fields


async def test_en_only_publishes(db_session):
    staff = await _active_staff(db_session)
    svc = _authoring(db_session)
    vid_str = await _make_complete_draft(svc, staff.id)
    result = await svc.publish_version(uuid.UUID(vid_str))
    assert result.version.status == "published"


async def test_lab_data_write_rederives_case_tests(db_session):
    staff = await _active_staff(db_session)
    svc = _authoring(db_session)
    view = await svc.create_case_draft(
        slug="labcase", from_version_id=None, created_by=staff.id
    )
    vid = uuid.UUID(view.version_id)
    specs = [
        LabTestSpec(key="CBC", kind="numeric_panel", result_by_language={"en": "a"}),
        LabTestSpec(key="Gene panel", kind="genetic", result_by_language={"en": "b"}),
    ]
    await svc.set_draft_lab_data(vid, "en", specs)
    repo = CaseAuthoringRepository(db_session)
    tests = await repo.get_tests(vid)
    assert [t.key for t in tests] == ["CBC", "Gene panel"]
    assert tests[1].kind.value == "genetic"


async def test_write_to_published_version_rejected(db_session):
    await _active_staff(db_session)
    published = await _seed_published(db_session, "xla")
    svc = _authoring(db_session)
    with pytest.raises(CaseAuthoringError) as exc:
        await svc.set_draft_localization(
            published.id, "en", dict(FULL_CONTENT)
        )
    assert exc.value.code == "version_published"


async def test_publish_authz_student_forbidden(db_session):
    staff = await _active_staff(db_session)
    student = await _active_student(db_session)
    svc = _authoring(db_session)
    vid_str = await _make_complete_draft(svc, staff.id)
    session_service, cohort_service = _tests(db_session)
    authoring_token = runtime.use_request_authoring_service(svc)
    try:
        mutation = Mutation()
        with pytest.raises(AuthError, match="Forbidden"):
            await mutation.publish_case_version(
                _info(student, db_session), version_id=vid_str
            )
    finally:
        runtime.reset_request_authoring_service(authoring_token)


async def test_publish_authz_unauth_forbidden(db_session):
    staff = await _active_staff(db_session)
    svc = _authoring(db_session)
    vid_str = await _make_complete_draft(svc, staff.id)
    authoring_token = runtime.use_request_authoring_service(svc)
    try:
        mutation = Mutation()
        with pytest.raises(AuthError, match="Authentication required"):
            await mutation.publish_case_version(
                _info(None, db_session), version_id=vid_str
            )
    finally:
        runtime.reset_request_authoring_service(authoring_token)


async def test_author_cases_lists_drafts_and_published(db_session):
    staff = await _active_staff(db_session)
    await _seed_published(db_session, "xla")
    svc = _authoring(db_session)
    await svc.create_case_draft(
        slug="draftone", from_version_id=None, created_by=staff.id
    )
    summaries = await svc.list_cases()
    slugs = {s.slug for s in summaries}
    assert "xla" in slugs
    assert "draftone" in slugs
    by_slug = {s.slug: s for s in summaries}
    assert by_slug["xla"].status == "published"
    assert by_slug["draftone"].status == "draft"


async def test_preview_resolver_requires_staff(db_session):
    student = await _active_student(db_session)
    staff = await _active_staff(db_session)
    svc = _authoring(db_session)
    vid_str = await _make_complete_draft(svc, staff.id)
    authoring_token = runtime.use_request_authoring_service(svc)
    try:
        query = Query()
        with pytest.raises(AuthError, match="Forbidden"):
            await query.preview_case(
                _info(student, db_session), version_id=vid_str, language="en"
            )
        case = await query.preview_case(
            _info(staff, db_session), version_id=vid_str, language="en"
        )
        assert case is not None
        assert case.model_diagnosis == "XLA"
    finally:
        runtime.reset_request_authoring_service(authoring_token)
