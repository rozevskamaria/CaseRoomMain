from app.content.cases.xla import XLA
from app.schemas.case import Case


CASES: dict[str, Case] = {
    XLA.id: XLA,
}


def get_case(case_id: str) -> Case | None:
    return CASES.get(case_id)
