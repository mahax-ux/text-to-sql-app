import os
from typing import List, Optional, Dict, Any, Union
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from src.state import EngineSessionState, UserClarificationResponse, ExecutionStatus
from src.detector import AmbiguityDetector
from src.sql_compiler import SQLCompiler

app = FastAPI(title="Text-to-SQL Clarification Engine API")

# Enable CORS for local Vite dev and Vercel production domains
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

detector = AmbiguityDetector()
compiler = SQLCompiler()

# --- Pydantic Request Models ---

class QueryRequest(BaseModel):
    # Accepts query, raw_query, or text to avoid payload mismatch
    query: Optional[str] = None
    raw_query: Optional[str] = None
    text: Optional[str] = None

class ClarificationSubmitRequest(BaseModel):
    session_id: Optional[str] = "sess_default"
    query: Optional[str] = None
    raw_query: Optional[str] = None
    resolved_clarifications: List[Dict[str, Any]] = Field(default_factory=list)


# --- Endpoints ---

@app.get("/")
def root():
    return {"status": "ok", "service": "Text-to-SQL Engine Running"}


# Handles: /api/query and /api/query/
@app.post("/api/query")
@app.post("/api/query/")
def analyze_query(payload: QueryRequest):
    # Extract the user input from any of the allowed keys
    prompt = payload.raw_query or payload.query or payload.text
    if not prompt or not prompt.strip():
        raise HTTPException(
            status_code=400,
            detail="No query string found. Please provide 'query' or 'raw_query'."
        )

    session_state = EngineSessionState(
        session_id="web_session_1",
        raw_query=prompt.strip()
    )
    
    session_state = detector.analyze(session_state)
    return session_state.model_dump()


# Handles both route variations and the short alias, with & without trailing slashes
@app.post("/api/clarify-and-compile")
@app.post("/api/clarify-and-compile/")
@app.post("/api/compile")
@app.post("/api/compile/")
def clarify_and_compile(payload: ClarificationSubmitRequest):
    prompt = payload.raw_query or payload.query
    if not prompt:
        raise HTTPException(
            status_code=400,
            detail="Missing 'raw_query' or 'query' in compilation request."
        )

    session_state = EngineSessionState(
        session_id=payload.session_id or "web_session_1",
        raw_query=prompt
    )
    
    # Map user resolutions safely
    session_state.resolved_clarifications = [
        UserClarificationResponse(
            term=item.get("term", ""),
            selected_option_id=item.get("selected_option_id", "")
        )
        for item in payload.resolved_clarifications
        if isinstance(item, dict) and "term" in item and "selected_option_id" in item
    ]
    
    session_state = compiler.compile_and_execute(session_state)
    return session_state.model_dump()