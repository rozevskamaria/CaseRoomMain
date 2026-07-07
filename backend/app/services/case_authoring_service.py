from __future__ import annotations

import re
import uuid
from dataclasses import dataclass, field

from app.models.case import (
    CaseTestKind,
    CaseVersion,
    CaseVersionStatus,
    Language,
)
from app.repositories.case_authoring_repo import (
    CaseAuthoringRepository,
    CaseSummaryRow,
    TestSpec,
)
from app.repositories.case_repo import project_case
from app.schemas.case import Case

RUNTIME_CONTENT_KEYS = (
    "title",
    "patient",
    "opening_clinical",
    "opening",
    "red_flags",
    "parent_prompt",
    "lab_data",
    "exam_findings",
    "model_diagnosis",
    "model_management",
    "model_genetic_counselling",
    "key_clues",
    "wrong_paths",
)

SCALAR_FIELDS = ("difficulty", "target_diagnosis", "topic", "iuis")

_SLUG_PATTERN = re.compile(r"^[a-z0-9-]+$")
_VALID_KINDS = {kind.value for kind in CaseTestKind}


class CaseAuthoringError(Exception):
    def __init__(self, code: str, fields: list[str] | None = None) -> None:
        super().__init__(code)
        self.code = code
        self.fields = fields or []


@dataclass
class LabTestSpec:
    key: str
    kind: str
    result_by_language: dict[str, str]


@dataclass
class CaseSummary:
    case_id: str
    slug: str
    version_id: str
    version_no: int
    status: str
    is_current: bool
    difficulty: str
    topic: str
    target_diagnosis: str
    iuis: str
    has_lv: bool
    created_at: object


@dataclass
class CaseLocalizationView:
    language: str
    content: dict


@dataclass
class CaseTestView:
    key: str
    kind: str
    ord: int


@dataclass
class CaseVersionView:
    case_id: str
    slug: str
    version_id: str
    version_no: int
    status: str
    is_current: bool
    difficulty: str
    topic: str
    target_diagnosis: str
    iuis: str
    localizations: list[CaseLocalizationView] = field(default_factory=list)
    tests: list[CaseTestView] = field(default_factory=list)


@dataclass
class PublishResult:
    version: CaseVersionView


@dataclass
class DiscardResult:
    case_id: str
    deleted_case: bool


@dataclass
class ScalarPatch:
    difficulty: str | None = None
    target_diagnosis: str | None = None
    topic: str | None = None
    iuis: str | None = None


def _non_empty_str(value: object) -> bool:
    return isinstance(value, str) and value.strip() != ""


def _validate_lab_data(content: dict, prefix: str, errors: list[str]) -> None:
    lab_data = content.get("lab_data")
    if not isinstance(lab_data, dict) or not lab_data:
        errors.append(f"{prefix}lab_data")
        return
    seen: set[str] = set()
    for key, value in lab_data.items():
        if not _non_empty_str(key):
            errors.append(f"{prefix}lab_data.key")
            continue
        if key in seen:
            errors.append(f"{prefix}lab_data.duplicate:{key}")
        seen.add(key)
        if not _non_empty_str(value):
            errors.append(f"{prefix}lab_data.value:{key}")


