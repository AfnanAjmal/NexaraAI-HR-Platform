from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from langchain_core.messages import HumanMessage
from pydantic import BaseModel

from backend.graph.interview_graph import interview_app
from backend.database.mongo import candidates_col
from backend.models.schemas import (
    InterviewStartRequest,
    InterviewRespondRequest,
    InterviewRespondResponse,
)
import base64

from backend.config import SCORE_THRESHOLD, DEEPGRAM_API_KEY


router = APIRouter()


# -------------------
# 1. Config (must be ABOVE /interview/{token} — FastAPI matches routes in order)
# -------------------
@router.get("/interview/config")
async def interview_config(token: str):
    candidate = await candidates_col.find_one({"token": token}, {"_id": 0})
    if not candidate:
        raise HTTPException(status_code=404, detail="Invalid token")
    return {"deepgram_key": DEEPGRAM_API_KEY}


# -------------------
# 2. Interview page
# -------------------
@router.get("/interview/{token}", response_class=HTMLResponse)
async def interview_page(token: str):
    candidate = await candidates_col.find_one({"token": token}, {"_id": 0})
    if not candidate:
        raise HTTPException(status_code=404, detail="Invalid interview link")
    if candidate["status"] not in ("pending",):
        return HTMLResponse(
            "<h2 style='font-family:sans-serif;text-align:center;margin-top:20vh'>"
            "This interview has already been completed. Thank you!</h2>"
        )

    from backend.config import CONTACT_EMAIL
    with open("frontend/interview.html", encoding="utf-8") as f:
        html = (
            f.read()
             .replace("{{TOKEN}}",         token)
             .replace("{{NAME}}",          candidate["name"])
             .replace("{{ROLE}}",          candidate.get("jd_info", {}).get("role", "the applied role"))
             .replace("{{CONTACT_EMAIL}}", CONTACT_EMAIL)
        )
    return HTMLResponse(html)


# -------------------
# 2. Start interview
# -------------------
@router.post("/interview/start")
async def start_interview(req: InterviewStartRequest):
    candidate = await candidates_col.find_one({"token": req.token}, {"_id": 0})
    if not candidate:
        raise HTTPException(status_code=404, detail="Invalid token")

    config   = {"configurable": {"thread_id": req.token}}
    snapshot = interview_app.get_state(config)

    if snapshot.values:
        return {
            "response" : snapshot.values.get("last_response", ""),
            "phase"    : snapshot.values.get("phase", "intro"),
            "completed": snapshot.values.get("phase") == "done",
        }

    initial_state = {
        "candidate_id"    : candidate["id"],
        "role"            : candidate.get("jd_info", {}).get("role", "the applied role"),
        "phase"           : "intro",
        "question_index"  : 0,
        "questions"       : candidate["interview_plan"],
        "current_question": "",
        "last_user_input" : "",
        "messages"        : [],
        "silence_count"   : 0,
        "scores"          : {},
        "last_response"   : "",
    }

    result = interview_app.invoke(initial_state, config=config)

    return {
        "response" : result["last_response"],
        "phase"    : result["phase"],
        "completed": result["phase"] == "done",
    }


# -------------------
# 3. Respond to interview
# -------------------
@router.post("/interview/respond", response_model=InterviewRespondResponse)
async def respond_to_interview(req: InterviewRespondRequest):
    candidate = await candidates_col.find_one({"token": req.token}, {"_id": 0})
    if not candidate:
        raise HTTPException(status_code=404, detail="Invalid token")

    config = {"configurable": {"thread_id": req.token}}

    result = interview_app.invoke(
        {
            "last_user_input": req.message,
            "messages"       : [HumanMessage(content=req.message)],
        },
        config=config,
    )

    completed = result["phase"] == "done"

    if completed and result.get("scores"):
        score  = result["scores"].get("overall", 0)
        status = "selected" if score >= SCORE_THRESHOLD else "rejected"
        await candidates_col.update_one(
            {"token": req.token},
            {"$set": {
                "status"    : status,
                "score"     : score,
                "evaluation": result["scores"],
            }},
        )

        if status == "selected":
            from backend.services.email_service import send_offer_letter
            role = candidate.get("jd_info", {}).get("role", "the applied role")
            send_offer_letter(
                candidate_email=candidate["email"],
                candidate_name =candidate["name"],
                role           =role,
            )

    return InterviewRespondResponse(
        response =result["last_response"],
        phase    =result["phase"],
        completed=completed,
        scores   =result.get("scores") or None,
    )


# -------------------
# 4. Speak — text → mp3 audio stream (ElevenLabs, no LangGraph)
# -------------------
class SpeakRequest(BaseModel):
    token : str
    text  : str

@router.post("/interview/speak")
async def speak(req: SpeakRequest):
    candidate = await candidates_col.find_one({"token": req.token}, {"_id": 0})
    if not candidate:
        raise HTTPException(status_code=404, detail="Invalid token")

    from backend.services.elevenlabs_service import text_to_audio

    audio_bytes  = await text_to_audio(req.text)
    audio_base64 = base64.b64encode(audio_bytes).decode()
    return {"audio_base64": audio_base64}


# -------------------
# 5. Answer — STT text → LangGraph → ElevenLabs → base64 audio JSON
# -------------------
class AnswerRequest(BaseModel):
    token   : str
    message : str

@router.post("/interview/answer")
async def answer(req: AnswerRequest):
    candidate = await candidates_col.find_one({"token": req.token}, {"_id": 0})
    if not candidate:
        raise HTTPException(status_code=404, detail="Invalid token")

    config = {"configurable": {"thread_id": req.token}}

    result = interview_app.invoke(
        {
            "last_user_input": req.message,
            "messages"       : [HumanMessage(content=req.message)],
        },
        config=config,
    )

    response_text = result["last_response"]
    completed     = result["phase"] == "done"

    if completed and result.get("scores"):
        score  = result["scores"].get("overall", 0)
        status = "selected" if score >= SCORE_THRESHOLD else "rejected"
        await candidates_col.update_one(
            {"token": req.token},
            {"$set": {
                "status"    : status,
                "score"     : score,
                "evaluation": result["scores"],
            }},
        )
        role = candidate.get("jd_info", {}).get("role", "the applied role")
        if status == "selected":
            from backend.services.email_service import send_offer_letter
            send_offer_letter(
                candidate_email=candidate["email"],
                candidate_name =candidate["name"],
                role           =role,
            )
        else:
            from backend.services.email_service import send_rejection_email
            send_rejection_email(
                candidate_email=candidate["email"],
                candidate_name =candidate["name"],
                role           =role,
            )

    from backend.services.elevenlabs_service import text_to_audio

    audio_bytes  = await text_to_audio(response_text)
    audio_base64 = base64.b64encode(audio_bytes).decode()

    return {
        "response_text": response_text,
        "audio_base64" : audio_base64,
        "phase"        : result["phase"],
        "completed"    : completed,
    }
