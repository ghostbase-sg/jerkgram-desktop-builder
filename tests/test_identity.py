"""Identity overlay rejects tampering before writes and verifies repeat execution."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
try:
    import identity
except ImportError:
    identity = None


def digest(data):
    return hashlib.sha256(data).hexdigest()


class MaterializationTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(identity, 'D1 materializer is missing')
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.source = self.root / 'source'
        self.source.mkdir()
        self.git('init', '-q')
        self.git('config', 'user.name', 'Fixture')
        self.git('config', 'user.email', 'fixture@localhost')
        (self.source / 'stock.txt').write_text('stock\n')
        self.git('add', '.')
        self.git('commit', '-qm', 'stock')
        self.sha = self.git('rev-parse', 'HEAD').strip()
        self.overlay = self.root / 'builder'
        (self.overlay / 'patches').mkdir(parents=True)
        (self.overlay / 'payloads').mkdir()
        patch = b'diff --git a/stock.txt b/stock.txt\n--- a/stock.txt\n+++ b/stock.txt\n@@ -1 +1 @@\n-stock\n+Jerkgram\n'
        (self.overlay / 'patches/identity.patch').write_bytes(patch)
        (self.overlay / 'patches/series').write_text('identity.patch\n')
        (self.overlay / 'payloads/icon.txt').write_bytes(b'own icon\n')
        self.config = {'schema': 1, 'upstream_commit': self.sha,
                       'patches': [{'path': 'patches/identity.patch', 'sha256': digest(patch)}],
                       'files': {'stock.txt': {'before': digest(b'stock\n'), 'after': digest(b'Jerkgram\n')},
                                 'own.txt': {'before': None, 'after': digest(b'own icon\n')}},
                       'payloads': [{'path': 'payloads/icon.txt', 'target': 'own.txt', 'sha256': digest(b'own icon\n')}]}
        self.save()

    def save(self):
        (self.overlay / 'D1_CONFIG.json').write_text(json.dumps(self.config))

    def git(self, *args):
        return subprocess.check_output(['git', '-C', str(self.source), *args], text=True)

    def apply(self):
        return identity.materialize(self.source, self.sha, self.overlay, submodules=False)

    def test_apply_and_repeat_preserve_revision_and_exact_inventory(self):
        result = self.apply()
        self.assertEqual((self.source / 'stock.txt').read_text(), 'Jerkgram\n')
        self.assertEqual((self.source / 'own.txt').read_text(), 'own icon\n')
        self.assertEqual(self.git('rev-parse', 'HEAD').strip(), self.sha)
        self.assertEqual(self.apply(), result)
        (self.source / 'own.txt').write_text('tampered')
        with self.assertRaises(ValueError):
            self.apply()

    def test_wrong_pin_dirty_input_and_existing_build_fail_without_writes(self):
        with self.assertRaises(ValueError):
            identity.materialize(self.source, '0' * 40, self.overlay, submodules=False)
        (self.source / 'stock.txt').write_text('user work\n')
        with self.assertRaises(ValueError):
            self.apply()
        self.assertEqual((self.source / 'stock.txt').read_text(), 'user work\n')
        (self.source / 'stock.txt').write_text('stock\n')
        (self.source / 'out').mkdir()
        with self.assertRaises(ValueError):
            self.apply()
        self.assertFalse((self.source / 'own.txt').exists())

    def test_every_preimage_and_payload_checked_before_any_write(self):
        for kind in ('preimage', 'payload', 'patch', 'postimage'):
            with self.subTest(kind=kind):
                original = json.loads(json.dumps(self.config))
                if kind == 'preimage':
                    self.config['files']['stock.txt']['before'] = '0' * 64
                elif kind == 'postimage':
                    self.config['files']['stock.txt']['after'] = '0' * 64
                elif kind == 'payload':
                    self.config['payloads'][0]['sha256'] = '0' * 64
                else:
                    self.config['patches'][0]['sha256'] = '0' * 64
                self.save()
                with self.assertRaises(ValueError):
                    self.apply()
                self.assertEqual((self.source / 'stock.txt').read_bytes(), b'stock\n')
                self.assertFalse((self.source / 'own.txt').exists())
                self.config = original
        self.save()

    def test_materialized_tree_rejects_extra_changes_and_new_files(self):
        self.apply()
        (self.source / 'extra').write_text('surprise')
        with self.assertRaises(ValueError):
            self.apply()

    def test_ignored_configuration_input_is_not_a_build_cache(self):
        (self.source / '.gitignore').write_text('Telegram/build/target\nout/\n')
        self.git('add', '.gitignore'); self.git('commit', '-qm', 'ignored input fixture')
        self.sha = self.git('rev-parse', 'HEAD').strip()
        self.config['upstream_commit'] = self.sha; self.save()
        target = self.source / 'Telegram/build/target'; target.parent.mkdir(parents=True); target.write_text('linux\n')
        with self.assertRaises(ValueError): self.apply()
        self.assertEqual((self.source / 'stock.txt').read_text(), 'stock\n')

    def test_path_traversal_and_symlink_payload_rejected(self):
        self.config['payloads'][0]['target'] = '../escape'
        self.save()
        with self.assertRaises(ValueError):
            self.apply()
        self.config['payloads'][0]['target'] = 'own.txt'
        (self.overlay / 'payloads/icon.txt').unlink()
        (self.overlay / 'payloads/icon.txt').symlink_to(self.source / 'stock.txt')
        self.save()
        with self.assertRaises(ValueError):
            self.apply()
        self.assertFalse((self.root / 'escape').exists())


if __name__ == '__main__':
    unittest.main()
