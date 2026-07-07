from __future__ import annotations

import asyncio

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.content.cases import CASES
from app.core.db import get_sessionmaker
from app.models.case import (
    Case as CaseModel,
    CaseLocalizationEN,
    CaseTestAnalyte,
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
from app.schemas.case import Case
from app.services.case_engine import flag_row, parse_lab_text

_GENETIC_KEYWORDS = (
    "gene panel",
    "genetic",
    "exome",
    "sequencing",
    "chimerism",
    "qf-pcr",
    "mefv",
    "autoinflammatory panel",
)
_QUALITATIVE_KEYWORDS = (
    "hiv test",
    "dhr",
    "nbt",
    "trec",
    "monospot",
    "ebv serology",
    "skin prick",
    "allergy test",
    "oxidative burst",
)
_MICROBIOLOGY_KEYWORDS = (
    "culture",
    "swab",
    "stool examination",
    "sputum",
    "bal ",
    "pcr",
)
_IMAGING_KEYWORDS = (
    "x-ray",
    "xray",
    " ct",
    "ct ",
    "ultrasound",
    "echocardiogram",
    "ecg",
    "colonoscopy",
    "biopsy",
    "imaging",
    "radiograph",
    "opg",
    "panoramic",
    "dexa",
    "mri",
    "scan",
    "endoscopy",
)

_KIND_MODEL = {
    CaseTestKind.numeric_panel: NumericPanelTest,
    CaseTestKind.imaging: ImagingTest,
    CaseTestKind.microbiology: MicrobiologyTest,
    CaseTestKind.genetic: GeneticTest,
    CaseTestKind.qualitative: QualitativeTest,
}


def classify_test_kind(test_name: str) -> CaseTestKind:
    n = test_name.lower()
    if any(k in n for k in _GENETIC_KEYWORDS):
        return CaseTestKind.genetic
    if any(k in n for k in _QUALITATIVE_KEYWORDS):
        return CaseTestKind.qualitative
    if any(k in n for k in _MICROBIOLOGY_KEYWORDS):
        return CaseTestKind.microbiology
    if any(k in n for k in _IMAGING_KEYWORDS):
        return CaseTestKind.imaging
    return CaseTestKind.numeric_panel


def _build_content(case: Case) -> dict:
    content = case.model_dump()
    content["lab_data"] = {k: v for k, v in case.lab_data.items()}
    content["wrong_paths"] = {k: v for k, v in case.wrong_paths.items()}
    content["red_flags"] = list(case.red_flags)
    content["key_clues"] = list(case.key_clues)
    return content


async def _seed_case(session: AsyncSession, case: Case) -> None:
    existing = await session.scalar(
        select(CaseModel).where(CaseModel.slug == case.id)
    )
    if existing is not None:
        return

    case_row = CaseModel(slug=case.id)
    session.add(case_row)
    await session.flush()

    version = CaseVersion(
        case_id=case_row.id,
        version_no=1,
        status=CaseVersionStatus.published,
        difficulty=case.difficulty,
        target_diagnosis=case.target_diagnosis,
        topic=case.topic,
        iuis=case.target_iuis,
        created_by=None,
    )
    session.add(version)
    await session.flush()

    case_row.current_version_id = version.id

    localization = CaseLocalizationEN(
        case_version_id=version.id,
        language=Language.en,
        content=_build_content(case),
    )
    session.add(localization)

    for ord_index, (test_name, result_text) in enumerate(case.lab_data.items()):
        kind = classify_test_kind(test_name)
        model_cls = _KIND_MODEL[kind]
        columns = {
            "case_version_id": version.id,
            "key": test_name,
            "kind": kind,
            "ord": ord_index,
        }
        test_row = model_cls(**columns)
        session.add(test_row)
        await session.flush()

        if kind is CaseTestKind.numeric_panel:
            analyte_ord = 0
            for parsed in parse_lab_text(result_text):
                if parsed["type"] != "row":
                    continue
                session.add(
                    CaseTestAnalyte(
                        case_test_id=test_row.id,
                        analyte=parsed["param"],
                        value=parsed["value"],
                        unit=None,
                        ref_range=None,
                        flag=flag_row(parsed["value"]),
                        ord=analyte_ord,
                    )
                )
                analyte_ord += 1

    await session.flush()


async def seed(session: AsyncSession) -> None:
    for case in CASES.values():
        await _seed_case(session, case)


async def main() -> None:
    sessionmaker = get_sessionmaker()
    async with sessionmaker() as session:
        await seed(session)
        await session.commit()


if __name__ == "__main__":
    asyncio.run(main())
