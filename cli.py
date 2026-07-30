#!/usr/bin/env python3
"""
Command Line Interface (CLI) Runner for Google ADK Agent.
Usage:
    python cli.py --query "Analyze Alphabet GOOGL risk and growth"
"""

import sys
import argparse
import json
from src.agent import workflow_executor
from src.eval.evaluator import evaluator

def main():
    parser = argparse.ArgumentParser(description="ADK Market Intelligence Agent CLI")
    parser.add_argument("--query", "-q", type=str, default="Analyze GOOGL market trends and financial risk", help="Research query or ticker symbol")
    parser.add_argument("--session", "-s", type=str, default="cli_session", help="Session ID")
    parser.add_argument("--eval", action="store_true", help="Run automated evaluation benchmark")

    args = parser.parse_args()

    print("\n========================================================")
    print("🤖 Google ADK Market Intelligence Agent CLI")
    print("========================================================\n")
    print(f"Executing Query: '{args.query}'\n")

    result = workflow_executor.run_intelligence_workflow(
        query=args.query,
        session_id=args.session
    )

    briefing = result.get("executive_briefing", {})
    print("--- EXECUTIVE BRIEFING ---")
    print(f"Title: {briefing.get('title')}")
    print(f"Risk Rating: {briefing.get('composite_risk_rating')}\n")
    print("Executive Summary:")
    print(briefing.get("executive_summary"))

    print("\nKey Findings:")
    for item in briefing.get("key_findings", []):
        print(f"  • {item}")

    print("\nStrategic Action Items:")
    for action in briefing.get("strategic_action_items", []):
        print(f"  ✓ {action}")

    print(f"\nExecution Latency: {result.get('latency_ms')} ms")
    print(f"Tools Executed: {', '.join(result.get('tools_executed', []))}")

    if args.eval:
        print("\n--- AUTOMATED BENCHMARK EVALUATION ---")
        eval_res = evaluator.evaluate_response(
            query=args.query,
            response_text=json.dumps(briefing),
            tools_called=result.get("tools_executed", []),
            expected_tools=["fetch_market_data", "calculate_risk_and_financial_health", "generate_executive_briefing"],
            context_used=True,
            latency_ms=result.get("latency_ms", 100.0)
        )
        print(f"Overall Score: {eval_res.overall_score}/100")
        print(f"  • Tool Usage: {eval_res.tool_usage_score}/25")
        print(f"  • Relevance: {eval_res.relevance_score}/25")
        print(f"  • Memory & Context: {eval_res.memory_context_score}/20")
        print(f"  • Latency: {eval_res.latency_score}/15")
        print(f"  • Format: {eval_res.output_format_score}/15")

    print("\n========================================================\n")

if __name__ == "__main__":
    main()
