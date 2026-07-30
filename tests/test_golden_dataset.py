"""
Regression test suite executing the formal Golden Benchmark Dataset.
"""

import unittest
from src.eval.benchmark_runner import GoldenBenchmarkRunner


class TestGoldenDataset(unittest.TestCase):

    def test_golden_dataset_benchmark(self):
        runner = GoldenBenchmarkRunner()
        report = runner.run_benchmark()

        self.assertEqual(report.failed_cases, 0)
        self.assertEqual(report.pass_rate_pct, 100.0)
        self.assertGreaterEqual(report.avg_score, 85.0)
        self.assertEqual(len(report.results), report.total_cases)


if __name__ == "__main__":
    unittest.main()
