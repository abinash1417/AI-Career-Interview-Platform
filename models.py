from dataclasses import dataclass, field
from typing import TypedDict


@dataclass
class CareerProfile:
    """Holds the user's resume text and target job description together."""
    resume_text: str
    job_description: str

    def is_valid(self) -> bool:
        return bool(self.resume_text.strip() and self.job_description.strip())


@dataclass
class InterviewTurn:
    """One question-answer exchange in a mock interview."""
    question: str
    answer: str = ""
    feedback: str = ""
    model_answer: str = ""


class PrepState(TypedDict):
    """Shared state for the resume -> gap analysis -> questions pipeline."""
    resume_text: str
    job_description: str
    resume_report_raw: str
    resume_report: dict
    gap_analysis: str
    questions: list[str]
    num_questions: int


class InterviewState(TypedDict):
    """Shared state for a single mock-interview answer evaluation turn."""
    question: str
    answer: str
    job_description: str
    history_summary: str
    feedback: str
    model_answer: str