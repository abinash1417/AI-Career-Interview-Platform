# 🎯 AI Career & Interview Platform

An end-to-end job preparation assistant: upload your resume and a target job description, get an honest, role-aware resume review, practice with tailored mock interview questions that adapt as you answer, and generate a ready-to-send application email.

## What it does

1. **Resume Analysis** — scores your resume specifically against the job you're applying for (not just "is this a good resume" in isolation), flags a genuine mismatch if your background doesn't fit the role, and lists strengths, weaknesses, and missing keywords
2. **Gap Analysis** — compares your resume against the job description to identify specific skill and experience gaps
3. **Mock Interview** — generates a user-chosen number of interview questions tailored to the identified gaps and role, mixing technical and behavioral questions
4. **Answer Evaluation** — after each answer, generates specific feedback and a model answer for comparison, aware of the questions already covered in the session
5. **Email Generator** — writes a tailored job application email using your resume and the job description

## Why role-aware scoring matters

An earlier version of this project scored resumes in isolation — a well-written resume for a completely unrelated field (e.g. a marketing resume submitted against a software engineering job) still received a high score, because the model was only judging resume quality, not job fit. This was caught through testing with a deliberately mismatched resume/job pair, and fixed by rewriting the analyzer's prompt to require both documents together and explicitly penalize genuine field mismatches, regardless of how polished the resume looks.

## Architecture

```
User uploads Resume (PDF) + pastes Job Description + chooses question count
       |
       v
Resume Analyzer (scores role FIT, not just resume quality)
       |
       v
Gap Analysis (specific skill/experience gaps vs this job)
       |
       v
Question Generator (N tailored questions, technical + behavioral)
       |
       v
Mock Interview Loop:
   User answers -> Answer Evaluator (feedback + model answer, aware of prior Q&A)
       |
       v
Email Generator (tailored application email)
```

## Tech Stack

- **LLM:** Groq (`openai/gpt-oss-120b`) via LangChain
- **Orchestration:** LangGraph (StateGraph for the resume -> gap -> questions pipeline)
- **Session Memory:** Streamlit `session_state` for multi-step flow, plus interview history passed into each answer evaluation for adaptive, context-aware feedback
- **Frontend:** Streamlit
- **Resilience:** `tenacity` for automatic retry on API rate limits

## Project Structure

```
AI-Career-Interview-Platform/
├── app.py                    # Streamlit UI - multi-step flow with session state
├── config.py                  # Centralized settings
├── models.py                   # CareerProfile, InterviewTurn, PrepState, InterviewState
├── document_processor.py        # ResumeParser - PDF text extraction
├── prep_pipeline.py              # PrepPipeline - resume/gap/question LangGraph pipeline
├── interview_engine.py            # InterviewEngine - answer evaluation with history awareness
├── email_generator.py              # EmailGenerator - few-shot tailored email writing
├── static/
│   └── style.css                     # UI styling
└── requirements.txt
```

## Running Locally

```bash
git clone https://github.com/abinash1417/AI-Career-Interview-Platform.git
cd AI-Career-Interview-Platform
python -m venv venv
venv\Scripts\activate   # or source venv/bin/activate on Mac/Linux
pip install -r requirements.txt
```

Create a `.env` file with:

```
GROQ_API_KEY=your_key_here
```

Then run:

```bash
streamlit run app.py
```

## Known Limitations

- Resume parsing works best with standard, text-based PDFs (scanned/image-based resumes are not OCR'd)
- Mock interview follow-ups are generated per-answer but not yet chained into true multi-turn back-and-forth within a single question
- Groq's free tier rate limit (8,000 tokens/minute) may cause delays with very long resumes or job descriptions

## What I'd Add Next

- True multi-turn follow-up questioning within a single interview question, not just across questions
- Voice input/output for a more realistic mock interview experience
- Downloadable PDF report summarizing the full session (resume feedback, interview performance, email)