class CaseAuthoringService:
    def __init__(self, repo: CaseAuthoringRepository) -> None:
        self._repo = repo

    async def list_cases(self) -> list[CaseSummary]:
        rows = await self._repo.list_versions()
        summaries: list[CaseSummary] = []
        for row in rows:
            has_lv = await self._has_lv(row.version_id)
            summaries.append(_summary_from_row(row, has_lv))
        return summaries

    async def get_draft(self, version_id: uuid.UUID) -> CaseVersionView | None:
        version = await self._repo.get_version(version_id)
        if version is None:
            return None
        return await self._view(version)

    async def get_open_draft(self, case_id: uuid.UUID) -> CaseVersionView | None:
        version = await self._repo.get_open_draft(case_id)
        if version is None:
            return None
        return await self._view(version)

    async def create_case_draft(
        self,
        *,
        slug: str | None,
        from_version_id: uuid.UUID | None,
        created_by: uuid.UUID | None,
    ) -> CaseVersionView:
        if (slug is None) == (from_version_id is None):
            raise CaseAuthoringError("invalid_args")
        if slug is not None:
            return await self._create_new_case(slug, created_by)
        return await self._fork_from_version(from_version_id, created_by)

    async def _create_new_case(
        self, slug: str, created_by: uuid.UUID | None
    ) -> CaseVersionView:
        normalized = slug.strip()
        if not normalized or len(normalized) > 64 or not _SLUG_PATTERN.match(normalized):
            raise CaseAuthoringError("invalid_slug", ["slug"])
        existing = await self._repo.get_case_by_slug(normalized)
        if existing is not None:
            raise CaseAuthoringError("slug_taken", ["slug"])
        case = await self._repo.create_case(normalized)
        version = await self._repo.create_version(
            case_id=case.id,
            version_no=1,
            difficulty="",
            topic="",
            target_diagnosis="",
            iuis="",
            created_by=created_by,
        )
        return await self._view(version)

    async def _fork_from_version(
        self, from_version_id: uuid.UUID, created_by: uuid.UUID | None
    ) -> CaseVersionView:
        source = await self._repo.get_version(from_version_id)
        if source is None:
            raise CaseAuthoringError("version_not_found", ["fromVersionId"])
        existing_draft = await self._repo.get_open_draft(source.case_id)
        if existing_draft is not None:
            return await self._view(existing_draft)
        next_no = await self._repo.max_version_no(source.case_id) + 1
        try:
            draft = await self._repo.create_version(
                case_id=source.case_id,
                version_no=next_no,
                difficulty=source.difficulty,
                topic=source.topic,
                target_diagnosis=source.target_diagnosis,
                iuis=source.iuis,
                created_by=created_by,
            )
        except Exception:
            converged = await self._repo.get_open_draft(source.case_id)
            if converged is None:
                raise
            return await self._view(converged)
        await self._repo.clone_into_draft(
            src_version_id=source.id, dst_version_id=draft.id
        )
        return await self._view(draft)

    async def set_draft_scalars(
        self, version_id: uuid.UUID, patch: ScalarPatch
    ) -> CaseVersionView:
        version = await self._require_draft(version_id)
        updates = {
            name: value
            for name, value in (
                ("difficulty", patch.difficulty),
                ("target_diagnosis", patch.target_diagnosis),
                ("topic", patch.topic),
                ("iuis", patch.iuis),
            )
            if value is not None
        }
        if updates:
            await self._repo.update_version_scalars(version, **updates)
        return await self._view(version)

    async def set_draft_localization(
        self, version_id: uuid.UUID, language: str, content: dict
    ) -> CaseVersionView:
        version = await self._require_draft(version_id)
        lang = Language(language)
        await self._repo.upsert_localization(version.id, lang, dict(content))
        await self._rederive_tests_if_en(version, lang)
        return await self._view(version)

    async def set_draft_lab_data(
        self, version_id: uuid.UUID, language: str, lab_tests: list[LabTestSpec]
    ) -> CaseVersionView:
        version = await self._require_draft(version_id)
        lang = Language(language)
        existing = await self._repo.get_localization(version.id, lang)
        content = dict(existing.content) if existing is not None else {}
        lab_data: dict[str, str] = {}
        for spec in lab_tests:
            lab_data[spec.key] = spec.result_by_language.get(language, "")
        content["lab_data"] = lab_data
        await self._repo.upsert_localization(version.id, lang, content)
        if lang is Language.en:
            await self._repo.replace_tests(
                version.id, _specs_from_lab_tests(lab_tests)
            )
        return await self._view(version)

    async def preview(self, version_id: uuid.UUID, language: str) -> Case | None:
        version = await self._repo.get_version(version_id)
        if version is None:
            return None
        lang = Language(language)
        localization = await self._repo.get_localization(version.id, lang)
        if localization is None and lang is not Language.en:
            localization = await self._repo.get_localization(version.id, Language.en)
        if localization is None:
            return None
        case = await self._repo.get_case(version.case_id)
        slug = case.slug if case is not None else ""
        tests = await self._repo.get_tests(version.id)
        return project_case(slug, version, localization.content, tests)

    async def publish_version(self, version_id: uuid.UUID) -> PublishResult:
        version = await self._repo.get_version(version_id)
        if version is None:
            raise CaseAuthoringError("version_not_found")
        if version.status is CaseVersionStatus.published:
            return PublishResult(version=await self._view(version))
        await self._validate_publishable(version)
        await self._repo.publish(version)
        return PublishResult(version=await self._view(version))

    async def discard_draft(self, version_id: uuid.UUID) -> DiscardResult:
        version = await self._repo.get_version(version_id)
        if version is None:
            raise CaseAuthoringError("version_not_found")
        if version.status is CaseVersionStatus.published:
            raise CaseAuthoringError("cannot_discard_published")
        attempts = await self._repo.count_attempts_for_version(version.id)
        assignments = await self._repo.count_assignments_for_version(version.id)
        if attempts > 0 or assignments > 0:
            raise CaseAuthoringError("cannot_discard_referenced")
        case_id = version.case_id
        version_count = await self._repo.count_versions_for_case(case_id)
        await self._repo.delete_draft(version)
        deleted_case = False
        if version_count <= 1:
            await self._repo.delete_case(case_id)
            deleted_case = True
        return DiscardResult(case_id=str(case_id), deleted_case=deleted_case)

    async def _require_draft(self, version_id: uuid.UUID) -> CaseVersion:
        version = await self._repo.get_version(version_id)
        if version is None:
            raise CaseAuthoringError("version_not_found")
        if version.status is not CaseVersionStatus.draft:
            raise CaseAuthoringError("version_published")
        return version

    async def _rederive_tests_if_en(
        self, version: CaseVersion, language: Language
    ) -> None:
        if language is not Language.en:
            return
        localization = await self._repo.get_localization(version.id, Language.en)
        if localization is None:
            return
        lab_data = localization.content.get("lab_data")
        if not isinstance(lab_data, dict):
            return
        existing = {t.key: t.kind for t in await self._repo.get_tests(version.id)}
        specs: list[TestSpec] = []
        for ord_index, key in enumerate(lab_data.keys()):
            kind = existing.get(key, CaseTestKind.numeric_panel)
            specs.append(TestSpec(key=key, kind=kind.value, ord=ord_index))
        await self._repo.replace_tests(version.id, specs)

    async def _validate_publishable(self, version: CaseVersion) -> None:
        errors: list[str] = []
        for name in SCALAR_FIELDS:
            if not _non_empty_str(getattr(version, name, "")):
                errors.append(f"scalar.{name}")

        en = await self._repo.get_localization(version.id, Language.en)
        if en is None:
            errors.append("localization.en")
            raise CaseAuthoringError("incomplete_localization", errors)
        content = en.content
        for key in RUNTIME_CONTENT_KEYS:
            if key not in content:
                errors.append(f"en.{key}")
                continue
            value = content[key]
            if key == "lab_data":
                continue
            if key in ("red_flags", "key_clues"):
                if not isinstance(value, list) or not value:
                    errors.append(f"en.{key}")
            elif key == "wrong_paths":
                if not isinstance(value, dict) or not value:
                    errors.append(f"en.{key}")
            elif not _non_empty_str(value):
                errors.append(f"en.{key}")
        _validate_lab_data(content, "en.", errors)

        lv = await self._repo.get_localization(version.id, Language.lv)
        if lv is not None:
            en_lab = content.get("lab_data")
            lv_lab = lv.content.get("lab_data")
            en_wrong = content.get("wrong_paths")
            lv_wrong = lv.content.get("wrong_paths")
            if (
                isinstance(en_lab, dict)
                and isinstance(lv_lab, dict)
                and set(en_lab.keys()) != set(lv_lab.keys())
            ):
                errors.append("lv.lab_data.keys")
            if (
                isinstance(en_wrong, dict)
                and isinstance(lv_wrong, dict)
                and set(en_wrong.keys()) != set(lv_wrong.keys())
            ):
                errors.append("lv.wrong_paths.keys")

        if errors:
            raise CaseAuthoringError("incomplete_localization", errors)

    async def _has_lv(self, version_id: uuid.UUID) -> bool:
        return (
            await self._repo.get_localization(version_id, Language.lv) is not None
        )

    async def _view(self, version: CaseVersion) -> CaseVersionView:
        case = await self._repo.get_case(version.case_id)
        slug = case.slug if case is not None else ""
        is_current = (
            case is not None and case.current_version_id == version.id
        )
        localizations = [
            CaseLocalizationView(language=loc.language.value, content=loc.content)
            for loc in await self._repo.get_localizations(version.id)
        ]
        tests = [
            CaseTestView(key=t.key, kind=t.kind.value, ord=t.ord)
            for t in await self._repo.get_tests(version.id)
        ]
        return CaseVersionView(
            case_id=str(version.case_id),
            slug=slug,
            version_id=str(version.id),
            version_no=version.version_no,
            status=version.status.value,
            is_current=is_current,
            difficulty=version.difficulty,
            topic=version.topic,
            target_diagnosis=version.target_diagnosis,
            iuis=version.iuis,
            localizations=localizations,
            tests=tests,
        )


def _specs_from_lab_tests(lab_tests: list[LabTestSpec]) -> list[TestSpec]:
    specs: list[TestSpec] = []
    for ord_index, spec in enumerate(lab_tests):
        kind = spec.kind if spec.kind in _VALID_KINDS else CaseTestKind.numeric_panel.value
        specs.append(TestSpec(key=spec.key, kind=kind, ord=ord_index))
    return specs


def _summary_from_row(row: CaseSummaryRow, has_lv: bool) -> CaseSummary:
    return CaseSummary(
        case_id=str(row.case_id),
        slug=row.slug,
        version_id=str(row.version_id),
        version_no=row.version_no,
        status=row.status.value,
        is_current=row.current_version_id == row.version_id,
        difficulty=row.difficulty,
        topic=row.topic,
        target_diagnosis=row.target_diagnosis,
        iuis=row.iuis,
        has_lv=has_lv,
        created_at=row.created_at,
    )
