"""
Golden Dataset Benchmark Runner for Google ADK Agent.
Executes automated regression testing across multi-scenario test cases,
computing pass/fail rates, latency percentiles, and 5-criteria rubric scores.
"""

import json
import os
import time
from typing import Dict, Any, List, Optional
from src.agent import workflow_executor
from src.eval.evaluator import evaluator


class BenchmarkReport:
    def __init__(self, total_cases: int, passed_cases: int, avg_score: float, results: List[Dict[str, Any]], duration_sec: float):
        self.total_cases = total_cases
        self.passed_cases = passed_cases
        self.failed_cases = total_cases - passed_cases
        self.pass_rate_pct = round((passed_cases / max(1, total_cases)) * 100.0, 1)
        self.avg_score = round(avg_score, 1)
        self.results = results
        self.duration_sec = round(duration_sec, 2)

    def print_summary(self):
        print("\n" + "=" * 70)
        print("🏆 ADK MARKET INTELLIGENCE AGENT - GOLDEN BENCHMARK REPORT")
        print("=" * 70)
        print(f"Total Test Cases: {self.total_cases} | Passed: {self.passed_cases} | Failed: {self.failed_cases}")
        print(f"Pass Rate:        {self.pass_rate_pct}%")
        print(f"Average Score:    {self.avg_score} / 100.0")
        print(f"Benchmark Time:   {self.duration_sec}s\n")
        print("-" * 70)
        print(f"{'ID':<8} {'Category':<24} {'Score':<8} {'Status':<8} {'Latency':<10}")
        print("-" * 70)
        for r in self.results:
            status = "✅ PASS" if r["passed"] else "❌ FAIL"
            print(f"{r['id']:<8} {r['category']:<24} {r['score']:<8} {status:<8} {r['latency_ms']}ms")
        print("=" * 70 + "\n")


class GoldenBenchmarkRunner:
    """
    Executes the golden regression dataset against the multi-agent system.
    """

    def __init__(self, dataset_path: Optional[str] = None):
        self.dataset_path = dataset_path or os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "data",
            "golden_dataset.json"
        )

    def load_dataset(self) -> Dict[str, Any]:
        with open(self.dataset_path, "r") as f:
            return json.load(f)

    def run_benchmark(self) -> BenchmarkReport:
        dataset = self.load_dataset()
        cases = dataset.get("test_cases", [])
        results = []
        scores = []
        passed_count = 0
        start_time = time.time()

        for tc in cases:
            tc_id = tc["id"]
            category = tc.get("category", "General")
            query = tc["query"]
            expected_tools = tc.get("expected_tools", [])
            min_score = tc.get("min_score", 80.0)

            t0 = time.time()
            res = workflow_executor.run_intelligence_workflow(
                query=query,
                session_id=f"benchmark_{tc_id.lower()}"
            )
            lat = round((time.time() - t0) * 1000, 2)

            # Check if this was a guardrail test case
            if tc.get("expect_guardrail_trigger"):
                passed_guard = res.get("status") == "GUARDRAIL_VIOLATION"
                score = 100.0 if passed_guard else 50.0
                eval_res_dict = {
                    "id": tc_id,
                    "category": category,
                    "score": score,
                    "passed": passed_guard and (score >= min_score),
                    "latency_ms": lat,
                    "feedback": [] if passed_guard else ["Guardrail did not intercept injection."]
                }
            else:
                eval_out = evaluator.evaluate_response(
                    query=query,
                    response_data=res,
                    expected_tools=expected_tools,
                    context_used=tc.get("context_used", True),
                    latency_ms=lat
                )
                score = eval_out.normalized_score
                is_pass = score >= min_score
                eval_res_dict = {
                    "id": tc_id,
                    "category": category,
                    "score": score,
                    "passed": is_pass,
                    "latency_ms": lat,
                    "criteria_breakdown": eval_out.criteria_breakdown,
                    "feedback": eval_out.feedback
                }

            scores.append(score)
            if eval_res_dict["passed"]:
                passed_count += 1
            results.append(eval_res_dict)

        avg_score = sum(scores) / max(1, len(scores))
        total_time = time.time() - start_time

        report = BenchmarkReport(
            total_cases=len(cases),
            passed_cases=passed_count,
            avg_score=avg_score,
            results=results,
            duration_sec=total_time
        )
        return report


if __name__ == "__main__":
    runner = GoldenBenchmarkRunner()
    report = runner.run_benchmark()
    report.print_summary()
