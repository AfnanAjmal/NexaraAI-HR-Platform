import uuid
from datetime import datetime

from fastapi import APIRouter, UploadFile, File, Form, HTTPException

from backend.database.mongo import candidates_col
from backend.models.schemas import ProcessCandidateResponse, PipelineResponse, CandidateCard
from backend.services.extraction import extract_resume, extract_jd, extract_text_from_pdf
from backend.services.interview_plan import generate_interview_plan
from backend.services.email_service import send_interview_email
from backend.services.token_service import generate_token
from backend.config import BASE_URL


router = APIRouter(prefix="/hr")


# -------------------
# 1. New candidate
# -------------------
@router.post("/new-candidate", response_model=ProcessCandidateResponse)
async def new_candidate(
    resume : UploadFile = File(...),
    jd_text: str        = Form(...),
    email  : str        = Form(...),
):
    resume_bytes = await resume.read()
    resume_text  = extract_text_from_pdf(resume_bytes)

    resume_info = extract_resume(resume_text)
    jd_info     = extract_jd(jd_text)
    plan        = generate_interview_plan(resume_info.model_dump(), jd_info.model_dump())

    candidate_id   = str(uuid.uuid4())
    token          = generate_token(candidate_id)
    interview_link = f"{BASE_URL}/interview/{token}"

    candidate_doc = {
        "id"            : candidate_id,
        "name"          : resume_info.name,
        "email"         : resume_info.email or email,
        "resume_text"   : resume_text,
        "jd_text"       : jd_text,
        "resume_info"   : resume_info.model_dump(),
        "jd_info"       : jd_info.model_dump(),
        "interview_plan": plan.model_dump(),
        "token"         : token,
        "status"        : "pending",
        "score"         : None,
        "created_at"    : datetime.utcnow(),
    }

    await candidates_col.insert_one(candidate_doc)

    send_interview_email(
        candidate_email=candidate_doc["email"],
        candidate_name=resume_info.name,
        role=jd_info.role,
        token=token,
    )

    return ProcessCandidateResponse(
        candidate_id=candidate_id,
        name=resume_info.name,
        interview_link=interview_link,
        status="pending",
    )


# -------------------
# 2. Candidates pipeline
# -------------------
@router.get("/candidates", response_model=PipelineResponse)
async def get_candidates():
    pipeline = [
        {"$group": {
            "_id"       : "$status",
            "candidates": {"$push": {
                "id"    : "$id",
                "name"  : "$name",
                "email" : "$email",
                "status": "$status",
                "score" : "$score",
                "token" : "$token",
            }},
        }},
    ]

    groups = {"pending": [], "interviewed": [], "selected": [], "rejected": []}

    async for group in candidates_col.aggregate(pipeline):
        status = group["_id"]
        if status in groups:
            groups[status] = [CandidateCard(**c) for c in group["candidates"]]

    return PipelineResponse(**groups)


# -------------------
# 3. Candidate detail
# -------------------
@router.get("/candidate/{candidate_id}")
async def get_candidate(candidate_id: str):
    doc = await candidates_col.find_one({"id": candidate_id}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return doc
