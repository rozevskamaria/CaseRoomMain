from pydantic import BaseModel


class Case(BaseModel):
    id: str
    title: str
    topic: str
    patient: str
    difficulty: str
    opening_clinical: str
    opening: str
    target_diagnosis: str
    target_iuis: str
    red_flags: list[str]
    parent_prompt: str
    lab_data: dict[str, str]
    exam_findings: str
    model_diagnosis: str
    model_management: str
    model_genetic_counselling: str
    key_clues: list[str]
    wrong_paths: dict[str, str]
