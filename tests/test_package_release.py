import json
from pathlib import Path
import shutil
import sys
import tarfile
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
try:
    import package_release
except ImportError:
    package_release=None

class PackageTests(unittest.TestCase):
    def test_archive_allowlist_strip_copy_and_hash_provenance(self):
        self.assertIsNotNone(package_release,'D1 packager is missing')
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);binary=p/'Jerkgram';shutil.copy2('/bin/true',binary)
            original=binary.read_bytes()
            (p/'private').mkdir();(p/'private/tdata').write_text('not a release member')
            files={'LICENSE.txt':b'fixture notice\n','integration/com.jerkgram.desktop.desktop':b'[Desktop Entry]\nName=Jerkgram\n'}
            result=package_release.create_archive(binary,p/'dist',files,{'version':'0.1.0-alpha.1','source':'fixture'},epoch=1)
            self.assertEqual(binary.read_bytes(),original)
            report=json.loads(result.read_text())
            archive=p/'dist'/report['artifact']['name']
            with tarfile.open(archive) as t:
                self.assertEqual(set(t.getnames()),{'Jerkgram/Jerkgram','Jerkgram/LICENSE.txt','Jerkgram/integration/com.jerkgram.desktop.desktop'})
                self.assertTrue(t.extractfile('Jerkgram/Jerkgram').read().startswith(b'\x7fELF'))
            self.assertEqual(report['binary']['original_bytes'],len(original))
            self.assertGreater(report['artifact']['bytes'],0)
            self.assertIn('sha256',report['artifact'])
            with self.assertRaises(ValueError):package_release.create_archive(binary,p/'other',{'../escape':b'bad'},{'version':'0.1.0-alpha.1'},epoch=1)
            self.assertFalse((p/'escape').exists())

    def test_undeclared_or_symlink_assets_cannot_enter_release(self):
        import hashlib
        self.assertIsNotNone(package_release)
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); folder=root/'payloads/linux-identity/generated'; folder.mkdir(parents=True)
            icon=folder/'icon16.png';icon.write_bytes(b'fixture')
            config={'payloads':[{'path':str(icon.relative_to(root)),'target':'Telegram/Resources/art/icon16.png','sha256':hashlib.sha256(b'fixture').hexdigest()}]}
            self.assertEqual(list(package_release.integration_assets(root,config)),['integration/icons/icon16.png'])
            (folder/'iconprivate.png').write_text('secret')
            with self.assertRaises(ValueError):package_release.integration_assets(root,config)
            (folder/'iconprivate.png').unlink();icon.unlink();icon.symlink_to('/etc/hostname')
            with self.assertRaises(ValueError):package_release.integration_assets(root,config)

class SourceNoticeTests(unittest.TestCase):
    def test_tracked_notices_only_not_untracked_credentials(self):
        import subprocess
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)
            subprocess.run(['git','init','-q',str(p)],check=True)
            (p/'LICENSE').write_text('fixture license')
            subprocess.run(['git','-C',str(p),'add','LICENSE'],check=True)
            (p/'LICENSE-private-key').write_text('must not ship')
            self.assertEqual(package_release.source_notices(p),{'licenses/source/LICENSE':b'fixture license'})
