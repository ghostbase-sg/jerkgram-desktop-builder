import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import tarfile
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('builder', ROOT / 'scripts/builder.py')

class BuilderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not (ROOT / 'scripts/builder.py').exists():
            raise AssertionError('builder implementation is missing')
        cls.b = importlib.util.module_from_spec(SPEC)
        SPEC.loader.exec_module(cls.b)

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.source = self.base / 'source'
        subprocess.run(['git', 'init', '-q', str(self.source)], check=True)
        self.git('config', 'user.name', 'Fixture')
        self.git('config', 'user.email', 'fixture@example.invalid')
        (self.source / 'stock.txt').write_text('stock\n')
        self.git('add', '.')
        self.git('commit', '-qm', 'fixture')
        self.sha = self.git('rev-parse', 'HEAD').strip()

    def git(self, *args):
        return subprocess.check_output(['git', '-C', str(self.source), *args], text=True)

    def test_verify_rejects_wrong_revision_and_dirty_tree(self):
        self.b.verify_source(self.source, self.sha)
        with self.assertRaises(ValueError):
            self.b.verify_source(self.source, '0' * 40)
        (self.source / 'stock.txt').write_text('changed\n')
        with self.assertRaises(ValueError):
            self.b.verify_source(self.source, self.sha)

    def test_verify_rejects_untracked_files(self):
        (self.source / 'surprise').write_text('unexpected')
        with self.assertRaises(ValueError):
            self.b.verify_source(self.source, self.sha)

    def test_zero_materialization_and_nonempty_overlay_rejection(self):
        overlay = self.base / 'builder'
        (overlay / 'patches').mkdir(parents=True)
        (overlay / 'payloads').mkdir()
        (overlay / 'patches/series').write_text('# No D1 patches\n')
        (overlay / 'payloads/manifest.json').write_text('[]')
        before = self.git('rev-parse', 'HEAD')
        self.assertEqual(self.b.materialize(self.source, self.sha, overlay), [])
        self.assertEqual(self.git('rev-parse', 'HEAD'), before)
        (overlay / 'patches/series').write_text('unimplemented.patch\n')
        with self.assertRaises(ValueError):
            self.b.materialize(self.source, self.sha, overlay)
        self.assertEqual(self.git('status', '--porcelain'), '')

    def test_secret_validation_and_redaction(self):
        env = {'TDESKTOP_API_ID': '1234567', 'TDESKTOP_API_HASH': 'a' * 32}
        values = self.b.credentials(env)
        self.assertEqual(self.b.redact('ID=1234567 HASH=' + 'a' * 32, values), 'ID=[REDACTED] HASH=[REDACTED]')
        for invalid in ({}, {'TDESKTOP_API_ID': 'x', 'TDESKTOP_API_HASH': 'a' * 32}):
            with self.assertRaises(ValueError):
                self.b.credentials(invalid)

    def test_build_adapter_redacts_failure_and_limits_lto_without_secret_argv(self):
        import contextlib
        import io
        from unittest.mock import patch
        docker = self.base / 'docker'
        argv_file = self.base / 'argv.json'
        docker.write_text("#!/usr/bin/env python3\nimport os,json,sys\njson.dump(sys.argv,open(os.environ['ARGV_FILE'],'w'))\nprint(os.environ['TDESKTOP_API_ID']+' '+os.environ['TDESKTOP_API_HASH'])\nsys.exit(7)\n")
        docker.chmod(0o755)
        env = dict(os.environ, PATH=str(self.base) + os.pathsep + os.environ['PATH'],
                   TDESKTOP_API_ID='1234567', TDESKTOP_API_HASH='b' * 32, ARGV_FILE=str(argv_file))
        output = io.StringIO()
        with patch.dict(os.environ, env, clear=True), contextlib.redirect_stdout(output):
            with self.assertRaisesRegex(ValueError, 'Release build failed'):
                self.b.build_release(self.source, self.sha, 'fixture-image', 2)
        args = json.loads(argv_file.read_text())
        joined = ' '.join(args)
        self.assertNotIn('1234567', joined)
        self.assertNotIn('b' * 32, joined)
        self.assertIn('-flto=1 --param=lto-max-streaming-parallelism=1', joined)
        self.assertNotIn('1234567', output.getvalue())
        self.assertNotIn('b' * 32, output.getvalue())
        self.assertIn('[REDACTED]', output.getvalue())

    def test_prepare_new_checkout_fetches_exact_tag(self):
        self.git('tag', 'vfixture')
        dest = self.base / 'prepared'
        self.b.prepare(dest, str(self.source), 'vfixture', self.sha, False)
        self.assertEqual(subprocess.check_output(['git', '-C', str(dest), 'rev-parse', 'HEAD'], text=True).strip(), self.sha)
        bad = self.base / 'mismatched'
        with self.assertRaisesRegex(ValueError, 'does not resolve'):
            self.b.prepare(bad, str(self.source), 'vfixture', '0' * 40, False)
        self.assertFalse((bad / 'stock.txt').exists())

    def test_package_strips_copy_and_emits_verified_provenance(self):
        binary = self.base / 'Telegram'
        shutil.copy2('/bin/true', binary)
        before = binary.read_bytes()
        out = self.base / 'artifacts'
        manifest_path = self.b.package(binary, out, self.source, self.sha, '0.0.0-d0', ROOT)
        manifest = json.loads(manifest_path.read_text())
        archive = out / manifest['artifact']['name']
        self.assertEqual(binary.read_bytes(), before)
        self.assertEqual(manifest['artifact']['sha256'], self.b.sha256(archive))
        self.assertEqual(manifest['upstream_commit'], self.sha)
        self.assertEqual(manifest['product_changes'], [])
        with tarfile.open(archive) as tf:
            self.assertEqual(tf.getnames(), ['Telegram'])
            data = tf.extractfile('Telegram').read()
            self.assertTrue(data.startswith(b'\x7fELF'))
            self.assertEqual(len(data), manifest['binary']['stripped_bytes'])
        self.assertIn(archive.name, (out / 'SHA256SUMS').read_text())
        with self.assertRaises(ValueError):
            self.b.package(binary, out, self.source, self.sha, '0.0.0-d0', ROOT)
        with self.assertRaises(ValueError):
            self.b.package(binary, self.source / 'dist', self.source, self.sha, '0.0.0-d0', ROOT)

    def test_prepare_existing_wrong_checkout_preserves_contents(self):
        before = (self.source / 'stock.txt').read_bytes()
        with self.assertRaises(ValueError):
            self.b.prepare(self.source, 'file:///unused', 'v0', '0' * 40, False)
        self.assertEqual((self.source / 'stock.txt').read_bytes(), before)
        self.assertEqual(self.git('rev-parse', 'HEAD').strip(), self.sha)

if __name__ == '__main__':
    unittest.main()
