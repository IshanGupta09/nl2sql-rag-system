# eval/benchmark.py
#
# Usage:
#   Make sure uvicorn api:app is running, then:
#   python eval/benchmark.py

import json
import os
import sys
import time
from datetime import datetime

import requests

# =====================================================
# PATHS
# =====================================================

BASE_DIR       = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
QUESTIONS_FILE = os.path.join(BASE_DIR, "eval", "questions.json")
RESULTS_FILE   = os.path.join(BASE_DIR, "eval", "results.json")
API_URL        = "http://127.0.0.1:8000/query"

# sqlcoder-7b-2 can take up to ~90s on complex JOIN queries
REQUEST_TIMEOUT = 200

# =====================================================
# COLORS
# =====================================================

GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
DIM    = "\033[2m"
RESET  = "\033[0m"

# =====================================================
# API CALL
# =====================================================

def call_api(question: str) -> dict:
    try:
        resp = requests.post(
            API_URL,
            json={"question": question},
            timeout=REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.ConnectionError:
        print(f"\n{RED}ERROR: Cannot connect to API. Run: uvicorn api:app{RESET}\n")
        sys.exit(1)
    except requests.exceptions.Timeout:
        return {
            "error": f"Timed out after {REQUEST_TIMEOUT}s",
            "final_sql": None,
            "result": None,
            "execution_time_sec": REQUEST_TIMEOUT,
        }
    except Exception as e:
        return {
            "error": str(e),
            "final_sql": None,
            "result": None,
            "execution_time_sec": 0,
        }


# =====================================================
# GRADERS
# =====================================================

def grade(test: dict, response: dict) -> tuple[bool, str]:
    if response.get("error"):
        return False, f"API error: {response['error']}"

    if not response.get("final_sql"):
        return False, "No SQL generated"

    result = response.get("result")
    if result is None:
        return False, "No result returned"

    check = test.get("result_check")

    if check == "non_empty":
        return _grade_non_empty(result)

    elif check == "exact_row_count":
        return _grade_exact_rows(result, test.get("expected_rows"))

    elif check == "has_column":
        return _grade_has_column(result, test["expected_column"])

    return False, f"Unknown check type: {check}"


def _grade_non_empty(result: list) -> tuple[bool, str]:
    if result and len(result) > 0:
        return True, f"{len(result)} row(s) returned"
    return False, "Empty result — query returned 0 rows"


def _grade_exact_rows(result: list, expected: int | None) -> tuple[bool, str]:
    if expected is None:
        return _grade_non_empty(result)
    actual = len(result)
    if actual == expected:
        return True, f"Exactly {actual} row(s) as expected"
    return False, f"Expected {expected} rows, got {actual}"


def _grade_has_column(result: list, column: str) -> tuple[bool, str]:
    if not result:
        return False, "Empty result"
    cols = [k.lower() for k in result[0].keys()]
    if column.lower() in cols:
        return True, f"Column '{column}' present, {len(result)} row(s)"
    return False, f"Column '{column}' missing. Got columns: {list(result[0].keys())}"


# =====================================================
# MAIN RUNNER
# =====================================================

def run_benchmark():
    with open(QUESTIONS_FILE, "r") as f:
        questions = json.load(f)

    total     = len(questions)
    passed    = 0
    failed    = 0
    results   = []
    start_all = time.perf_counter()

    print(f"\n{BOLD}{CYAN}{'═' * 62}{RESET}")
    print(f"{BOLD}{CYAN}   QueryMind Evaluation Benchmark{RESET}")
    print(f"{CYAN}   {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{RESET}")
    print(f"{CYAN}   Timeout per question: {REQUEST_TIMEOUT}s{RESET}")
    print(f"{BOLD}{CYAN}{'═' * 62}{RESET}\n")

    category_stats: dict[str, dict] = {}

    for i, test in enumerate(questions, 1):
        cat = test["category"]
        q   = test["question"]

        if cat not in category_stats:
            category_stats[cat] = {"passed": 0, "total": 0}
        category_stats[cat]["total"] += 1

        print(f"{DIM}[{i:02d}/{total}]{RESET} {q}")
        print(f"        {DIM}Category: {cat}{RESET}")

        t0       = time.perf_counter()
        response = call_api(q)
        elapsed  = round(time.perf_counter() - t0, 2)

        ok, reason = grade(test, response)

        if ok:
            passed += 1
            category_stats[cat]["passed"] += 1
            status = f"{GREEN}✅ PASS{RESET}"
        else:
            failed += 1
            status = f"{RED}❌ FAIL{RESET}"

        sql_display = (response.get("final_sql") or "None")
        if len(sql_display) > 80:
            sql_display = sql_display[:77] + "..."

        print(f"        {status}  {DIM}({elapsed}s){RESET}")
        print(f"        {DIM}SQL: {sql_display}{RESET}")
        print(f"        {DIM}Why: {reason}{RESET}")
        print()

        results.append({
            "id":           test["id"],
            "category":     cat,
            "question":     q,
            "expected_sql": test["expected_sql"],
            "actual_sql":   response.get("final_sql"),
            "passed":       ok,
            "reason":       reason,
            "exec_time":    elapsed,
            "api_error":    response.get("error"),
        })

    total_time = round(time.perf_counter() - start_all, 1)
    accuracy   = round(passed / total * 100)

    print(f"\n{BOLD}{'─' * 62}{RESET}")
    print(f"{BOLD}  Results by Category{RESET}")
    print(f"{'─' * 62}{RESET}")
    for cat, s in category_stats.items():
        p   = s["passed"]
        t   = s["total"]
        pct = round(p / t * 100)
        bar = "█" * int(pct / 10) + "░" * (10 - int(pct / 10))
        c   = GREEN if pct >= 80 else (YELLOW if pct >= 60 else RED)
        print(f"  {cat:<20} {c}{p}/{t}  {bar}  {pct}%{RESET}")

    summary_color = GREEN if accuracy >= 80 else (YELLOW if accuracy >= 60 else RED)
    print(f"\n{BOLD}{'═' * 62}{RESET}")
    print(f"{BOLD}  BENCHMARK SUMMARY{RESET}")
    print(f"{'═' * 62}{RESET}")
    print(f"  Total questions  : {BOLD}{total}{RESET}")
    print(f"  Passed           : {GREEN}{BOLD}{passed}{RESET}")
    print(f"  Failed           : {RED}{BOLD}{failed}{RESET}")
    print(f"  Accuracy         : {summary_color}{BOLD}{accuracy}%{RESET}")
    print(f"  Total time       : {total_time}s")
    print(f"  Avg per question : {round(total_time / total, 1)}s")
    print(f"{'═' * 62}\n")

    print(f"{BOLD}{CYAN}  📄 Resume line:{RESET}")
    print(f"  {DIM}\"Achieved {accuracy}% SQL accuracy on a {total}-question benchmark")
    print(f"   covering simple queries, filters, aggregations, JOINs, and date filters.\"{RESET}\n")

    os.makedirs(os.path.dirname(RESULTS_FILE), exist_ok=True)
    output = {
        "timestamp":      datetime.now().isoformat(),
        "total":          total,
        "passed":         passed,
        "failed":         failed,
        "accuracy_pct":   accuracy,
        "total_time_sec": total_time,
        "avg_time_sec":   round(total_time / total, 1),
        "categories":     category_stats,
        "results":        results,
    }
    with open(RESULTS_FILE, "w") as f:
        json.dump(output, f, indent=2)

    print(f"  {DIM}Saved → eval/results.json{RESET}\n")
    return output


if __name__ == "__main__":
    run_benchmark()