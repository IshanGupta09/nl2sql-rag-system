# api.py — FastAPI backend
# ─────────────────────────────────────────────────────────────
# LOCAL / DOCKER USE ONLY — not needed for Streamlit Cloud.
# Run with:  uvicorn api:app --reload
#
# Streamlit Cloud deployment uses streamlit.py directly (standalone).
# ─────────────────────────────────────────────────────────────

import os
import sqlite3
import time
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel

load_dotenv(Path(__file__).resolve().parent / ".env")

from llm.sql_generator import generate_sql, correct_sql
from nlg.answer_generator import generate_answer

# RAG retriever is optional — only available if vectorstore is built
try:
    from rag.retriever import retrieve_context
    _RAG_AVAILABLE = True
except ImportError:
    _RAG_AVAILABLE = False

DEFAULT_DB  = "data/ecommerce.db"
UPLOAD_DIR  = "data/uploads"
Path(UPLOAD_DIR).mkdir(parents=True, exist_ok=True)

# ── Schema cache ─────────────────────────────────────────────
_schema_cache: dict[str, str] = {}

ENUM_LIKE_COLUMNS = {
    "customers": ["region", "customer_type"],
    "products":  ["category"],
}


def _get_distinct_values(cursor, table: str, column: str, limit: int = 5) -> list:
    try:
        cursor.execute(
            f"SELECT DISTINCT {column} FROM {table} WHERE {column} IS NOT NULL LIMIT {limit};"
        )
        return [str(row[0]) for row in cursor.fetchall()]
    except Exception:
        return []


def build_schema(db_path: str) -> str:
    """Auto-discover schema from any SQLite database."""
    parts = []
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        for table in tables:
            cursor.execute(f"PRAGMA table_info({table});")
            col_parts = []
            for col in cursor.fetchall():
                col_name, col_type = col[1], col[2]
                if col_type.upper() in ("TEXT", "VARCHAR") or col_type == "":
                    values = _get_distinct_values(cursor, table, col_name)
                    if 1 < len(values) <= 8:
                        values_str = ", ".join(f"'{v}'" for v in values)
                        col_parts.append(f"  {col_name} {col_type}  -- values: {values_str}")
                        continue
                col_parts.append(f"  {col_name} {col_type}")
            parts.append(f"Table: {table}\n" + "\n".join(col_parts))
    return "\n\n".join(parts)


def get_schema(db_path: str) -> str:
    if db_path not in _schema_cache:
        _schema_cache[db_path] = build_schema(db_path)
    return _schema_cache[db_path]


def get_table_info(db_path: str) -> list[dict]:
    tables = []
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        for (table,) in cursor.fetchall():
            cursor.execute(f"PRAGMA table_info({table});")
            cols = [{"name": r[1], "type": r[2]} for r in cursor.fetchall()]
            cursor.execute(f"SELECT COUNT(*) FROM {table};")
            row_count = cursor.fetchone()[0]
            tables.append({"table": table, "columns": cols, "row_count": row_count})
    return tables


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Building default schema cache...")
    if Path(DEFAULT_DB).exists():
        _schema_cache[DEFAULT_DB] = build_schema(DEFAULT_DB)
        print("Schema ready.")
    else:
        print(f"Warning: {DEFAULT_DB} not found.")
    yield
    print("Shutting down.")


app = FastAPI(title="NL2SQL RAG API — Multi-DB", version="14.0", lifespan=lifespan)

FORBIDDEN = {"DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "TRUNCATE"}


def is_safe_sql(sql: str) -> bool:
    return not any(word in sql.upper().split() for word in FORBIDDEN)


def execute_sql(sql: str, db_path: str):
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(sql)
            if cursor.description is None:
                return [], None
            columns = [d[0] for d in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()], None
    except Exception as e:
        return None, str(e)


# ── Endpoints ────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "running", "rag_available": _RAG_AVAILABLE}


@app.post("/upload-db")
async def upload_database(file: UploadFile = File(...)):
    """Upload a SQLite .db file and return its schema info."""
    if not file.filename.endswith(".db"):
        return {"error": "Only .db files are supported."}

    save_path = str(Path(UPLOAD_DIR) / file.filename)
    content   = await file.read()
    with open(save_path, "wb") as f:
        f.write(content)

    try:
        tables = get_table_info(save_path)
        schema = build_schema(save_path)
        _schema_cache[save_path] = schema
    except Exception as e:
        Path(save_path).unlink(missing_ok=True)
        return {"error": f"Invalid SQLite file: {e}"}

    return {
        "db_path":  save_path,
        "filename": file.filename,
        "tables":   tables,
        "schema":   schema,
    }


@app.get("/schema")
def get_schema_endpoint(db_path: str = DEFAULT_DB):
    try:
        return {
            "db_path": db_path,
            "tables":  get_table_info(db_path),
            "schema":  get_schema(db_path),
        }
    except Exception as e:
        return {"error": str(e)}


class QueryRequest(BaseModel):
    question: str
    db_path:  str = DEFAULT_DB


@app.post("/query")
async def query_database(request: QueryRequest):
    start = time.perf_counter()
    db    = request.db_path

    # Security: only allow paths inside data/
    try:
        db_resolved  = Path(db).resolve()
        project_root = Path(".").resolve()
        if not str(db_resolved).startswith(str(project_root / "data")):
            return {"error": "Access to this database path is not allowed."}
    except Exception:
        return {"error": "Invalid database path."}

    if not Path(db).exists():
        return {"error": f"Database not found: {db}"}

    try:
        schema = get_schema(db)

        # RAG context — only for default DB, only if vectorstore is built
        business_context = None
        if db == DEFAULT_DB and _RAG_AVAILABLE:
            try:
                business_context = retrieve_context(request.question)
            except Exception:
                pass

        sql = generate_sql(
            question=request.question,
            schema=schema,
            business_context=business_context,
        )

        if not sql:
            raise ValueError("LLM returned no SQL.")
        if not is_safe_sql(sql):
            raise ValueError(f"Unsafe SQL blocked: {sql}")

        result, error = execute_sql(sql, db)

        if error:
            corrected = correct_sql(
                question=request.question,
                schema=schema,
                business_context=business_context,
                previous_sql=sql,
                error=error,
            )
            if corrected and is_safe_sql(corrected):
                r2, e2 = execute_sql(corrected, db)
                if not e2:
                    sql, result, error = corrected, r2, e2

        nl_answer = None
        if not error and result is not None:
            try:
                nl_answer = generate_answer(
                    question=request.question,
                    sql=sql,
                    result=result,
                )
            except Exception:
                pass

        return {
            "question":           request.question,
            "db_path":            db,
            "final_sql":          sql if not error else None,
            "result":             result if not error else None,
            "nl_answer":          nl_answer,
            "error":              error,
            "execution_time_sec": round(time.perf_counter() - start, 3),
        }

    except Exception as e:
        return {
            "question":           request.question,
            "db_path":            db,
            "final_sql":          None,
            "result":             None,
            "nl_answer":          None,
            "error":              str(e),
            "execution_time_sec": round(time.perf_counter() - start, 3),
        }