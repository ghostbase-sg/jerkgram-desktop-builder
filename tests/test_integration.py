import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
try:
    import install_linux
except ImportError:
    install_linux=None

class IntegrationTests(unittest.TestCase):
    def test_only_owned_paths_no_default_handler_takeover_and_dry_run(self):
        self.assertIsNotNone(install_linux,'Integration installer is missing')
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);pkg=p/'package with spaces';(pkg/'integration/icons').mkdir(parents=True)
            (pkg/'Jerkgram').write_text('fixture')
            (pkg/'integration/com.jerkgram.desktop.desktop').write_text('[Desktop Entry]\nName=Jerkgram\nExec=Jerkgram -- %U\nTryExec=Jerkgram\n[Desktop Action quit]\nExec=Jerkgram -quit\n')
            xdg=p/'xdg';(xdg/'applications').mkdir(parents=True)
            official=xdg/'applications/org.telegram.desktop.desktop';official.write_text('official')
            defaults=xdg/'applications/mimeapps.list';defaults.write_text('tg=official')
            plan=install_linux.install(pkg,xdg,False)
            self.assertFalse((xdg/'applications/com.jerkgram.desktop.desktop').exists())
            install_linux.install(pkg,xdg,True)
            text=(xdg/'applications/com.jerkgram.desktop.desktop').read_text()
            self.assertIn('package with spaces/Jerkgram" -- %U',text)
            self.assertEqual(official.read_text(),'official')
            self.assertEqual(defaults.read_text(),'tg=official')
            self.assertTrue(all('org.telegram' not in x for x in plan))
