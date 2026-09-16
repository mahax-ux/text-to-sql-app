import sys
import traceback

try:
    from src.state import EngineSessionState, UserClarificationResponse, ExecutionStatus
    from src.detector import AmbiguityDetector
    from src.sql_compiler import SQLCompiler
except Exception as e:
    print("Import Error during startup:")
    traceback.print_exc()
    sys.exit(1)

def run_cli():
    print("=== Text-to-SQL Clarification Engine (Groq / SQLite) ===")
    print("Type your database question below (or type 'exit' to quit).\n")

    try:
        detector = AmbiguityDetector()
        compiler = SQLCompiler()
    except Exception as e:
        print("Initialization Error (Check your API key and connection):")
        traceback.print_exc()
        return

    while True:
        try:
            raw_query = input("\nQuery > ").strip()
            if not raw_query or raw_query.lower() in ["exit", "quit"]:
                break

            # Initialize session state
            session_state = EngineSessionState(
                session_id="cli_sess_1",
                raw_query=raw_query
            )

            # Step 1: Detect ambiguities
            print("Analyzing query for ambiguities...")
            session_state = detector.analyze(session_state)

            # Step 2: Handle clarifications if needed
            if session_state.status == ExecutionStatus.NEEDS_CLARIFICATION:
                print("\n[!] Clarification needed to ensure precise SQL generation:")
                resolved_responses = []

                for idx, q in enumerate(session_state.detected_ambiguities, 1):
                    print(f"\n{idx}. {q.question}")
                    for opt_idx, opt in enumerate(q.options, 1):
                        print(f"   [{opt_idx}] {opt.label}")
                    
                    choice = input("Select option number: ").strip()
                    try:
                        selected_opt = q.options[int(choice) - 1]
                        resolved_responses.append(
                            UserClarificationResponse(
                                term=q.term,
                                selected_option_id=selected_opt.id
                            )
                        )
                    except (ValueError, IndexError):
                        print("Invalid selection. Defaulting to first option.")
                        resolved_responses.append(
                            UserClarificationResponse(
                                term=q.term,
                                selected_option_id=q.options[0].id
                            )
                        )

                session_state.resolved_clarifications = resolved_responses

            # Step 3: Compile and Execute SQL
            print("\nCompiling and executing SQL...")
            session_state = compiler.compile_and_execute(session_state)

            if session_state.status == ExecutionStatus.SUCCESS:
                print("\n--- Generated SQL ---")
                print(session_state.generated_sql)
                print("\n--- Query Results ---")
                if session_state.query_results:
                    for row in session_state.query_results:
                        print(row)
                else:
                    print("(Query returned 0 rows)")
            else:
                print("\nFailed to compile or execute query.")

        except KeyboardInterrupt:
            print("\nExiting...")
            sys.exit(0)
        except Exception as e:
            print(f"\nAn error occurred during execution: {e}")
            traceback.print_exc()

if __name__ == "__main__":
    run_cli()