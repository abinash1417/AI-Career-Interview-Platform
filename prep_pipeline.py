import json
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, START, END
from tenacity import retry, wait_exponential, stop_after_attempt

from config import Config
from models import PrepState


class PrepPipeline:
    """Runs once per session: analyzes the resume, finds gaps against the job
    description, and generates tailored interview questions.
    """

    def __init__(self):
        self._model = ChatGroq(model=Config.MODEL_NAME, temperature=Config.MODEL_TEMPERATURE)
        self._graph = self._build_graph()

    @retry(wait=wait_exponential(multiplier=1, min=Config.RETRY_MIN_WAIT, max=Config.RETRY_MAX_WAIT),
           stop=stop_after_attempt(Config.RETRY_MAX_ATTEMPTS))
    def _resume_analyzer_node(self, state: PrepState) -> dict:
        response = self._model.invoke([
            ("system", """You are an experienced technical recruiter reviewing a resume for a SPECIFIC job.
Your score must reflect how well this resume fits THIS job, not how good the resume looks in isolation.

If the resume's experience, skills, and background are largely UNRELATED to the job description
(e.g. a marketing resume for an engineering role), the overall_score MUST be low (2-4 range) regardless
of how well-written or polished the resume is, and you must clearly state the mismatch.

Respond ONLY with valid JSON in this exact format:
{
  "overall_score": number 1-10,
  "role_fit": "one honest sentence stating whether this resume actually fits this specific job",
  "strengths": ["...", "...", "..."],
  "weaknesses": ["...", "...", "..."],
  "missing_keywords": ["...", "..."]
}
No text outside the JSON."""),
            ("human", f"Job Description:\n{state['job_description']}\n\nResume:\n{state['resume_text']}")
        ])
        return {"resume_report_raw": response.content}

    @retry(wait=wait_exponential(multiplier=1, min=Config.RETRY_MIN_WAIT, max=Config.RETRY_MAX_WAIT),
           stop=stop_after_attempt(Config.RETRY_MAX_ATTEMPTS))
    def _gap_analysis_node(self, state: PrepState) -> dict:
        response = self._model.invoke([
            ("system", "You are a career coach. Compare the resume against the job description. "
                       "If the resume is largely unrelated to this job's field, say so plainly and "
                       "explain what fundamental gap exists (not just minor skill gaps). "
                       "Otherwise, identify specific skill gaps, experience gaps, and areas the "
                       "candidate should be ready to address. Be honest and specific, not generic. "
                       "4-6 bullet points."),
            ("human", f"Resume:\n{state['resume_text']}\n\nJob Description:\n{state['job_description']}")
        ])
        return {"gap_analysis": response.content}

    @retry(wait=wait_exponential(multiplier=1, min=Config.RETRY_MIN_WAIT, max=Config.RETRY_MAX_WAIT),
           stop=stop_after_attempt(Config.RETRY_MAX_ATTEMPTS))
    def _question_generator_node(self, state: PrepState) -> dict:
        num_questions = state.get("num_questions", Config.DEFAULT_NUM_QUESTIONS)
        response = self._model.invoke([
            ("system", f"You are an interviewer preparing for this candidate. Based on the gap analysis "
                       f"and job description, generate exactly {num_questions} interview "
                       f"questions that specifically probe the identified gaps and role requirements. "
                       f"Mix technical and behavioral questions. Return ONLY the questions, one per line, "
                       f"numbered 1-{num_questions}. No extra commentary."),
            ("human", f"Job Description:\n{state['job_description']}\n\nGap Analysis:\n{state['gap_analysis']}")
        ])
        questions = self._parse_questions(response.content, num_questions)
        return {"questions": questions}

    @staticmethod
    def _parse_questions(raw_text: str, num_questions: int) -> list[str]:
        lines = raw_text.strip().split("\n")
        questions = []
        for line in lines:
            cleaned = line.strip()
            if cleaned and cleaned[0].isdigit():
                cleaned = cleaned.split(".", 1)[-1].strip()
            if cleaned:
                questions.append(cleaned)
        return questions[:num_questions]

    def _build_graph(self):
        builder = StateGraph(PrepState)
        builder.add_node("resume_analyzer", self._resume_analyzer_node)
        builder.add_node("gap_analysis", self._gap_analysis_node)
        builder.add_node("question_generator", self._question_generator_node)

        builder.add_edge(START, "resume_analyzer")
        builder.add_edge("resume_analyzer", "gap_analysis")
        builder.add_edge("gap_analysis", "question_generator")
        builder.add_edge("question_generator", END)

        return builder.compile()

    def run(self, resume_text: str, job_description: str, num_questions: int = None) -> PrepState:
        result = self._graph.invoke({
            "resume_text": resume_text,
            "job_description": job_description,
            "resume_report_raw": "",
            "resume_report": {},
            "gap_analysis": "",
            "questions": [],
            "num_questions": num_questions or Config.DEFAULT_NUM_QUESTIONS
        })
        result["resume_report"] = self._parse_resume_report(result["resume_report_raw"])
        return result

    @staticmethod
    def _parse_resume_report(raw_text: str) -> dict:
        try:
            return json.loads(raw_text)
        except json.JSONDecodeError:
            return {
                "overall_score": None,
                "role_fit": "Could not analyze role fit.",
                "strengths": [],
                "weaknesses": [],
                "missing_keywords": [],
            }