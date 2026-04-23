from langchain_groq import ChatGroq
from langchain_core.messages import BaseMessage

from backend.models.schemas import EvaluationResult
from backend.config import GROQ_API_KEY, MODEL_NAME


# -------------------
# 1. LLM
# -------------------
llm       = ChatGroq(api_key=GROQ_API_KEY, model=MODEL_NAME, temperature=0)
evaluator = llm.with_structured_output(EvaluationResult)


# -------------------
# 2. Evaluator
# -------------------
def evaluate_interview(messages: list[BaseMessage], role: str) -> EvaluationResult:
    transcript = "\n".join(
        f"{'Interviewer' if i % 2 == 0 else 'Candidate'}: {m.content}"
        for i, m in enumerate(messages)
    )

    prompt = f"""
You are an expert HR evaluator. Carefully review this interview transcript for the role: {role}

Transcript:
{transcript}

Evaluate the candidate on:
- Technical knowledge (0-10)
- Communication skills (0-10)
- Confidence and clarity (0-10)
- Overall performance (0-10)

Provide a detailed summary paragraph explaining your scores and recommendation.
    """.strip()

    return evaluator.invoke(prompt)
