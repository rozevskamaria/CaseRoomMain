from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.case import (
    Case as CaseModel,
    CaseLocalization,
    CaseTest,
    CaseVersion,
    CaseVersionStatus,
    Language,
)
from app.schemas.case import Case


def order_lab_data(
    tests: list[CaseTest], lab_data: dict[str, str]
) -> dict[str, str]:
    ordered = {test.key: lab_data[test.key] for test in tests if test.key in lab_data}
    for key, value in lab_data.items():
        if key not in ordered:
            ordered[key] = value
    return ordered


def project_case(
    slug: str,
    version: CaseVersion,
    content: dict,
    tests: list[CaseTest],
) -> Case:
    return Case(
        id=slug,
        title=content["title"],
        topic=version.topic,
        patient=content["patient"],
        difficulty=version.difficulty,
        opening_clinical=content["opening_clinical"],
        opening=content["opening"],
        target_diagnosis=version.target_diagnosis,
        target_iuis=version.iuis,
        red_flags=list(content["red_flags"]),
        parent_prompt=content["parent_prompt"],
        lab_data=order_lab_data(tests, content["lab_data"]),
        exam_findings=content["exam_findings"],
        model_diagnosis=content["model_diagnosis"],
        model_management=content["model_management"],
        model_genetic_counselling=content["model_genetic_counselling"],
        key_clues=list(content["key_clues"]),
        wrong_paths=dict(content["wrong_paths"]),
    )


class CaseRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_case_by_slug(self, slug: str) -> CaseModel | None:
        return await self._session.scalar(
            select(CaseModel).where(CaseModel.slug == slug)
        )

    async def get_case_version(self, slug: str) -> CaseVersion | None:
        stmt = (
            select(CaseVersion)
            .join(CaseModel, CaseModel.id == CaseVersion.case_id)
            .where(CaseModel.slug == slug)
            .where(CaseVersion.status == CaseVersionStatus.published)
            .order_by(CaseVersion.version_no.desc())
            .limit(1)
        )
        return await self._session.scalar(stmt)

    async def get_localization(
        self, case_version_id: uuid.UUID, language: str
    ) -> CaseLocalization | None:
        stmt = (
            select(CaseLocalization)
            .where(CaseLocalization.case_version_id == case_version_id)
            .where(CaseLocalization.language == Language(language))
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

    async def list_published_slugs(self) -> list[str]:
        stmt = (
            select(CaseModel.slug)
            .join(CaseVersion, CaseVersion.case_id == CaseModel.id)
            .where(CaseVersion.status == CaseVersionStatus.published)
            .order_by(CaseModel.slug)
            .distinct()
        )
        result = await self._session.scalars(stmt)
        return list(result)

    async def _ordered_lab_data(
        self, case_version_id: uuid.UUID, lab_data: dict[str, str]
    ) -> dict[str, str]:
        tests = await self.get_tests(case_version_id)
        return order_lab_data(tests, lab_data)

    async def get_published_case(
        self, slug: str, language: str = "en"
    ) -> Case | None:
        version = await self.get_case_version(slug)
        if version is None:
            return None
        localization = await self.get_localization(version.id, language)
        if localization is None and language != "en":
            localization = await self.get_localization(version.id, "en")
        if localization is None:
            return None
        tests = await self.get_tests(version.id)
        return project_case(slug, version, localization.content, tests)
