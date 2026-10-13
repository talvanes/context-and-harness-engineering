#!/usr/bin/env python3
"""Focused recovery protocol regressions; separate from the preserved baseline harness."""
import unittest

MAX_ATTEMPTS = 2


class FakeCommitter:
    def __init__(self, first_status, second_status="committed"):
        self.calls = 0
        self.first_status = first_status
        self.second_status = second_status
        self.operation_status = "unknown"

    def commit(self, operation_id):
        self.calls += 1
        if self.calls == 1:
            if self.first_status == "committed":
                self.operation_status = "committed"
                raise TimeoutError("response lost after commit")
            if self.first_status == "failed_no_effects":
                self.operation_status = "failed_no_effects"
                raise TimeoutError("response lost; status confirms no effects")
            self.operation_status = "unknown"
            raise TimeoutError("response lost; status unavailable")
        if self.calls == 2:
            self.operation_status = self.second_status
            return self.second_status
        raise AssertionError("retry exceeded bounded attempt count")

    def status(self, operation_id):
        return self.operation_status


def recover(tool, operation_id="op-regression"):
    """One initial attempt; retry only an explicit no-effects failure, at most once."""
    try:
        result = tool.commit(operation_id)
        return {"decision": "completed", "status": result}
    except TimeoutError:
        status = tool.status(operation_id)
    if status == "committed":
        return {"decision": "do_not_replay", "status": status}
    if status == "unknown":
        return {"decision": "pause_duplicate_prone_action", "status": status}
    if status == "failed_no_effects":
        if tool.calls >= MAX_ATTEMPTS:
            return {"decision": "stop_retry_bound", "status": status}
        result = tool.commit(operation_id)
        return {"decision": "bounded_retry", "status": result}
    return {"decision": "stop_unrecognized_status", "status": status}


class RecoveryProtocolTests(unittest.TestCase):
    def test_committed_after_timeout_is_not_replayed(self):
        tool = FakeCommitter("committed")
        outcome = recover(tool)
        self.assertEqual(outcome, {"decision": "do_not_replay", "status": "committed"})
        self.assertEqual(tool.calls, 1)

    def test_unknown_status_is_not_retried(self):
        tool = FakeCommitter("unknown")
        outcome = recover(tool)
        self.assertEqual(outcome, {"decision": "pause_duplicate_prone_action", "status": "unknown"})
        self.assertEqual(tool.calls, 1)

    def test_confirmed_no_effects_failure_retries_within_bound(self):
        tool = FakeCommitter("failed_no_effects", second_status="committed")
        outcome = recover(tool)
        self.assertEqual(outcome, {"decision": "bounded_retry", "status": "committed"})
        self.assertEqual(tool.calls, 2)
        self.assertLessEqual(tool.calls, MAX_ATTEMPTS)


if __name__ == "__main__":
    unittest.main(verbosity=2)
