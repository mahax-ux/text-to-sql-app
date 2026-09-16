import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

from src.state import EngineSessionState, UserClarificationResponse, ExecutionStatus
from src.detector import AmbiguityDetector
from src.sql_compiler import SQLCompiler

app = FastAPI(title="Text-to-SQL Clarification Engine API")

# Enable CORS for local React/JSX development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

detector = AmbiguityDetector()
compiler = SQLCompiler()

class QueryRequest(BaseModel):
    raw_query: str

class ClarificationSubmitRequest(BaseModel):
    session_id: str
    raw_query: str
    resolved_clarifications: List[Dict[str, str]]

@app.post("/api/query")
def analyze_query(payload: QueryRequest):
    session_state = EngineSessionState(
        session_id="web_sess_1",
        raw_query=payload.raw_query
    )
    session_state = detector.analyze(session_state)
    return session_state.model_dump()

@app.post("/api/clarify-and-compile")
def clarify_and_compile(payload: ClarificationSubmitRequest):
    session_state = EngineSessionState(
        session_id=payload.session_id,
        raw_query=payload.raw_query
    )
    
    session_state.resolved_clarifications = [
        UserClarificationResponse(term=item["term"], selected_option_id=item["selected_option_id"])
        for item in payload.resolved_clarifications
    ]
    
    session_state = compiler.compile_and_execute(session_state)
    return session_state.model_dump()