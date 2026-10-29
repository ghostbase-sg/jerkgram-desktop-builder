import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
try:import toolchain_actions as actions
except ImportError:actions=None
class ToolchainActionsTests(unittest.TestCase):
    def test_dispatch_only_pinned_infrastructure_operations(self):
        self.assertIsNotNone(actions)
        payload=actions.dispatch_body('d2/fast-dev-build','restore-registry')
        self.assertEqual(payload['inputs'],{'retain_toolchain':True,'toolchain_operation':'restore-registry'})
        self.assertEqual(payload['ref'],'d2/fast-dev-build')
        for value in ('build','production','publish; env'):
            with self.assertRaises(ValueError):actions.dispatch_body('d2/fast-dev-build',value)
