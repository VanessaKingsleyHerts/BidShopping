import pytest

def test_forced_failure():
    """
    This test always fails—used to generate a failure log for our CI anomaly detector.
    """
    assert False, "💥 Simulated CI failure for logging"
