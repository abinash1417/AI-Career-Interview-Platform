import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Central configuration for the AI Career & Interview Platform."""

    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    MODEL_NAME = "openai/gpt-oss-120b"
    MODEL_TEMPERATURE = 0.4

    RETRY_MIN_WAIT = 4
    RETRY_MAX_WAIT = 30
    RETRY_MAX_ATTEMPTS = 5

    DEFAULT_NUM_QUESTIONS = 5

    APP_TITLE = "🎯 AI Career & Interview Platform"
    APP_CAPTION = "Upload your resume and a job description to get personalized feedback, tailored interview practice, and a ready-to-send application email."
    PAGE_TITLE = "AI Career & Interview Platform"