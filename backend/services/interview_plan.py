from langchain_groq import ChatGroq

from backend.models.schemas import InterviewPlan
from backend.config import GROQ_API_KEY, MODEL_NAME


# -------------------
# 1. LLM
# -------------------
llm            = ChatGroq(api_key=GROQ_API_KEY, model=MODEL_NAME, temperature=0.7)
plan_generator = llm.with_structured_output(InterviewPlan)


# -------------------
# 2. Generator
# -------------------
def generate_interview_plan(resume_info: dict, jd_info: dict) -> InterviewPlan:
    prompt = f"""
Generate a structured interview plan for the following candidate.

Candidate Profile:
- Name          : {resume_info.get('name')}
- Skills        : {', '.join(resume_info.get('skills', []))}
- Experience    : {resume_info.get('experience')}
- Education     : {resume_info.get('education')}

Job Details:
- Role             : {jd_info.get('role')}
- Required Skills  : {', '.join(jd_info.get('required_skills', []))}
- Experience Level : {jd_info.get('experience_level')}

Generate:
- 1 introduction / warm-up question (about the candidate, their background)
- 1 technical question (specific to the role and required skills)
- 1 behavioral question (situational, past experience, problem-solving)

Questions must be open-ended and conversational.
    """.strip()

    return plan_generator.invoke(prompt)
