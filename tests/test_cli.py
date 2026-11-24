import json
import subprocess
import sys
import unittest


class CliTests(unittest.TestCase):
    def test_offline_demo_returns_trace(self) -> None:
        run = subprocess.run([sys.executable, "main.py", "--offline"], capture_output=True, text=True, check=False)
        self.assertEqual(run.returncode, 0, run.stderr)
        output = json.loads(run.stdout)
        self.assertEqual([item["selected"] for item in output["decisions"]], ["research", "analysis", "finish"])
        self.assertEqual([item["agent"] for item in output["contributions"]], ["research", "analysis"])
        self.assertEqual(output["analysis"]["percent_change"], 50.0)
        self.assertIn("INC-104", output["answer"])
