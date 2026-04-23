from typing import TypedDict, Optional, List, Dict, Annotated, Literal

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


# -------------------
# 1. Chat state
# -------------------
class HRData(TypedDict, total=False):
    step        : str
    email       : Optional[str]
    jd_text     : Optional[str]
    resume_text : Optional[str]
    candidate_id: Optional[str]


class ChatbotState(TypedDict):
    messages         : Annotated[list[BaseMessage], add_messages]
    mode             : Literal["normal", "hr"]
    hr_authenticated : bool
    hr_data          : HRData
    last_response    : str


# -------------------
# 2. Interview state
# -------------------
class InterviewState(TypedDict):
    candidate_id    : str
    role            : str
    phase           : Literal["intro", "technical", "behavioral", "done"]
    question_index  : int
    questions       : Dict[str, List[str]]
    current_question: str
    last_user_input : str
    messages        : Annotated[list[BaseMessage], add_messages]
    silence_count   : int
    scores          : Dict
    last_response   : str
