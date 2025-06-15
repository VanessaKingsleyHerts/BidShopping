from django.test import SimpleTestCase

class SimulatedFailureTest(SimpleTestCase):
    def test_forced_failure(self):
        """Always fails – used to generate a failure log for CI anomaly detector."""
        #self.fail("💥 Simulated CI failure for logging")