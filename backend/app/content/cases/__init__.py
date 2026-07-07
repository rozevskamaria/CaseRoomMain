from app.content.cases.cgd import CGD
from app.content.cases.hies import HIES
from app.content.cases.pfapa import PFAPA
from app.content.cases.scid import SCID
from app.content.cases.thi import THI
from app.content.cases.xla import XLA
from app.schemas.case import Case


CASES: dict[str, Case] = {
    XLA.id: XLA,
    CGD.id: CGD,
    PFAPA.id: PFAPA,
    HIES.id: HIES,
    SCID.id: SCID,
    THI.id: THI,
}


def get_case(case_id: str) -> Case | None:
    return CASES.get(case_id)
