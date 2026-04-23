from fastapi import APIRouter
from langchain_core.messages import HumanMessage

from backend.graph.chat_graph import chat_app
from backend.models.schemas import ChatRequest, ChatResponse


router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    config   = {"configurable": {"thread_id": req.session_id}}
    snapshot = chat_app.get_state(config)
    current  = snapshot.values if snapshot.values else {}

    initial_state = {
        "messages"        : [HumanMessage(content=req.message)],
        "mode"            : current.get("mode", "normal"),
        "hr_authenticated": current.get("hr_authenticated", False),
        "hr_data"         : current.get("hr_data", {"step": "menu"}),
        "last_response"   : "",
    }

    result = chat_app.invoke(initial_state, config=config)

    return ChatResponse(
        response=result["last_response"],
        mode=result["mode"],
    )
