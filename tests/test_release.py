import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
try:
    import release
except ImportError:
    release = None

class ReleaseGateTests(unittest.TestCase):
    def test_config_gate_rejects_enabled_updater_or_unbounded_final_lto(self):
        self.assertIsNotNone(release, 'Release config gate is missing')
        with tempfile.TemporaryDirectory() as d:
            out=Path(d)
            (out/'CMakeFiles').mkdir()
            flags='-flto=auto -O3 -flto=1 --param=lto-max-streaming-parallelism=1'
            cache='DESKTOP_APP_DISABLE_AUTOUPDATE:BOOL=ON\nDESKTOP_APP_USE_PACKAGED:BOOL=OFF\nDESKTOP_APP_ENABLE_LTO:BOOL=ON\n'
            (out/'CMakeCache.txt').write_text(cache)
            ninja='build Release/Jerkgram: CXX_EXECUTABLE_LINKER__Telegram_Release @rsp\n  FLAGS = -flto=auto\n  LINK_FLAGS = '+flags+'\n  LINK_LIBRARIES = /usr/local/lib/libQt6Core.a /usr/local/lib/libQt6Gui.a /usr/local/lib/libQt6Widgets.a\n'
            p=out/'CMakeFiles/impl-Release.ninja';p.write_text(ninja)
            self.assertTrue(release.check_configuration(out))
            (out/'CMakeCache.txt').write_text(cache.replace('USE_PACKAGED:BOOL=OFF','USE_PACKAGED:INTERNAL=OFF'))
            self.assertTrue(release.check_configuration(out))
            p.write_text(ninja.replace(flags,flags+' -flto=auto'))
            with self.assertRaises(ValueError):release.check_configuration(out)
            p.write_text(ninja)
            (out/'CMakeCache.txt').write_text(cache.replace('AUTOUPDATE:BOOL=ON','AUTOUPDATE:BOOL=OFF'))
            with self.assertRaises(ValueError):release.check_configuration(out)
