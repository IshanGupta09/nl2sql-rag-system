# eval/report.py
#
# Run AFTER benchmark.py has produced eval/results.json
#
# Usage:
#   python eval/report.py
#
# Shows:
#   - Full accuracy summary
#   - Every failed test with actual vs expected SQL
#   - Actionable fix suggestions per failure type

import json
import os
import sys
from datetime import datetime

# =====================================================
# PATHS
# =====================================================

BASE_DIR     = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS_FILE = os.path.join(BASE_DIR, "eval", "results.json")

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
# FAILURE PATTERN ANALYSER
# Gives a human-readable suggestion for each failure
# =====================================================

def _analyse_failure(result: dict) -> str:
    sql    = (result.get("actual_sql") or "").upper()
    reason = result.get("reason", "").lower()
    error  = (result.get("api_error") or "").lower()
    cat    = result.get("category", "")

    if not result.get("actual_sql"):
        return "💡 Model returned no SQL. Prompt may need stronger instruction."

    if "syntax error" in error:
        return "💡 SQL syntax error. Check _fix_common_bugs() in sql_generator_fast.py."

    if "no such column" in error:
        return "💡 Hallucinated column. Pre-flight check should catch this — verify _preflight_check()."

    if "wrong value" in reason and cat == "Filter":
        return "💡 Wrong filter value. Ensure enum values are in schema cache (e.g. 'premium' not 'Premium')."

    if "empty result" in reason and cat == "Date Filter":
        return "💡 Date filter returned empty. Check DATE_PHRASE_MAP in sql_generator_fast.py."

    if "column" in reason and "not found" in reason:
        return "💡 Expected column missing. Model used a different column name or alias."

    if "expected" in reason and "rows" in reason:
        return "💡 Wrong row count. Model may be adding extra filters or missing GROUP BY."

    return "💡 Review actual SQL vs expected SQL above for clues."


# =====================================================
# MAIN REPORT
# =====================================================

def print_report():

    if not os.path.exists(RESULTS_FILE):
        print(f"\n{RED}No results file found at eval/results.json{RESET}")
        print(f"Run benchmark first: {CYAN}python eval/benchmark.py{RESET}\n")
        sys.exit(1)

    with open(RESULTS_FILE, "r") as f:
        data = json.load(f)

    total     = data["total"]
    passed    = data["passed"]
    failed    = data["failed"]
    accuracy  = data["accuracy_pct"]
    cats      = data["categories"]
    results   = data["results"]
    ts        = data["timestamp"][:19].replace("T", " ")

    color = GREEN if accuracy >= 80 else (YELLOW if accuracy >= 60 else RED)

    # ── Header ────────────────────────────────────────
    print(f"\n{BOLD}{CYAN}{'═' * 62}{RESET}")
    print(f"{BOLD}{CYAN}   QueryMind Benchmark Report{RESET}")
    print(f"{CYAN}   Generated: {ts}{RESET}")
    print(f"{BOLD}{CYAN}{'═' * 62}{RESET}\n")

    # ── Overall numbers ───────────────────────────────
    print(f"  {BOLD}Overall Accuracy{RESET}")
    print(f"  {'─' * 40}")
    print(f"  Total questions  : {BOLD}{total}{RESET}")
    print(f"  Passed           : {GREEN}{BOLD}{passed}{RESET}")
    print(f"  Failed           : {RED}{BOLD}{failed}{RESET}")
    print(f"  Accuracy         : {color}{BOLD}{accuracy}%{RESET}")
    print(f"  Avg query time   : {data['avg_time_sec']}s")
    print(f"  Total bench time : {data['total_time_sec']}s\n")

    # ── Category breakdown ────────────────────────────
    print(f"  {BOLD}Results by Category{RESET}")
    print(f"  {'─' * 40}")

    for cat, s in cats.items():
        p   = s["passed"]
        t   = s["total"]
        pct = round(p / t * 100)
        bar_filled = int(pct / 10)
        bar = "█" * bar_filled + "░" * (10 - bar_filled)
        c   = GREEN if pct >= 80 else (YELLOW if pct >= 60 else RED)
        print(f"  {cat:<22} {c}{p}/{t}  {bar}  {pct}%{RESET}")

    # ── Passed tests ──────────────────────────────────
    passed_tests = [r for r in results if r["passed"]]
    print(f"\n  {BOLD}{GREEN}✅ Passed Tests ({len(passed_tests)}){RESET}")
    print(f"  {'─' * 40}")
    for r in passed_tests:
        print(f"  {DIM}[{r['id']:02d}] {r['question'][:55]:<55}  {r['exec_time']}s{RESET}")

    # ── Failed tests — detailed breakdown ─────────────
    failed_tests = [r for r in results if not r["passed"]]

    if not failed_tests:
        print(f"\n  {GREEN}{BOLD}🎉 Perfect score — no failures!{RESET}\n")
    else:
        print(f"\n  {BOLD}{RED}❌ Failed Tests ({len(failed_tests)}) — Detailed Analysis{RESET}")
        print(f"  {'─' * 58}")

        for r in failed_tests:
            print(f"\n  {RED}{BOLD}[{r['id']:02d}] {r['question']}{RESET}")
            print(f"  {DIM}Category : {r['category']}{RESET}")
            print(f"  {DIM}Reason   : {r['reason']}{RESET}")

            if r.get("api_error"):
                print(f"  {RED}Error    : {r['api_error']}{RESET}")

            print(f"\n  {DIM}Expected SQL:{RESET}")
            print(f"  {CYAN}{r['expected_sql']}{RESET}")

            print(f"\n  {DIM}Actual SQL:{RESET}")
            actual = r.get("actual_sql") or "None"
            print(f"  {YELLOW}{actual}{RESET}")

            suggestion = _analyse_failure(r)
            print(f"\n  {suggestion}")
            print(f"  {'·' * 58}")

    # ── Resume line ───────────────────────────────────
    print(f"\n{BOLD}{CYAN}{'═' * 62}{RESET}")
    print(f"{BOLD}{CYAN}   📄 Copy this into your resume / README:{RESET}")
    print(f"{CYAN}{'═' * 62}{RESET}")
    print(f"\n  {DIM}\"Built an NL-to-SQL pipeline achieving {accuracy}% accuracy")
    print(f"   on a {total}-question benchmark spanning simple queries,")
    print(f"   filters, aggregations, JOINs, and date-range conditions.\"")
    print(f"{RESET}")


# =====================================================
# ENTRY POINT
# =====================================================

if __name__ == "__main__":
    print_report()