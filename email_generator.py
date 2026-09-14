from langchain_groq import ChatGroq
from tenacity import retry, wait_exponential, stop_after_attempt

from config import Config


class EmailGenerator:
    """Generates a tailored job application email using the resume and job description."""

    FEW_SHOT_EXAMPLE = """Example:
Purpose: Apply for a role, express strong fit
Email:
Subject: Application for Software Engineer Role - [Your Name]

Dear Hiring Manager,

I'm excited to apply for the Software Engineer position. With hands-on experience in Python,
machine learning, and building full-stack AI applications, I believe I'd be a strong fit for
your team's goals around [specific thing from job description].

I've attached my resume for your review and would welcome the opportunity to discuss how my
background aligns with what you're looking for.

Best regards,
[Your Name]"""

    def __init__(self):
        self._model = ChatGroq(model=Config.MODEL_NAME, temperature=Config.MODEL_TEMPERATURE)

    @retry(wait=wait_exponential(multiplier=1, min=Config.RETRY_MIN_WAIT, max=Config.RETRY_MAX_WAIT),
           stop=stop_after_attempt(Config.RETRY_MAX_ATTEMPTS))
    def generate(self, resume_text: str, job_description: str) -> str:
        response = self._model.invoke([
            ("system", "You are a professional career coach writing job application emails. "
                       "Write clear, genuine, tailored emails - avoid generic filler phrases."),
            ("human", f"{self.FEW_SHOT_EXAMPLE}\n\nNow write a new application email for this candidate:\n\n"
                       f"Resume:\n{resume_text}\n\nJob Description:\n{job_description}\n\nEmail:")
        ])
        return response.content