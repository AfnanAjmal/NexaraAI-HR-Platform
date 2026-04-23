import uuid
import threading
from datetime import datetime
from typing import Literal

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from backend.graph.state import ChatbotState
from backend.config import HR_PASSCODE, MONGODB_URI, DB_NAME, BASE_URL


# -------------------
# 1. Helpers
# -------------------
def get_hr_menu() -> str:
    return (
        "🔐 HR DASHBOARD\n\n"
        "1. New Candidate\n"
        "2. Candidates Pipeline\n\n"
        "Type 'exit' to leave HR mode."
    )


def _process_candidate_bg(hr_data: dict) -> None:
    """Runs in a background thread — extracts info, saves to DB, sends email."""
    try:
        from backend.services.extraction import extract_resume, extract_jd
        from backend.services.interview_plan import generate_interview_plan
        from backend.services.email_service import send_interview_email
        from backend.services.token_service import generate_token
        import pymongo

        resume_info = extract_resume(hr_data["resume_text"])
        jd_info     = extract_jd(hr_data["jd_text"])
        plan        = generate_interview_plan(resume_info.model_dump(), jd_info.model_dump())

        candidate_id = str(uuid.uuid4())
        token        = generate_token(candidate_id)

        # sync pymongo insert (motor is async — can't use inside sync thread easily)
        client = pymongo.MongoClient(MONGODB_URI)
        client[DB_NAME]["candidates"].insert_one({
            "id"            : candidate_id,
            "name"          : resume_info.name,
            "email"         : hr_data.get("email", ""),
            "resume_text"   : hr_data["resume_text"],
            "jd_text"       : hr_data["jd_text"],
            "resume_info"   : resume_info.model_dump(),
            "jd_info"       : jd_info.model_dump(),
            "interview_plan": plan.model_dump(),
            "token"         : token,
            "status"        : "pending",
            "score"         : None,
            "created_at"    : datetime.utcnow(),
        })
        client.close()

        send_interview_email(
            candidate_email=hr_data.get("email", ""),
            candidate_name=resume_info.name,
            role=jd_info.role,
            token=token,
        )
        print(f"✅ Candidate processed: {resume_info.name} | link: {BASE_URL}/interview/{token}")

    except Exception as e:
        print(f"❌ Background processing failed: {e}")


# -------------------
# 2. Nodes
# -------------------
def mode_selection(state: ChatbotState):
    message      = state["messages"][-1].content.strip()
    current_mode = state["mode"]

    if message == f"#hr:{HR_PASSCODE}":
        return {
            "mode"            : "hr",
            "hr_authenticated": True,
            "hr_data"         : {"step": "menu"},
            "last_response"   : get_hr_menu(),
        }

    if current_mode == "hr" and state.get("hr_authenticated"):
        if message.lower() == "exit":
            return {
                "mode"            : "normal",
                "hr_authenticated": False,
                "hr_data"         : {"step": "menu"},
                "last_response"   : "✅ Exited HR mode. Back to normal assistant.",
            }
        return {"mode": "hr"}

    return {"mode": "normal"}


def normal_rag_answer(state: ChatbotState):
    from backend.services.rag import rag_pipeline
    query  = state["messages"][-1].content
    answer = rag_pipeline(query)
    return {"last_response": answer}


def hr_handler(state: ChatbotState):
    message = state["messages"][-1].content.strip()
    hr_data = dict(state.get("hr_data") or {})
    step    = hr_data.get("step", "menu")

    # after processing is triggered, any message resets to menu
    if step == "processing":
        fresh = {"step": "menu"}
        return {"hr_data": fresh, "last_response": get_hr_menu()}

    if step == "menu":
        if message == "1":
            # clear stale candidate data so each new candidate starts fresh
            fresh_data = {"step": "collect_email"}
            return {"hr_data": fresh_data, "last_response": "📋 New Candidate\n\nEnter candidate email:"}
        if message == "2":
            return {
                "hr_data"      : hr_data,
                "last_response": "📊 Candidates Pipeline\n\nVisit: /hr/dashboard or GET /candidates",
            }
        return {"hr_data": hr_data, "last_response": get_hr_menu()}

    if step == "collect_email":
        hr_data["email"] = message
        hr_data["step"]  = "collect_jd"
        return {"hr_data": hr_data, "last_response": "✅ Email saved!\n\nNow paste the Job Description:"}

    if step == "collect_jd":
        hr_data["jd_text"] = message
        hr_data["step"]    = "collect_resume"
        return {"hr_data": hr_data, "last_response": "✅ JD saved!\n\nNow paste the candidate Resume:"}

    if step == "collect_resume":
        hr_data["resume_text"] = message
        hr_data["step"]        = "processing"

        # fire-and-forget: extract, save to DB, send email
        t = threading.Thread(target=_process_candidate_bg, args=(hr_data.copy(),), daemon=True)
        t.start()

        return {
            "hr_data"      : hr_data,
            "last_response": (
                "✅ All documents collected!\n\n"
                "⏳ Processing candidate...\n"
                "This takes ~30 seconds. The interview link will be emailed shortly.\n\n"
                "Send any message to return to the menu."
            ),
        }

    return {"hr_data": hr_data, "last_response": get_hr_menu()}


# -------------------
# 3. Router
# -------------------
def mode_router(state: ChatbotState) -> Literal["normal", "hr"]:
    return state["mode"]


# -------------------
# 4. Graph
# -------------------
checkpointer = MemorySaver()

builder = StateGraph(ChatbotState)

builder.add_node("mode_selection",    mode_selection)
builder.add_node("normal_rag_answer", normal_rag_answer)
builder.add_node("hr_handler",        hr_handler)

builder.add_edge(START, "mode_selection")

builder.add_conditional_edges(
    "mode_selection",
    mode_router,
    {
        "normal": "normal_rag_answer",
        "hr"    : "hr_handler",
    },
)

builder.add_edge("normal_rag_answer", END)
builder.add_edge("hr_handler",        END)

chat_app = builder.compile(checkpointer=checkpointer)
