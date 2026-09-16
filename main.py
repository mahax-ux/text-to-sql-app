import os
import sys
import uuid
import traceback
from typing import Dict, List, Optional, Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, model_validator

try:
    from src.state import (
        EngineSessionState,
        UserClarificationResponse,
        ExecutionStatus,
        ClarificationQuestion,
    )
    from src.detector import AmbiguityDetector
    from src.sql_compiler import SQLCompiler
except Exception as e:
    print("Import Error during startup:")
    traceback.print_exc()
    sys.exit(1)

app = FastAPI(title="Text-to-SQL Clarification Engine API")

# Enable CORS for local dev and deployed frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory session cache
sessions: Dict[str, EngineSessionState] = {}

# Initialize engine components
detector = AmbiguityDetector()
compiler = SQLCompiler()


# Request / Response Schemas
class QueryRequest(BaseModel):
    query: Optional[str] = None
    user_query: Optional[str] = None
    question: Optional[str] = None
    prompt: Optional[str] = None
    text: Optional[str] = None

    @model_validator(mode="after")
    def resolve_query_field(self):
        chosen = self.query or self.user_query or self.question or self.prompt or self.text
        if not chosen:
            raise ValueError("A query string must be provided (accepted keys: query, user_query, question, prompt, text).")
        self.query = chosen.strip()
        return self


class ClarificationAnswer(BaseModel):
    term: Optional[str] = None
    ambiguity_type: Optional[str] = None
    selected_option_id: Optional[str] = None
    option_id: Optional[str] = None

    @model_validator(mode="after")
    def resolve_ids(self):
        chosen_id = self.selected_option_id or self.option_id
        if not chosen_id:
            raise ValueError("An option ID must be provided.")
        self.selected_option_id = chosen_id
        if not self.term:
            self.term = ""
        return self


class ClarifyRequest(BaseModel):
    session_id: str
    answers: List[ClarificationAnswer]


@app.get("/")
def health_check():
    return {"status": "healthy", "service": "text-to-sql-engine"}


@app.post("/api/query")
def submit_query(req: QueryRequest):
    """Initial query entry point: analyzes prompt for ambiguities."""
    try:
        session_id = str(uuid.uuid4())
        session_state = EngineSessionState(
            session_id=session_id,
            raw_query=req.query
        )

        session_state = detector.analyze(session_state)
        sessions[session_id] = session_state

        # If no ambiguities, compile and execute immediately
        if session_state.status == ExecutionStatus.READY_TO_GENERATE:
            session_state = compiler.compile_and_execute(session_state)
            sessions[session_id] = session_state

        return session_state.model_dump()

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/clarify")
def clarify_query(req: ClarifyRequest):
    """Resolves selected options and generates the final SQL."""
    session_state = sessions.get(req.session_id)
    if not session_state:
        raise HTTPException(status_code=404, detail="Session not found.")

    try:
        session_state.resolved_clarifications = [
            UserClarificationResponse(
                term=ans.term,
                selected_option_id=ans.selected_option_id
            )
            for ans in req.answers
        ]

        session_state = compiler.compile_and_execute(session_state)
        sessions[req.session_id] = session_state

        return session_state.model_dump()

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)