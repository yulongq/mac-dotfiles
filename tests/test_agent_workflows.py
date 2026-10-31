import json
import runpy
import sqlite3
import subprocess
import unittest
from unittest.mock import patch

from test_dotfiles import ROOT


SCRIPT = runpy.run_path(str(ROOT / "scripts/measure-agent-workflows"))


class WorkflowBaselineTests(unittest.TestCase):
    def test_catalog_evidence_stays_within_each_task(self):
        catalog = SCRIPT["load_cases"](ROOT / "maintenance/agent-workflows.toml")
        self.assertTrue(catalog["cases"])
        self.assertEqual(catalog["historical_configuration"], "unverified")

    def test_index_distinguishes_missing_usage_from_incomplete_coverage(self):
        query = SCRIPT["query_index"]
        complete = {"type": "end", "complete": True, "refresh": {}}
        with patch("subprocess.run", return_value=subprocess.CompletedProcess(
                [], 1, json.dumps(complete), "")):
            self.assertEqual(query("SELECT 1 WHERE 0"), [])
        for records in ([], [{**complete, "complete": False}],
                        [{**complete, "refresh": {"stale": True}}],
                        [{**complete, "unavailable_ranges": 1}],
                        [complete, {"type": "row", "data": {}}]):
            with self.subTest(records=records), patch("subprocess.run", return_value=
                    subprocess.CompletedProcess([], 0, "\n".join(map(json.dumps, records)), "")):
                with self.assertRaises(RuntimeError):
                    query("SELECT 1")

    def test_metrics_include_trailing_usage_and_keep_unknown_outcomes(self):
        database = sqlite3.connect(":memory:")
        self.addCleanup(database.close)
        database.row_factory = sqlite3.Row
        database.executescript("""
            CREATE TABLE sessions(agent, session_id, session_kind, file_id, path);
            CREATE TABLE call_outcomes(id, file_id, line_no, ok);
            CREATE TABLE requests(id, file_id, line_no);
            CREATE TABLE request_passes(request_id, model, input, cache_read,
                cache_write, output, reasoning);
            CREATE TABLE events(file_id, line_no);
            INSERT INTO call_outcomes VALUES
                (1,1,10,1),(2,1,11,NULL),(3,1,20,0),(4,1,21,0),(5,2,10,0);
            INSERT INTO requests VALUES (1,1,10),(2,1,20),(3,1,21);
            INSERT INTO request_passes VALUES
                (1,'model',100,50,NULL,9,3),(2,'model',NULL,NULL,NULL,4,NULL),
                (3,'model',999,999,999,999,999);
            INSERT INTO events VALUES (1,10),(1,19),(1,20);
        """)
        case = {
            "id": "sample", "agent": "codex", "session": "00000000-0000-0000-0000-000000000001",
            # The final reply is line 19; its usage record is line 20.
            "first_line": 10, "last_line": 20, "evidence": [10, 19, 20],
        }
        database.executemany("INSERT INTO sessions VALUES (?,?,?,?,?)", [
            ("codex", case["session"], "main", 1, "/synthetic/main.jsonl"),
            ("codex", case["session"], "subagent", 2, "/synthetic/subagent.jsonl"),
        ])
        measure = SCRIPT["measure"]
        with patch.dict(measure.__globals__, {"query_index": lambda sql: [
                dict(row) for row in database.execute(sql)]}):
            result = measure([case])[0]
            self.assertEqual(result["calls"], {
                "calls": 3, "failed": 1, "succeeded": 1, "outcome_unknown": 1,
            })
            usage = result["usage"][0]
            self.assertEqual((usage["passes"], usage["input"], usage["input_recorded"]), (2, 100, 1))
            self.assertEqual((usage["output"], usage["output_recorded"]), (13, 2))
            self.assertIsNone(usage["cache_write"])
            self.assertEqual(usage["cache_write_recorded"], 0)
            with self.assertRaisesRegex(RuntimeError, "missing evidence"):
                measure([{**case, "evidence": [15]}])
            database.execute("INSERT INTO sessions VALUES (?,?,?,?,?)",
                             ("codex", case["session"], "main", 3, "/synthetic/duplicate.jsonl"))
            with self.assertRaisesRegex(RuntimeError, "expected one indexed main transcript"):
                measure([case])


if __name__ == "__main__":
    unittest.main()
