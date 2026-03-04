# llm/sql_generator.py
#
# Uses Groq API — free tier, works in India, ~1s response time.
# Get free key at: console.groq.com
# Install: pip install groq python-dotenv

import os
import re
from pathlib import Path

from dotenv import load_dotenv
from groq import Groq

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

_client = Groq(api_key=os.environ["GROQ_API_KEY"])
MODEL   = "llama-3.3-70b-versatile"   # Best free model on Groq for SQL

_SYSTEM = (
    "You are an expert SQLite query writer. "
    "Output ONLY the SQL statement — no markdown, no backticks, no explanation. "
    "Use only the tables and columns from the schema provided. "
    "Use exact string values shown in schema comments (e.g. 'premium', 'North'). "
    "SQLite syntax only: use strftime() or date('now','-N days') for dates. "
    "Never use DATEADD, GETDATE, ISNULL or other non-SQLite functions. "
    "Do NOT add WHERE filters not mentioned in the question. "
    "End the statement with a semicolon."
)

print(f"SQL generator ready: {MODEL} via Groq API")

# =====================================================
# DATE PHRASE MAP
# =====================================================

DATE_PHRASE_MAP = {
    r"last\s+month":     "strftime('%Y-%m', order_date) = strftime('%Y-%m', date('now','-1 month'))",
    r"this\s+month":     "strftime('%Y-%m', order_date) = strftime('%Y-%m', date('now'))",
    r"last\s+year":      "strftime('%Y', order_date) = strftime('%Y', date('now','-1 year'))",
    r"this\s+year":      "strftime('%Y', order_date) = strftime('%Y', date('now'))",
    r"last\s+7\s+days":  "order_date >= date('now', '-7 days')",
    r"last\s+30\s+days": "order_date >= date('now', '-30 days')",
    r"last\s+90\s+days": "order_date >= date('now', '-90 days')",
    r"today":            "order_date = date('now')",
    r"yesterday":        "order_date = date('now', '-1 day')",
}


def _resolve_date_phrases(question: str) -> tuple[str, str | None]:
    for pattern, sqlite_expr in DATE_PHRASE_MAP.items():
        if re.search(pattern, question, re.IGNORECASE):
            return question, f"Date hint — use exactly: {sqlite_expr}"
    return question, None


# =====================================================
# PROMPT BUILDER
# =====================================================

def _build_prompt(
    question: str,
    schema_text: str,
    business_context: str | None = None,
    previous_sql: str | None = None,
    error: str | None = None,
) -> str:
    question, date_hint = _resolve_date_phrases(question)

    parts = [f"Schema:\n{schema_text}"]
    if business_context:
        parts.append(f"Context: {business_context}")
    if date_hint:
        parts.append(date_hint)
    if previous_sql and error:
        parts.append(
            f"Your previous SQL had an error.\n"
            f"Bad SQL: {previous_sql}\n"
            f"Error: {error}\n"
            f"Write a corrected SQL."
        )
    parts.append(f"Question: {question}")
    return "\n\n".join(parts)


# =====================================================
# EXTRACTION + POST-PROCESS
# =====================================================

_SQL_PATTERN = re.compile(r"(select\s.+?)(;|\Z)", re.IGNORECASE | re.DOTALL)


def _extract_sql(text: str) -> str | None:
    if not text:
        return None
    text = re.sub(r"```sql\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"```\s*",    "", text)
    text = text.strip()

    match = _SQL_PATTERN.search(text)
    if not match:
        return None

    sql = match.group(1).strip()
    if not sql.endswith(";"):
        sql += ";"

    sql = re.sub(r"\bmonth\s*\(\s*(\w+)\s*\)", r"strftime('%m', \1)", sql, flags=re.IGNORECASE)
    sql = re.sub(r"\byear\s*\(\s*(\w+)\s*\)",  r"strftime('%Y', \1)", sql, flags=re.IGNORECASE)
    return sql


# =====================================================
# API CALL
# =====================================================

def _call(prompt: str) -> str:
    response = _client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": _SYSTEM},
            {"role": "user",   "content": prompt},
        ],
        temperature=0,
        max_tokens=300,
    )
    return response.choices[0].message.content or ""


# =====================================================
# SCHEMA RESOLVER
# =====================================================

def _resolve_schema(schema: str | None, schema_dict: dict | None) -> str:
    if schema_dict:
        return "\n".join(
            f"{table}({', '.join(cols)})"
            for table, cols in schema_dict.items()
        )
    if schema:
        return schema
    raise ValueError("Provide either schema or schema_dict.")


# =====================================================
# PUBLIC API
# =====================================================

def generate_sql(
    question: str,
    schema: str | None = None,
    schema_dict: dict | None = None,
    business_context: str | None = None,
) -> str | None:
    schema_text = _resolve_schema(schema, schema_dict)
    prompt      = _build_prompt(question, schema_text, business_context)
    return _extract_sql(_call(prompt))


def correct_sql(
    question: str,
    previous_sql: str,
    error: str,
    schema: str | None = None,
    schema_dict: dict | None = None,
    business_context: str | None = None,
) -> str | None:
    schema_text = _resolve_schema(schema, schema_dict)
    prompt      = _build_prompt(question, schema_text, business_context, previous_sql, error)
    return _extract_sql(_call(prompt))