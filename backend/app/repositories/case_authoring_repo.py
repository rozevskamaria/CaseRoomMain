from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.assignment import Assignment
from app.models.attempt import Attempt
from app.models.case import (
    Case as CaseModel,
    CaseLocalization,
    CaseLocalizationEN,
    CaseLocalizationLV,
    CaseTest,
    CaseTestKind,
    CaseVersion,
    CaseVersionStatus,
    GeneticTest,
    ImagingTest,
    Language,
    MicrobiologyTest,
    NumericPanelTest,
    QualitativeTest,
)

_LOCALIZATION_BY_LANGUAGE = {
    Language.en: CaseLocalizationEN,
    Language.lv: CaseLocalizationLV,
}

_TEST_MODEL_BY_KIND = {
    CaseTestKind.numeric_panel: NumericPanelTest,
    CaseTestKind.imaging: ImagingTest,
    CaseTestKind.microbiology: MicrobiologyTest,
    CaseTestKind.genetic: GeneticTest,
    CaseTestKind.qualitative: QualitativeTest,
}


@dataclass
class TestSpec:
    key: str
    kind: str
    ord: int


@dataclass
class CaseSummaryRow:
    case_id: uuid.UUID
    slug: str
    current_version_id: uuid.UUID | None
    version_id: uuid.UUID
    version_no: int
    status: CaseVersionStatus
    difficulty: str
    topic: str
    target_diagnosis: str
    iuis: str
    created_at: object


class CaseAuthoringRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_case(self, case_id: uuid.UUID) -> CaseModel | None:
        return await self._session.get(CaseModel, case_id)

    async def get_case_by_slug(self, slug: str) -> CaseModel | None:
        return await self._session.scalar(
            select(CaseModel).where(CaseModel.slug == slug)
        )

    async def get_version(self, version_id: uuid.UUID) -> CaseVersion | None:
        return await self._session.get(CaseVersion, version_id)

    async def get_open_draft(self, case_id: uuid.UUID) -> CaseVersion | None:
        stmt = (
            select(CaseVersion)
            .where(CaseVersion.case_id == case_id)
            .where(CaseVersion.status == CaseVersionStatus.draft)
            .order_by(CaseVersion.version_no.desc())
            .limit(1)
        )
        return await self._session.scalar(stmt)

    async def max_version_no(self, case_id: uuid.UUID) -> int:
        value = await self._session.scalar(
            select(func.max(CaseVersion.version_no)).where(
                CaseVersion.case_id == case_id
            )
        )
        return int(value or 0)

    async def list_versions(self) -> list[CaseSummaryRow]:
        stmt = (
            select(CaseModel, CaseVersion)
            .join(CaseVersion, CaseVersion.case_id == CaseModel.id)
            .order_by(CaseModel.slug, CaseVersion.version_no.desc())
        )
        result = await self._session.execute(stmt)
        rows: list[CaseSummaryRow] = []
        for case, version in result.all():
            rows.append(
                CaseSummaryRow(
                    case_id=case.id,
                    slug=case.slug,
                    current_version_id=case.current_version_id,
                    version_id=version.id,
                    version_no=version.version_no,
                    status=version.status,
                    difficulty=version.difficulty,
                    topic=version.topic,
                    target_diagnosis=version.target_diagnosis,
                    iuis=version.iuis,
                    created_at=version.created_at,
                )
            )
        return rows

    async def get_localizations(
        self, case_version_id: uuid.UUID
    ) -> list[CaseLocalization]:
        stmt = select(CaseLocalization).where(
            CaseLocalization.case_version_id == case_version_id
        )
        result = await self._session.scalars(stmt)
        return list(result)

    async def get_localization(
        self, case_version_id: uuid.UUID, language: Language
    ) -> CaseLocalization | None:
        stmt = (
            select(CaseLocalization)
            .where(CaseLocalization.case_version_id == case_version_id)
            .where(CaseLocalization.language == language)
        )
        return await self._session.scalar(stmt)

    async def get_tests(self, case_version_id: uuid.UUID) -> list[CaseTest]:
        stmt = (
            select(CaseTest)
            .where(CaseTest.case_version_id == case_version_id)
            .order_by(CaseTest.ord)
        )
        result = await self._session.scalars(stmt)
        return list(result)

    async def create_case(self, slug: str) -> CaseModel:
        case = CaseModel(slug=slug)
        self._session.add(case)
        await self._session.flush()
        return case

    async def create_version(
        self,
        *,
        case_id: uuid.UUID,
        version_no: int,
        difficulty: str,
        topic: str,
        target_diagnosis: str,
        iuis: str,
        created_by: uuid.UUID | None,
    ) -> CaseVersion:
        version = CaseVersion(
            case_id=case_id,
            version_no=version_no,
            status=CaseVersionStatus.draft,
            difficulty=difficulty,
            target_diagnosis=target_diagnosis,
            topic=topic,
            iuis=iuis,
            created_by=created_by,
        )
        self._session.add(version)
        await self._session.flush()
        return version

    async def clone_into_draft(
        self, *, src_version_id: uuid.UUID, dst_version_id: uuid.UUID
    ) -> None:
        for localization in await self.get_localizations(src_version_id):
            model_cls = _LOCALIZATION_BY_LANGUAGE[localization.language]
            self._session.add(
                model_cls(
                    case_version_id=dst_version_id,
                    language=localization.language,
                    content=dict(localization.content),
                )
            )
        for test in await self.get_tests(src_version_id):
            model_cls = _TEST_MODEL_BY_KIND[test.kind]
            self._session.add(
                model_cls(
                    case_version_id=dst_version_id,
                    key=test.key,
                    kind=test.kind,
                    ord=test.ord,
                )
            )
        await self._session.flush()

    async def update_version_scalars(
        self, version: CaseVersion, **fields: str
    ) -> None:
        for name, value in fields.items():
            setattr(version, name, value)
        await self._session.flush()

    async def upsert_localization(
        self, version_id: uuid.UUID, language: Language, content: dict
    ) -> None:
        existing = await self.get_localization(version_id, language)
        if existing is not None:
            existing.content = content
        else:
            model_cls = _LOCALIZATION_BY_LANGUAGE[language]
            self._session.add(
                model_cls(
                    case_version_id=version_id,
                    language=language,
                    content=content,
                )
            )
        await self._session.flush()

    async def replace_tests(
        self, version_id: uuid.UUID, specs: list[TestSpec]
    ) -> None:
        for test in await self.get_tests(version_id):
            await self._session.delete(test)
        await self._session.flush()
        for spec in specs:
            kind = CaseTestKind(spec.kind)
            model_cls = _TEST_MODEL_BY_KIND[kind]
            self._session.add(
                model_cls(
                    case_version_id=version_id,
                    key=spec.key,
                    kind=kind,
                    ord=spec.ord,
                )
            )
        await self._session.flush()

    async def publish(self, version: CaseVersion) -> None:
        version.status = CaseVersionStatus.published
        case = await self.get_case(version.case_id)
        if case is not None:
            case.current_version_id = version.id
        await self._session.flush()

    async def count_attempts_for_version(self, version_id: uuid.UUID) -> int:
        value = await self._session.scalar(
            select(func.count())
            .select_from(Attempt)
            .where(Attempt.case_version_id == version_id)
        )
        return int(value or 0)

    async def count_assignments_for_version(self, version_id: uuid.UUID) -> int:
        value = await self._session.scalar(
            select(func.count())
            .select_from(Assignment)
            .where(Assignment.case_version_id == version_id)
        )
        return int(value or 0)

    async def count_versions_for_case(self, case_id: uuid.UUID) -> int:
        value = await self._session.scalar(
            select(func.count())
            .select_from(CaseVersion)
            .where(CaseVersion.case_id == case_id)
        )
        return int(value or 0)

    async def delete_draft(self, version: CaseVersion) -> None:
        for localization in await self.get_localizations(version.id):
            await self._session.delete(localization)
        for test in await self.get_tests(version.id):
            await self._session.delete(test)
        await self._session.flush()
        case = await self.get_case(version.case_id)
        if case is not None and case.current_version_id == version.id:
            case.current_version_id = None
            await self._session.flush()
        await self._session.delete(version)
        await self._session.flush()

    async def delete_case(self, case_id: uuid.UUID) -> None:
        case = await self.get_case(case_id)
        if case is not None:
            await self._session.delete(case)
            await self._session.flush()
