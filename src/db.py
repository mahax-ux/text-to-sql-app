import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Tuple

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "dev.db"
SCHEMA_PATH = Path(__file__).resolve().parent.parent / "data" / "schema.sql"
SEED_PATH = Path(__file__).resolve().parent.parent / "data" / "seed.sql"


class DatabaseManager:
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self.init_db()

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self, force: bool = False):
        if self.db_path.exists() and not force:
            return

        with self.get_connection() as conn:
            with open(SCHEMA_PATH, "r") as f:
                conn.executescript(f.read())
            with open(SEED_PATH, "r") as f:
                conn.executescript(f.read())
            conn.commit()

    def get_schema_summary(self) -> str:
        with open(SCHEMA_PATH, "r") as f:
            return f.read()

    def execute_query(self, sql: str) -> Tuple[List[str], List[Dict[str, Any]]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql)
            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            rows = [dict(row) for row in cursor.fetchall()]
            return columns, rows


if __name__ == "__main__":
    db = DatabaseManager()
    cols, rows = db.execute_query("SELECT full_name, email, status FROM users")
    print("Database operational. Sample rows:", rows)