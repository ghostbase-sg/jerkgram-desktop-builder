import sys
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
try:
    from updater_runtime_probe import discovery_hit
except ImportError:
    discovery_hit=None

class UpdaterProbeTests(unittest.TestCase):
    def test_gdb_command_listing_is_not_a_discovery_event(self):
        self.assertIsNotNone(discovery_hit)
        listing='1 breakpoint keep y 0x123\n        printf "UPDATER_HIT HTTP\\n"\n        quit 41\n'
        self.assertFalse(discovery_hit(listing))
        self.assertTrue(discovery_hit('Breakpoint 1 at 0x123\nUPDATER_HIT HTTP\n'))
