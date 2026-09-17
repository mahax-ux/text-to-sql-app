import os
import sys
import uuid
import traceback
from typing import Dict, Any, List
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

try:
    from src.state import (
        EngineSessionState,
        UserClarificationResponse,
        ExecutionStatus,
    )
    from src.detector import AmbiguityDetector
    from src.sql_compiler import SQLCompiler
except Exception as e:
    print("Import Error during startup:")
    traceback.print_exc()
    sys.exit(1)

app = FastAPI(title="Text-to-SQL Clarification Engine API")

# Explicit CORS settings for production & local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://text-to-sql-app.vercel.app",
        "http://localhost:5173",
        "http://localhost:3000",
        "*",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS", "PUT", "DELETE"],
    allow_headers=["*"],
    expose_headers=["*"],
)

sessions: Dict[str, EngineSessionState] = {}
detector = AmbiguityDetector()
compiler = SQLCompiler()


@app.options("/{full_path:path}")
async def options_preflight_handler(full_path: str):
    """Explicit preflight handler to prevent proxy CORS drops."""
    response = Response(status_code=200)
    response.headers["Access-Control-Allow-Origin"] = "https://text-to-sql-app.vercel.app"
    response.headers["Access-Control-Allow-Methods"] = "POST, GET, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"
    return response


@app.get("/")
def root():
    return {"status": "healthy", "service": "text-to-sql-engine"}


@app.post("/api/query")
async def submit_query(request: Request):
    try:
        data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body received.")

    raw_text = (
        data.get("query")
        or data.get("user_query")
        or data.get("question")
        or data.get("prompt")
        or data.get("text")
        or data.get("sql_query")
        or ""
    )

    if isinstance(raw_text, str):
        raw_text = raw_text.strip()

    if not raw_text:
        raise HTTPException(
            status_code=400,
            detail=f"No query string found. Received payload keys: {list(data.keys())}",
        )

    session_id = data.get("session_id") or str(uuid.uuid4())

    try:
        session_state = EngineSessionState(
            session_id=session_id,
            raw_query=raw_text,
        )

        session_state = detector.analyze(session_state)
        sessions[session_id] = session_state

        if session_state.status == ExecutionStatus.READY_TO_GENERATE:
            session_state = compiler.compile_and_execute(session_state)
            sessions[session_id] = session_state

        return session_state.model_dump()

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Engine processing error: {str(e)}")


@app.post("/api/clarify")
async def clarify_query(request: Request):
    try:
        data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body received.")

    session_id = data.get("session_id")
    if not session_id or session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session expired or not found.")

    raw_answers = data.get("answers", [])
    resolved_responses: List[UserClarificationResponse] = []

    for item in raw_answers:
        if isinstance(item, dict):
            term = item.get("term", "")
            option_id = item.get("selected_option_id") or item.get("option_id") or item.get("id") or ""
            if option_id:
                resolved_responses.append(
                    UserClarificationResponse(
                        term=term,
                        selected_option_id=option_id,
                    )
                )

    try:
        session_state = sessions[session_id]
        session_state.resolved_clarifications = resolved_responses

        session_state = compiler.compile_and_execute(session_state)
        sessions[session_id] = session_state

        return session_state.model_dump()

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Compilation error: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)