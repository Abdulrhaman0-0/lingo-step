"""Pure benchmark accounting tests; they never claim measured model accuracy."""
import csv
import importlib.util
from pathlib import Path
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "benchmark_ai.py"
spec = importlib.util.spec_from_file_location("ai_benchmark", SCRIPT)
benchmark = importlib.util.module_from_spec(spec)
spec.loader.exec_module(benchmark)


class BenchmarkAccountingTests(unittest.TestCase):
    def test_letter_accuracy_counts_unknown_as_wrong(self):
        rows = [
            {"model": "camera_live", "device": "test-pi", "expected": "A",
             "predicted": "A", "raw_predicted": "A",
             "correct": "1", "raw_correct": "1", "status": "recognized",
             "inference_ms": "10", "response_ms": "800",
             "capture_ms": "20", "elapsed_ms": "800"},
            {"model": "camera_live", "device": "test-pi", "expected": "B",
             "predicted": "UNKNOWN", "raw_predicted": "A",
             "correct": "0", "raw_correct": "0", "status": "timeout",
             "inference_ms": "30", "response_ms": "",
             "capture_ms": "30", "elapsed_ms": "5000"},
            {"model": "camera_live", "device": "test-pi", "expected": "OTHER",
             "predicted": "UNKNOWN", "raw_predicted": "OTHER",
             "correct": "1", "raw_correct": "1", "status": "rejected",
             "inference_ms": "20", "response_ms": "",
             "capture_ms": "20", "elapsed_ms": "850"},
        ]
        result = benchmark.summarize(rows)
        self.assertEqual(result["letter_accuracy_pct"], 50.0)
        self.assertEqual(result["negative_rejection_pct"], 100.0)
        self.assertEqual(result["all_trials_accuracy_pct"], 66.67)
        self.assertEqual(result["unknown_or_rejected_on_letters"], 1)
        self.assertEqual(result["per_letter"]["B"]["accuracy_pct"], 0.0)
        self.assertEqual(result["inference_ms"]["mean_ms"], 20.0)
        self.assertEqual(result["inference_ms"]["p95_ms"], 29.0)
        self.assertEqual(result["response_ms"]["n"], 1)

    def test_labels_and_other_ground_truth(self):
        self.assertEqual(benchmark.parse_letters("A,B,C"), ["A", "B", "C"])
        self.assertEqual(benchmark.parse_letters("abc"), ["A", "B", "C"])
        for bad in ("", "AAB", "A1", "A-Z"):
            with self.assertRaises(ValueError):
                benchmark.parse_letters(bad)
        self.assertTrue(benchmark.is_correct("OTHER", "UNKNOWN"))
        self.assertTrue(benchmark.is_correct("OTHER", "OTHERS"))
        self.assertFalse(benchmark.is_correct("A", "UNKNOWN"))
        self.assertFalse(benchmark.is_correct("OTHER", "A"))
        self.assertFalse(benchmark.is_correct("A", "B"))

    def test_randomized_schedule_is_reproducible_and_balanced(self):
        a = benchmark.trial_order(["A", "B"], 10, 3, 27)
        self.assertEqual(a, benchmark.trial_order(["A", "B"], 10, 3, 27))
        self.assertEqual(a.count("A"), 10)
        self.assertEqual(a.count("B"), 10)
        self.assertEqual(a.count("OTHER"), 3)

    def test_reports_have_summary_and_confusion_matrix(self):
        with tempfile.TemporaryDirectory() as temp:
            csv_file = Path(temp) / "trials.csv"
            rows = [
                {"model": "mic_live", "device": "test", "trial": 1,
                 "expected": "A", "predicted": "B", "raw_predicted": "B",
                 "correct": "0", "raw_correct": "0", "status": "recognized",
                 "inference_ms": "90", "response_ms": "3100", "elapsed_ms": "3100"},
                {"model": "mic_live", "device": "test", "trial": 2,
                 "expected": "B", "predicted": "B", "raw_predicted": "B",
                 "correct": "1", "raw_correct": "1", "status": "recognized",
                 "inference_ms": "120", "response_ms": "3200", "elapsed_ms": "3200"},
            ]
            with csv_file.open("w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=benchmark.FIELDS)
                writer.writeheader()
                writer.writerows([{k: row.get(k, "") for k in benchmark.FIELDS}
                                  for row in rows])
            benchmark.write_report(csv_file)
            report = (csv_file.parent / "trials_summary.md").read_text(encoding="utf-8")
            self.assertIn("50.00%", report)
            with (csv_file.parent / "trials_confusion.csv").open(
                    encoding="utf-8", newline="") as f:
                reader = list(csv.DictReader(f))
                self.assertEqual(reader[0]["expected"], "A")
                self.assertEqual(reader[0]["B"], "1")
                self.assertEqual(reader[1]["B"], "1")

    def test_manifest_needs_ground_truth_and_existing_records(self):
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "labels.csv"
            source.write_text("path,expected\ncards/a01.jpg,A\ncards/no_card.jpg,others\n",
                              encoding="utf-8")
            self.assertEqual(
                benchmark.load_manifest(source),
                [(Path(temp) / "cards/a01.jpg", "A"),
                 (Path(temp) / "cards/no_card.jpg", "OTHER")],
            )
            with self.assertRaises(FileExistsError):
                existing = Path(temp) / "existing.csv"
                existing.write_text("do not overwrite", encoding="utf-8")
                benchmark.prepare_output("camera", existing)


if __name__ == "__main__":
    unittest.main()
