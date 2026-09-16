import os
import json
from pathlib import Path
from typing import Dict, Any
from openai import OpenAI
from dotenv import load_dotenv

from src.state import EngineSessionState, ExecutionStatus, UserClarificationResponse
from src.db import DatabaseManager

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL", "https://api.groq.com/openai/v1")
)

GROQ_MODEL = "openai/gpt-oss-20b"


class SQLCompiler:
    def __init__(self):
        self.db_manager = DatabaseManager()
        self.schema_summary = self.db_manager.get_schema_summary()

    def compile_and_execute(self, state: EngineSessionState) -> EngineSessionState:
        # Build context from resolved clarifications
        resolved_context = []
        for res in state.resolved_clarifications:
            resolved_context.append(f"- Term '{res.term}': Selected option ID '{res.selected_option_id}'")

        system_prompt = f"""
You are an expert Text-to-SQL Compiler for SQLite. Your job is to convert a user's natural language request into a precise, executable SQLite query.

DATABASE SCHEMA:
{self.schema_summary}

USER'S ORIGINAL REQUEST:
"{state.raw_query}"

RESOLVED CLARIFICATIONS (User choices for ambiguous terms):
{json.dumps(resolved_context, indent=2) if resolved_context else "None (Query was unambiguous)"}

INSTRUCTIONS:
1. Write a valid SQLite query that precisely fulfills the user's request, incorporating all constraints from the resolved clarifications.
2. Ensure table names, column names, and joins are accurate according to the schema.
3. Return a JSON object with the generated SQL string.

OUTPUT FORMAT (JSON ONLY):
{{
  "sql": "SELECT ... FROM ..."
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
                temperature=0.0
            )

            result = json.loads(response.choices[0].message.content)
            sql = result.get("sql", "").strip()
            state.generated_sql = sql

            # Execute the query against SQLite
            columns, rows = self.db_manager.execute_query(sql)
            state.query_results = rows
            state.status = ExecutionStatus.SUCCESS

        except Exception as e:
            print(f"Error compiling or executing SQL: {e}")
            state.status = ExecutionStatus.FAILED

        return state


if __name__ == "__main__":
    test_state = EngineSessionState(
        session_id="test_compile_1",
        raw_query="Show me the top revenue for active users",
        resolved_clarifications=[
            UserClarificationResponse(term="revenue", selected_option_id="net_revenue"),
            UserClarificationResponse(term="top", selected_option_id="by_spend"),
            UserClarificationResponse(term="active_user", selected_option_id="status_active")
        ]
    )
    
    compiler = SQLCompiler()
    result_state = compiler.compile_and_execute(test_state)
    print(f"Status: {result_state.status}")
    print(f"Generated SQL:\n{result_state.generated_sql}")
    print(f"Query Results: {result_state.query_results}")