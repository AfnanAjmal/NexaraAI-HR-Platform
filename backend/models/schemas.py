from typing import Optional, List, Dict, Literal
from pydantic import BaseModel, Field


# -------------------
# 1. Chat
# -------------------
class ChatRequest(BaseModel):
    session_id : str
    message    : str

class ChatResponse(BaseModel):
    response   : str
    mode       : str


# -------------------
# 2. HR
# -------------------
class ProcessCandidateResponse(BaseModel):
    candidate_id   : str
    name           : str
    interview_link : str
    status         : str

class CandidateCard(BaseModel):
    id    : str
    name  : str
    email : str
    status: str
    score : Optional[float] = None
    token : Optional[str]   = None

class PipelineResponse(BaseModel):
    pending     : List[CandidateCard] = []
    interviewed : List[CandidateCard] = []
    selected    : List[CandidateCard] = []
    rejected    : List[CandidateCard] = []


# -------------------
# 3. Interview
# -------------------
class InterviewStartRequest(BaseModel):
    token : str

class InterviewRespondRequest(BaseModel):
    token   : str
    message : str

class InterviewRespondResponse(BaseModel):
    response  : str
    phase     : str
    completed : bool
    scores    : Optional[Dict] = None


# -------------------
# 4. LLM structured outputs
# -------------------
class ResumeInfo(BaseModel):
    name      : str       = Field(description="Full name of the candidate")
    email     : str       = Field(description="Email address")
    education : str       = Field(description="Education background summary")
    skills    : List[str] = Field(description="List of technical and soft skills")
    experience: str       = Field(description="Work experience summary")

class JDInfo(BaseModel):
    role             : str       = Field(description="Job role or title")
    required_skills  : List[str] = Field(description="List of required skills")
    experience_level : str       = Field(description="Required experience level (e.g. junior, senior)")

class InterviewPlan(BaseModel):
    intro      : List[str] = Field(description="1 warm-up / introduction question")
    technical  : List[str] = Field(description="1 technical question based on role and skills")
    behavioral : List[str] = Field(description="1 behavioral / situational question")

class EvaluationResult(BaseModel):
    technical_score : float = Field(ge=0, le=10, description="Technical knowledge score out of 10")
    communication   : float = Field(ge=0, le=10, description="Communication skills score out of 10")
    confidence      : float = Field(ge=0, le=10, description="Confidence and clarity score out of 10")
    overall         : float = Field(ge=0, le=10, description="Overall performance score out of 10")
    summary         : str   = Field(description="Detailed evaluation summary paragraph")
