from langchain_groq import ChatGroq
from tenacity import retry, wait_exponential, stop_after_attempt

from config import Config


class InterviewEngine:
    """Handles individual mock-interview answer evaluations, aware of prior
    questions/answers in the same session (conversation memory).
    """

    def __init__(self):
        self._model = ChatGroq(model=Config.MODEL_NAME, temperature=Config.MODEL_TEMPERATURE)

    @retry(wait=wait_exponential(multiplier=1, min=Config.RETRY_MIN_WAIT, max=Config.RETRY_MAX_WAIT),
           stop=stop_after_attempt(Config.RETRY_MAX_ATTEMPTS))
    def evaluate_answer(self, question: str, answer: str, job_description: str,
                         history_summary: str = "") -> dict:
        """Evaluate one interview answer, returning feedback and a model answer."""
        history_note = f"\n\nPrevious questions covered in this interview:\n{history_summary}" if history_summary else ""

        response = self._model.invoke([
            ("system", """You are an experienced interview coach. Evaluate the candidate's answer.
Respond ONLY with valid JSON in this exact format:
{
  "feedback": "2-3 sentences of specific, honest feedback on the answer",
  "model_answer": "a strong example answer to this question, 3-4 sentences"
}
No text outside the JSON."""),
            ("human", f"Job context: {job_description}\n\nQuestion: {question}\n\n"
                       f"Candidate's answer: {answer}{history_note}")
        ])

        return self._parse_evaluation(response.content)

    @retry(wait=wait_exponential(multiplier=1, min=Config.RETRY_MIN_WAIT, max=Config.RETRY_MAX_WAIT),
           stop=stop_after_attempt(Config.RETRY_MAX_ATTEMPTS))
    def generate_followup(self, question: str, answer: str, job_description: str) -> str:
        """Generate a natural follow-up question based on the candidate's answer."""
        response = self._model.invoke([
            ("system", "You are conducting a live interview. Based on the candidate's answer, ask ONE "
                       "natural, probing follow-up question - the way a real interviewer would dig deeper. "
                       "Return ONLY the follow-up question, nothing else."),
            ("human", f"Job context: {job_description}\n\nOriginal question: {question}\n\n"
                       f"Candidate's answer: {answer}")
        ])
        return response.content.strip()

    @staticmethod
    def _parse_evaluation(raw_text: str) -> dict:
        import json
        try:
            return json.loads(raw_text)
        except json.JSONDecodeError:
            return {
                "feedback": "Could not generate structured feedback.",
                "model_answer": raw_text[:300]
            }