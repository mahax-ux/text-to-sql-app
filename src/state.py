from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class AmbiguityType(str, Enum):
    METRIC = "METRIC_AMBIGUITY"
    RANKING = "RANKING_AMBIGUITY"
    TEMPORAL = "TEMPORAL_AMBIGUITY"
    FILTER_SCOPE = "FILTER_SCOPE_AMBIGUITY"
    ENTITY = "ENTITY_AMBIGUITY"


class ClarificationOption(BaseModel):
    id: str
    label: str
    sql_snippet: Optional[str] = None


class ClarificationQuestion(BaseModel):
    ambiguity_type: AmbiguityType
    term: str
    question: str
    options: List[ClarificationOption]


class UserClarificationResponse(BaseModel):
    term: str
    selected_option_id: str


class ExecutionStatus(str, Enum):
    IDLE = "IDLE"
    NEEDS_CLARIFICATION = "NEEDS_CLARIFICATION"
    READY_TO_GENERATE = "READY_TO_GENERATE"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


class EngineSessionState(BaseModel):
    session_id: str
    raw_query: str
    turn_count: int = 1
    detected_ambiguities: List[ClarificationQuestion] = Field(default_factory=list)
    resolved_clarifications: List[UserClarificationResponse] = Field(default_factory=list)
    generated_sql: Optional[str] = None
    query_results: Optional[List[Dict[str, Any]]] = None
    status: ExecutionStatus = ExecutionStatus.IDLE