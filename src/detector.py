import os
import json
import yaml
from pathlib import Path
from typing import List, Dict, Any
from openai import OpenAI
from dotenv import load_dotenv

from src.state import EngineSessionState, ClarificationQuestion, AmbiguityType, ClarificationOption, ExecutionStatus
from src.db import DatabaseManager

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL", "https://api.groq.com/openai/v1")
)

GROQ_MODEL = "openai/gpt-oss-20b"
GLOSSARY_PATH = Path(__file__).resolve().parent.parent / "config" / "glossary.yaml"


class AmbiguityDetector:
    def __init__(self):
        with open(GLOSSARY_PATH, "r") as f:
            self.glossary = yaml.safe_load(f).get("terms", {})
        db_manager = DatabaseManager()
        self.schema_summary = db_manager.get_schema_summary()

    def analyze(self, state: EngineSessionState) -> EngineSessionState:
        system_prompt = f"""
You are an expert Text-to-SQL Ambiguity Detection Engine. Your job is to analyze user queries against a database schema and business glossary to detect if the query is ambiguous, underspecified, or contains terms with multiple valid interpretations.

DATABASE SCHEMA:
{self.schema_summary}

BUSINESS GLOSSARY & AMBIGUITIES:
{json.dumps(self.glossary, indent=2)}

INSTRUCTIONS:
1. Analyze the user's natural language query.
2. Check if the query relies on vague terms from the glossary or lacks necessary constraints.
3. If ambiguities are found, output a JSON response containing a list of detected ambiguities with options for clarification.
4. If the query is completely clear and unambiguous, return an empty list of ambiguities.

OUTPUT FORMAT (JSON ONLY):
{{
  "has_ambiguities": true/false,
  "ambiguities": [
    {{
      "ambiguity_type": "METRIC_AMBIGUITY" | "RANKING_AMBIGUITY" | "TEMPORAL_AMBIGUITY" | "FILTER_SCOPE_AMBIGUITY" | "ENTITY_AMBIGUITY",
      "term": "the vague word or concept",
      "question": "A clear, natural clarification question to ask the user",
      "options": [
        {{
          "id": "short_unique_id",
          "label": "Description of option",
          "sql_snippet": "Corresponding SQL fragment"
        }}
      ]
    }}
  ]
}}
"""

        try:
            response = client.chat.completions.create(
                model=GROQ_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": state.raw_query}
                ],
                response_format={"type": "json_object"},
                temperature=0.1
            )
            
            result = json.loads(response.choices[0].message.content)
            
            flagged_questions: List[ClarificationQuestion] = []
            if result.get("has_ambiguities", False):
                for amb in result.get("ambiguities", []):
                    options = [
                        ClarificationOption(
                            id=opt["id"],
                            label=opt["label"],
                            sql_snippet=opt.get("sql_snippet")
                        )
                        for opt in amb.get("options", [])
                    ]
                    flagged_questions.append(
                        ClarificationQuestion(
                            ambiguity_type=AmbiguityType(amb["ambiguity_type"]),
                            term=amb["term"],
                            question=amb["question"],
                            options=options
                        )
                    )

            state.detected_ambiguities = flagged_questions
            if flagged_questions:
                state.status = ExecutionStatus.NEEDS_CLARIFICATION
            else:
                state.status = ExecutionStatus.READY_TO_GENERATE

        except Exception as e:
            print(f"Error during ambiguity detection: {e}")
            state.status = ExecutionStatus.READY_TO_GENERATE

        return state