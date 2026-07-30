#!/usr/bin/env python3
"""
Command Line Interface (CLI) Runner for Google ADK Agent.
Usage:
    python cli.py --query "Analyze Alphabet GOOGL risk and growth"
    python cli.py --eval-golden
    python cli.py --hitl
"""

import sys
import argparse
import json
from src.agent import workflow_executor
from src.eval.evaluator import evaluator
from src.eval.benchmark_runner import GoldenBenchmarkRunner
from src.orchestration.hitl import hitl_manager
from src.config import config


def main():
    parser = argparse.ArgumentParser(description="ADK Market Intelligence Agent CLI")
    parser.add_argument("--query", "-q", type=str, default="Analyze GOOGL market trends and financial risk", help="Research query or ticker symbol")
    parser.add_argument("--session", "-s", type=str, default="cli_session", help="Session ID")
    parser.add_argument("--eval", action="store_true", help="Run automated evaluation benchmark on current query")
    parser.add_argument("--eval-golden", action="store_true", help="Run formal Golden Dataset regression benchmark")
    parser.add_argument("--hitl", action="store_true", help="Interactive Human-in-the-Loop approval mode")

    args = parser.parse_args()

    print("\n========================================================")
    print("🤖 Google ADK Market Intelligence Agent CLI")
    print("========================================================")
    print(f"• Root Model:      {config.model_pro}")
    print(f"• Quant Model:     {config.model_flash}")
    print(f"• Research Model:  {config.model_flash_lite}")
    print(f"• Persistent Store:{config.session_db_path}")
    print("========================================================\n")

    if args.eval_golden:
        print("Running Golden Benchmark Regression Suite...\n")
        runner = GoldenBenchmarkRunner()
        report = runner.run_benchmark()
        report.print_summary()
        return

    print(f"Executing Query: '{args.query}'\n")

    result = workflow_executor.run_intelligence_workflow(
        query=args.query,
        session_id=args.session,
        auto_approve_hitl=not args.hitl
    )

    if result.get("status") == "GUARDRAIL_VIOLATION":
        print(f"⚠️ GUARDRAIL INTERCEPT: {result.get('error')} [{result.get('violation_code')}]")
        return

    briefing = result.get("executive_briefing", {})
    print("--- EXECUTIVE BRIEFING ---")
    print(f"Title:       {briefing.get('title')}")
    print(f"Risk Rating: {briefing.get('composite_risk_rating')}")
    print(f"Status:      {result.get('hitl_status')}\n")

    print("Executive Summary:")
    print(briefing.get("executive_summary"))

    print("\nKey Findings:")
    for item in briefing.get("key_findings", []):
        print(f"  • {item}")

    print("\nStrategic Action Items:")
    for action in briefing.get("strategic_action_items", []):
        print(f"  ✓ {action}")

    print("\nRegulatory Disclaimer:")
    print(f"  ℹ️ {briefing.get('disclaimer')}")

    print(f"\nExecution Latency: {result.get('latency_ms')} ms")
    print(f"Tools Executed:    {', '.join(result.get('tools_executed', []))}")
    print(f"Trace ID:          {result.get('trace_id')}")

    # Interactive Human-in-the-Loop Prompt
    if args.hitl and result.get("pending_approval"):
        pending = result.get("pending_approval")
        print("\n--- 🧑‍💼 HUMAN-IN-THE-LOOP (HITL) APPROVAL REQUIRED ---")
        print(f"Approval ID: {pending.get('approval_id')}")
        print(f"Reason:      {pending.get('description')}")
        choice = input("Enter decision [A]pprove / [R]eject / [M]odify (default A): ").strip().upper()
        if choice == "R":
            reason = input("Enter rejection reason: ")
            hitl_manager.reject(pending.get("approval_id"), reason)
            print("❌ Proposal Rejected by Operator.")
        elif choice == "M":
            notes = input("Enter operator modification notes: ")
            hitl_manager.modify(pending.get("approval_id"), briefing, notes)
            print("✏️ Proposal Modified & Approved by Operator.")
        else:
            hitl_manager.approve(pending.get("approval_id"), "Approved via CLI interactive session.")
            print("✅ Proposal Approved by Operator.")

    if args.eval:
        print("\n--- AUTOMATED BENCHMARK EVALUATION ---")
        eval_res = evaluator.evaluate_response(
            query=args.query,
            response_data=result,
            expected_tools=["fetch_market_data", "calculate_risk_and_financial_health", "generate_executive_briefing"],
            context_used=True,
            latency_ms=result.get("latency_ms", 100.0)
        )
        print(f"Overall Score:    {eval_res.total_score}/95 pts ({eval_res.normalized_score}%)")
        print("Criteria Breakdown:")
        for criterion, score in eval_res.criteria_breakdown.items():
            print(f"  • {criterion:<28}: {score}")
        print(f"Status: {'✅ PASSED' if eval_res.passed else '❌ FAILED'}")

    print("\n========================================================\n")


if __name__ == "__main__":
    main()
