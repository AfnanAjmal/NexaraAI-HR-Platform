from typing import Literal, List

from langchain_groq import ChatGroq
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from backend.graph.state import InterviewState
from backend.config import GROQ_API_KEY, MODEL_NAME


# -------------------
# 1. LLM
# -------------------
llm = ChatGroq(api_key=GROQ_API_KEY, model=MODEL_NAME, temperature=0.7)


# -------------------
# 2. Constants
# -------------------
PHASE_ORDER   = ["intro", "technical", "behavioral"]

HUMAN_PHRASES = [
    "That's interesting, thank you for sharing.",
    "I see, that gives me a good picture.",
    "Alright, let's continue.",
    "Good answer! Moving forward.",
    "I appreciate your response.",
    "That's a great point.",
    "Thank you for being so detailed.",
]


# -------------------
# 3. Helpers
# -------------------
def get_ack(index: int) -> str:
    return HUMAN_PHRASES[index % len(HUMAN_PHRASES)]


def get_next_phase(current_phase: str):
    idx = PHASE_ORDER.index(current_phase)
    return PHASE_ORDER[idx + 1] if idx + 1 < len(PHASE_ORDER) else None


# -------------------
# 4. Nodes
# -------------------
def ask_question(state: InterviewState):
    phase  = state["phase"]
    index  = state["question_index"]
    q_list = state["questions"].get(phase, [])

    if index >= len(q_list):
        return {
            "phase"        : "done",
            "last_response": "Thank you for your time! The interview is complete. We'll be in touch soon. 🙏",
            "messages"     : [AIMessage(content="The interview is complete. We'll be in touch soon. 🙏")],
        }

    question = q_list[index]
    return {
        "current_question": question,
        "last_response"   : question,
        "messages"        : [AIMessage(content=question)],
    }


def input_router_node(state: InterviewState):
    return state


def silence_handler(state: InterviewState):
    count = state["silence_count"] + 1
    if count >= 3:
        msg = f"Take your time. Let me rephrase — {state['current_question']}"
    else:
        msg = "Take your time! Whenever you're ready, please go ahead. 😊"
    return {
        "silence_count": count,
        "last_response": msg,
        "messages"     : [AIMessage(content=msg)],
    }


def company_rag_answer(state: InterviewState):
    from backend.services.rag import rag_pipeline
    answer   = rag_pipeline(state["last_user_input"])
    response = f"{answer}\n\nNow, back to our interview — {state['current_question']}"
    return {
        "last_response": response,
        "messages"     : [AIMessage(content=response)],
    }


def repeat_question(state: InterviewState):
    msg = f"Of course! Here's the question again:\n\n{state['current_question']}"
    return {
        "last_response": msg,
        "messages"     : [AIMessage(content=msg)],
    }


def normal_interview_flow(state: InterviewState):
    ack   = get_ack(state["question_index"])
    phase = state["phase"]

    follow_up_prompt = (
        f"You are a professional AI interviewer named Sarah.\n"
        f"The candidate just answered this question:\n"
        f'Question: "{state["current_question"]}"\n'
        f'Answer: "{state["last_user_input"]}"\n\n'
        f"The answer has {len(state['last_user_input'].split())} words.\n\n"
        f"Rules:\n"
        f"- If the answer is completely empty or just 1-2 meaningless words "
        f"(like 'yes', 'ok', 'fine'), reply with FOLLOWUP: and a short "
        f"clarifying question.\n"
        f"- For ALL other answers, even short ones, reply with ACK: and a "
        f"natural 1-sentence acknowledgment like '{ack}'. "
        f"Do NOT ask any question.\n\n"
        f"Reply with either FOLLOWUP: or ACK: prefix only."
    )

    ai_reaction = llm.invoke([SystemMessage(content=follow_up_prompt)]).content.strip()

    is_followup  = ai_reaction.upper().startswith("FOLLOWUP:")
    clean_reaction = ai_reaction.split(":", 1)[1].strip() if ":" in ai_reaction else ai_reaction

    # Short answer — ask follow-up, stay on same question
    if is_followup:
        return {
            "phase"           : phase,
            "question_index"  : state["question_index"],
            "current_question": state["current_question"],
            "silence_count"   : 0,
            "last_response"   : clean_reaction,
            "messages"        : [AIMessage(content=clean_reaction)],
        }

    # Good answer — advance to next phase
    next_phase = get_next_phase(phase)
    if next_phase:
        next_q   = state["questions"][next_phase][0]
        response = (
            f"{clean_reaction}\n\n"
            f"Let's move on to the {next_phase} round.\n\n{next_q}"
        )
        return {
            "phase"           : next_phase,
            "question_index"  : 0,
            "current_question": next_q,
            "silence_count"   : 0,
            "last_response"   : response,
            "messages"        : [AIMessage(content=response)],
        }

    # All rounds done
    response = (
        f"{clean_reaction}\n\n"
        f"That wraps up the main interview questions. "
        f"Do you have any questions for me about the role or the company?"
    )
    return {
        "phase"           : "candidate_questions",
        "question_index"  : 0,
        "current_question": "Do you have any questions?",
        "silence_count"   : 0,
        "last_response"   : response,
        "messages"        : [AIMessage(content=response)],
    }


