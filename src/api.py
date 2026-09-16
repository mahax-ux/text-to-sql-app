import uuid
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.state import (
    EngineSessionState,
    UserClarificationResponse,
    ExecutionStatus,
)
from src.detector import AmbiguityDetector
from src.sql_compiler import SQLCompiler
from src.db import DatabaseManager

app = FastAPI(title="Text-to-SQL Clarification Engine API")

# Broad CORS configuration to handle dynamic local ports (5173, 5174, etc.)
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize engines
detector = AmbiguityDetector()
compiler = SQLCompiler()
db = DatabaseManager()

# In-memory session store
session_store = {}


class InitialQueryRequest(BaseModel):
    raw_query: str


class ClarificationRequest(BaseModel):
    session_id: str
    raw_query: str
    resolved_clarifications: List[UserClarificationResponse]


@app.post("/api/query", response_model=EngineSessionState)
def handle_initial_query(req: InitialQueryRequest):
    session_id = f"sess_{uuid.uuid4().hex[:8]}"
    state = EngineSessionState(
        session_id=session_id,
        raw_query=req.raw_query,
    )

    # Detect ambiguities via LLM + Glossary
    analyzed_state = detector.analyze(state)
    session_store[session_id] = analyzed_state
    return analyzed_state


@app.post("/api/clarify-and-compile", response_model=EngineSessionState)
def handle_clarification_and_compile(req: ClarificationRequest):
    # Retrieve existing state or initialize fallback
    state = session_store.get(req.session_id)
    if not state:
        state = EngineSessionState(
            session_id=req.session_id,
            raw_query=req.raw_query,
        )

    # Attach selected user choices
    state.resolved_clarifications = req.resolved_clarifications
    state.status = ExecutionStatus.READY_TO_GENERATE

    # Compile and execute query
    compiled_state = compiler.compile_and_execute(state)

    if compiled_state.status == ExecutionStatus.FAILED:
        raise HTTPException(
            status_code=500,
            detail="Failed to compile or execute SQL statement."
        )

    session_store[req.session_id] = compiled_state
    return compiled_state


@app.get("/health")
def health():
    return {"status": "operational"}