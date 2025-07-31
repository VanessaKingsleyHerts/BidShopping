from django.test import SimpleTestCase
import os

class SimulatedFailureTest(SimpleTestCase):
    # def test_forced_failure(self):
        # """Always fails – used to generate a failure log for CI anomaly detector."""
        # self.fail("💥 Simulated CI failure for logging")

    def test_failure_sim(self):
    if os.environ.get("FAIL_NEXT") == "1":
    self.assertEqual(1, 0)  # Force fail
