import streamlit as st
from document_processor import ResumeParser
from prep_pipeline import PrepPipeline
from interview_engine import InterviewEngine
from email_generator import EmailGenerator
from config import Config

st.set_page_config(page_title=Config.PAGE_TITLE, layout="wide", page_icon="🎯")


def load_custom_css():
    with open("static/style.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


@st.cache_resource
def get_prep_pipeline() -> PrepPipeline:
    return PrepPipeline()


@st.cache_resource
def get_interview_engine() -> InterviewEngine:
    return InterviewEngine()


@st.cache_resource
def get_email_generator() -> EmailGenerator:
    return EmailGenerator()


def init_session_state():
    defaults = {
        "prep_done": False,
        "resume_text": "",
        "job_description": "",
        "resume_report": {},
        "gap_analysis": "",
        "questions": [],
        "current_q_index": 0,
        "interview_history": [],
        "generated_email": ""
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def render_upload_section(prep_pipeline: PrepPipeline):
    st.markdown("### 📄 Step 1: Upload Resume & Job Description")

    col1, col2 = st.columns(2)
    with col1:
        resume_file = st.file_uploader("Upload your resume (PDF)", type="pdf")
    with col2:
        job_description = st.text_area("Paste the job description", height=200)

    num_questions = st.number_input(
        "How many interview questions would you like?",
        min_value=1, max_value=30, value=Config.DEFAULT_NUM_QUESTIONS, step=1
    )

    if st.button("🚀 Analyze & Prepare", type="primary"):
        if not resume_file or not job_description.strip():
            st.warning("Please upload a resume and paste a job description.")
            return

        with st.spinner("Analyzing resume, finding gaps, generating interview questions..."):
            resume_text = ResumeParser.extract_text(resume_file)
            result = prep_pipeline.run(resume_text, job_description, int(num_questions))

        st.session_state.resume_text = resume_text
        st.session_state.job_description = job_description
        st.session_state.resume_report = result["resume_report"]
        st.session_state.gap_analysis = result["gap_analysis"]
        st.session_state.questions = result["questions"]
        st.session_state.prep_done = True
        st.session_state.current_q_index = 0
        st.session_state.interview_history = []
        st.rerun()


def render_resume_report():
    report = st.session_state.resume_report
    st.markdown("### 📊 Resume Analysis")

    score = report.get("overall_score")
    if score is not None:
        st.metric("Overall Resume Score", f"{score}/10")

    role_fit = report.get("role_fit")
    if role_fit:
        if score is not None and score <= 4:
            st.warning(f"**Role Fit:** {role_fit}")
        else:
            st.info(f"**Role Fit:** {role_fit}")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**✅ Strengths**")
        for s in report.get("strengths", []):
            st.markdown(f"- {s}")
    with col2:
        st.markdown("**⚠️ Weaknesses**")
        for w in report.get("weaknesses", []):
            st.markdown(f"- {w}")

    if report.get("missing_keywords"):
        st.markdown("**🔑 Missing Keywords:** " + ", ".join(report["missing_keywords"]))

    with st.expander("📋 Gap Analysis vs Job Description"):
        st.write(st.session_state.gap_analysis)


def render_mock_interview(interview_engine: InterviewEngine):
    st.markdown("### 🎤 Step 2: Mock Interview")

    questions = st.session_state.questions
    idx = st.session_state.current_q_index

    if idx >= len(questions):
        st.success("✅ Interview complete! Review your feedback below.")
        for i, turn in enumerate(st.session_state.interview_history, 1):
            with st.expander(f"Q{i}: {turn['question']}"):
                st.markdown(f"**Your answer:** {turn['answer']}")
                st.markdown(f"**Feedback:** {turn['feedback']}")
                st.markdown(f"**Model answer:** {turn['model_answer']}")
        return

    question = questions[idx]
    st.markdown(f"**Question {idx + 1} of {len(questions)}:**")
    st.info(question)

    answer = st.text_area("Your answer", key=f"answer_{idx}", height=120)

    if st.button("Submit Answer", type="primary", key=f"submit_{idx}"):
        if not answer.strip():
            st.warning("Please write an answer first.")
            return

        history_summary = "\n".join(
            f"- {t['question']}" for t in st.session_state.interview_history
        )

        with st.spinner("Evaluating your answer..."):
            evaluation = interview_engine.evaluate_answer(
                question, answer, st.session_state.job_description, history_summary
            )

        st.session_state.interview_history.append({
            "question": question,
            "answer": answer,
            "feedback": evaluation["feedback"],
            "model_answer": evaluation["model_answer"]
        })

        st.markdown("**Feedback:** " + evaluation["feedback"])
        st.markdown("**Model answer:** " + evaluation["model_answer"])

        st.session_state.current_q_index += 1
        if st.button("Next Question ➡️"):
            st.rerun()


def render_email_section(email_generator: EmailGenerator):
    st.markdown("### ✉️ Step 3: Generate Application Email")

    if st.button("Generate Email"):
        with st.spinner("Writing a tailored application email..."):
            email = email_generator.generate(
                st.session_state.resume_text, st.session_state.job_description
            )
        st.session_state.generated_email = email

    if st.session_state.generated_email:
        st.text_area("Your generated email", st.session_state.generated_email, height=250)


def main():
    load_custom_css()
    init_session_state()

    st.title(Config.APP_TITLE)
    st.caption(Config.APP_CAPTION)
    st.markdown("---")

    prep_pipeline = get_prep_pipeline()
    interview_engine = get_interview_engine()
    email_generator = get_email_generator()

    if not st.session_state.prep_done:
        render_upload_section(prep_pipeline)
        return

    render_resume_report()
    st.markdown("---")
    render_mock_interview(interview_engine)
    st.markdown("---")
    render_email_section(email_generator)

    if st.button("🔄 Start Over with a New Resume/Job"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()


if __name__ == "__main__":
    main()