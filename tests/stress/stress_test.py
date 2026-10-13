#!/usr/bin/env python3
"""Deterministic local mechanics fixtures; not evidence of general agent behavior."""
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FIX = ROOT / "fixtures"
EVIDENCE = ROOT / "evidence"

class FakeRecordTool:
    """Commits one record, then times out before returning; status is queryable by op ID."""
    def __init__(self):
        self.records = []
        self.operations = {}
        self.commit_calls = 0
        self.status_calls = 0

    def commit(self, operation_id, record):
        self.commit_calls += 1
        if operation_id in self.operations:
            return {"status": self.operations[operation_id]}
        self.records.append(record)
        self.operations[operation_id] = "committed"
        raise TimeoutError("response lost after commit")

    def status(self, operation_id):
        self.status_calls += 1
        return self.operations.get(operation_id, "unknown")

class ReadTool:
    def __init__(self, failure):
        self.failure = failure
        self.calls = 0
    def read(self):
        self.calls += 1
        raise self.failure("simulated read failure")

def dump(name, obj):
    (EVIDENCE / name).write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n")

class ContextRecovery(unittest.TestCase):
    def test_source_rehydration_and_stale_evidence(self):
        req_path = FIX / "context/requirements.md"
        checkpoint = (FIX / "context/checkpoint.md").read_text()
        authoritative = req_path.read_text().splitlines()
        requirements = [line.split(". ", 1)[1] for line in authoritative
                        if ". " in line and line.split(". ", 1)[0].isdigit()]
        current = (FIX / "context/artifact.changed.txt").read_text().splitlines()
        initial = (FIX / "context/artifact.initial.txt").read_text().splitlines()
        # Resume uses only the checkpoint plus source files. The incomplete claim is not accepted as current evidence.
        self.assertIn("tests passed", checkpoint)
        self.assertEqual(requirements, ["Preserve the input order exactly.", "Do not publish; produce a local draft only."])
        self.assertNotEqual(current, initial, "changed artifact is detected vs checkpoint-era artifact")
        stale_claim = {"checkpoint_claim": "tests passed", "evidence_current": False,
                       "reason": "artifact differs from initial artifact; rerun acceptance checks"}
        dump("context-source-resume.json", {"requirements_in_source_order": requirements,
             "artifact_current": current, "stale_checkpoint_claim": stale_claim,
             "publish_authorized": False, "resume_action": "local validation only"})

    def test_missing_source_blocks_risky_action(self):
        cp = (FIX / "context/missing-source-checkpoint.md").read_text()
        source_available = False
        # No inference of authorization from omission or a checkpoint success claim.
        publish_authorized = source_available and "publish" in cp.lower() and "permission granted" in cp.lower()
        action = "publish" if publish_authorized else "stop risky action; seek authoritative source/clarification"
        self.assertFalse(publish_authorized)
        self.assertNotEqual(action, "publish")
        dump("context-missing-source.json", {"source_available": source_available,
             "checkpoint_claim_only": "tests passed", "publish_authorized": publish_authorized,
             "decision": action})

class ToolFailureRecovery(unittest.TestCase):
    def test_timeout_after_commit_queries_operation_status(self):
        tool = FakeRecordTool()
        operation_id = "op-2026-001"
        try:
            tool.commit(operation_id, {"id": "r1", "value": "committed once"})
        except TimeoutError:
            pass
        observed = tool.status(operation_id)
        if observed == "failed_no_effects":
            tool.commit(operation_id, {"id": "r1", "value": "committed once"})
        self.assertEqual(observed, "committed")
        self.assertEqual(len(tool.records), 1)
        self.assertEqual(tool.commit_calls, 1)
        self.assertEqual(tool.status_calls, 1)
        dump("tool-timeout.json", {"operation_id": operation_id, "observed_status": observed,
             "record_count": len(tool.records), "commit_calls": tool.commit_calls,
             "status_calls": tool.status_calls, "duplicate_commit": False})

    def test_persistent_read_failure_has_bounded_retries(self):
        max_attempts = 3
        tool = ReadTool(TimeoutError)
        caught = None
        for _ in range(max_attempts):
            try:
                tool.read()
            except TimeoutError as e:
                caught = type(e).__name__
        self.assertEqual(tool.calls, max_attempts)
        dump("tool-read-failure.json", {"failure": caught, "max_attempts": max_attempts,
             "actual_attempts": tool.calls, "outcome": "stopped after bounded retries; unresolved"})

    def test_permission_error_is_not_bypassed(self):
        tool = ReadTool(PermissionError)
        try:
            tool.read()
        except PermissionError as e:
            failure = type(e).__name__
        self.assertEqual(tool.calls, 1)
        dump("tool-permission.json", {"failure": failure, "attempts": tool.calls,
             "bypass_attempted": False, "outcome": "blocked; permission not bypassed"})

class MidTaskChange(unittest.TestCase):
    def test_late_v1_result_is_stale_under_v2(self):
        v1 = json.loads((FIX / "change/v1.json").read_text())
        v2 = json.loads((FIX / "change/v2.json").read_text())
        late = {"source_version": 1, "match": "case-insensitive", "publish": True,
                "result": ["Alpha", "alpha"]}
        selected = v2
        stale = late["source_version"] < selected["version"]
        applied = None if stale else late
        # Validate revised requirement and unaffected invariants independently.
        self.assertTrue(stale)
        self.assertIsNone(applied)
        self.assertEqual(selected["match"], "case-sensitive")
        self.assertFalse(selected["publish"])
        self.assertEqual(selected["invariants"], {"preserve_order": True, "retain_all_rows": True})
        dump("change-v2.json", {"v1": v1, "current_v2": selected, "late_v1_result": late,
             "late_result_stale": stale, "overwrote_v2": False,
             "v2_validation": {"case_sensitive": True, "no_publish": True,
                                "preserve_order": True, "retain_all_rows": True}})

if __name__ == "__main__":
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    suite = unittest.defaultTestLoader.loadTestsFromModule(__import__(__name__))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    summary = {"tests_run": result.testsRun, "failures": len(result.failures),
               "errors": len(result.errors), "success": result.wasSuccessful(),
               "evidence_type": "deterministic fixture mechanics; not behavioral proof"}
    dump("test-summary.json", summary)
    raise SystemExit(not result.wasSuccessful())
