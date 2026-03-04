# nlg/answer_generator.py
#
# Natural language answer generation using Groq API.

import json
import os
import re
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from groq import Groq

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

_client = Groq(api_key=os.environ["GROQ_API_KEY"])
MODEL   = "llama-3.3-70b-versatile"

_SYSTEM = (
    "You summarise database query results in plain English. "
    "Write exactly one clear sentence. No SQL, no technical terms. End with a period."
)


def _summarise_result(result: list[dict]) -> str:
    if not result:
        return "0 rows returned"
    n      = len(result)
    sample = result[:5] if n > 5 else result
    text   = json.dumps(sample, indent=None, default=str)
    if n > 5:
        text += f"\n... {n} total rows"
    return text


def generate_answer(
    question: str,
    sql: str,
    result: list[dict[str, Any]],
) -> str:
    if not result:
        return "No results were found for your query."

    prompt = (
        f"Question: {question}\n"
        f"SQL used: {sql}\n"
        f"Query result: {_summarise_result(result)}\n\n"
        "Write one clear, specific sentence answering the question. "
        "Include exact numbers or names from the result. End with a period."
    )

    try:
        response = _client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": _SYSTEM},
                {"role": "user",   "content": prompt},
            ],
            temperature=0,
            max_tokens=120,
        )
        answer = (response.choices[0].message.content or "").strip()

        if re.search(r"\bSELECT\b|\bFROM\b|\bWHERE\b", answer, re.IGNORECASE):
            return _fallback(question, result)
        if len(answer) > 300:
            return answer[:300].rsplit(".", 1)[0] + "."
        return answer

    except Exception as e:
        print(f"[NLG Error] {e}")
        return _fallback(question, result)


def _fallback(question: str, result: list[dict]) -> str:
    n = len(result)
    if n == 0:
        return "No results were found for your query."
    if n == 1:
        values = list(result[0].values())
        if len(values) == 1:
            val = values[0]
            q   = question.lower()
            if isinstance(val, (int, float)):
                if "how many" in q:                return f"There are {int(val):,} in total."
                if "revenue" in q or "total" in q: return f"The total is ${val:,.2f}."
                if "average" in q or "avg" in q:   return f"The average is ${val:,.2f}."
                if "highest" in q or "max" in q:   return f"The highest value is ${val:,.2f}."
                if "lowest"  in q or "min" in q:   return f"The lowest value is ${val:,.2f}."
            return f"The result is {val}."
    return f"Your query returned {n} result{'s' if n != 1 else ''}."