def candidate_questions_handler(state: InterviewState):
    user_input = state["last_user_input"].strip().lower()

    no_phrases = [
        "no", "nope", "none", "nothing", "no thank", "no thanks",
        "i'm good", "im good", "all good", "not really", "that's all",
        "thats all", "i'm fine", "im fine", "no more",
    ]
    if any(phrase in user_input for phrase in no_phrases):
        # Run evaluation silently — don't reveal scores to candidate
        all_messages = state["messages"] + [HumanMessage(content=state["last_user_input"])]
        try:
            from backend.services.evaluation import evaluate_interview
            role        = state.get("role", "the applied role")
            eval_result = evaluate_interview(all_messages, role=role)
            scores      = eval_result.model_dump()
        except Exception as e:
            print(f"⚠️  Evaluation failed: {e}")
            scores = {}

        closing = (
            "It was great speaking with you today! "
            "Thank you so much for your time. We'll be in touch soon. "
            "Have a wonderful day! 😊"
        )
        return {
            "phase"        : "done",
            "scores"       : scores,
            "last_response": closing,
            "messages"     : [AIMessage(content=closing)],
        }

    # Answer the candidate's question using RAG
    from backend.services.rag import rag_pipeline
    answer   = rag_pipeline(state["last_user_input"])
    response = f"{answer}\n\nDo you have any other questions?"
    return {
        "last_response": response,
        "messages"     : [AIMessage(content=response)],
    }



# -------------------
# 5. Routers
# -------------------
def entry_router(state: InterviewState) -> Literal["ask_question", "input_router_node"]:
    if not state.get("last_user_input", "").strip():
        return "ask_question"
    return "input_router_node"


def input_router(state: InterviewState) -> Literal["silence", "company", "repeat", "normal", "candidate_questions"]:
    if state.get("phase") == "candidate_questions":
        return "candidate_questions"

    user_input = state["last_user_input"].strip().lower()

    if not user_input:
        return "silence"

    if any(kw in user_input for kw in ["repeat", "again", "pardon", "rephrase", "say that again"]):
        return "repeat"

    # only trigger company RAG when the candidate is ASKING about the company —
    # not when their answer merely contains common words like "team" or "office"
    is_question = (
        user_input.endswith("?") or
        any(user_input.startswith(w) for w in ["what ", "how ", "does ", "is ", "are ", "do ", "can you ", "tell me about nexara", "who "])
    )
    company_kws = ["nexara", "company policy", "company culture", "company benefit",
                   "company salary", "work from home", "office location", "about the company"]
    is_company_question = is_question and any(kw in user_input for kw in company_kws)

    if is_company_question:
        return "company"

    return "normal"


# -------------------
# 6. Graph
# -------------------
interview_checkpointer = MemorySaver()

builder = StateGraph(InterviewState)

builder.add_node("ask_question",               ask_question)
builder.add_node("input_router_node",          input_router_node)
builder.add_node("silence_handler",            silence_handler)
builder.add_node("company_rag_answer",         company_rag_answer)
builder.add_node("repeat_question",            repeat_question)
builder.add_node("normal_interview_flow",      normal_interview_flow)
builder.add_node("candidate_questions_handler",candidate_questions_handler)

builder.add_conditional_edges(
    START,
    entry_router,
    {
        "ask_question"      : "ask_question",
        "input_router_node" : "input_router_node",
    },
)

builder.add_conditional_edges(
    "input_router_node",
    input_router,
    {
        "silence"            : "silence_handler",
        "company"            : "company_rag_answer",
        "repeat"             : "repeat_question",
        "normal"             : "normal_interview_flow",
        "candidate_questions": "candidate_questions_handler",
    },
)

builder.add_edge("ask_question",               END)
builder.add_edge("silence_handler",            END)
builder.add_edge("company_rag_answer",         END)
builder.add_edge("repeat_question",            END)
builder.add_edge("normal_interview_flow",      END)
builder.add_edge("candidate_questions_handler",END)

interview_app = builder.compile(checkpointer=interview_checkpointer)
