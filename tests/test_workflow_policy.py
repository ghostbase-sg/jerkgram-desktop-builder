from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
class WorkflowPolicyTests(unittest.TestCase):
    def test_expensive_jobs_are_manual_and_preflight_is_hosted_without_secrets(self):
        pre=(ROOT/'.github/workflows/linux-preflight.yml').read_text()
        self.assertIn('runs-on: ubuntu-24.04',pre);self.assertNotIn('self-hosted',pre);self.assertNotIn('secrets.',pre)
        for name in ('production.yml','toolchain-publish.yml'):
            text=(ROOT/'.github/workflows'/name).read_text()
            self.assertIn('  workflow_dispatch:',text);self.assertNotIn('  push:',text);self.assertNotIn('  pull_request:',text)
            self.assertIn("github.actor == 'ghostbase-sg'",text)
        self.assertIn('--execute-production',(ROOT/'.github/workflows/production.yml').read_text())
