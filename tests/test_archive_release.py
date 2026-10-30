import json,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
try:import archive_release as ar
except ImportError:ar=None
class ArchiveReleaseTests(unittest.TestCase):
    def test_split_join_hashes_and_tamper_fail_closed(self):
        self.assertIsNotNone(ar)
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);archive=root/'image.tar.zst';archive.write_bytes(b'0123456789');image='sha256:'+'1'*64
            plan=ar.plan(archive,image,chunk_bytes=4)
            self.assertEqual([p['bytes'] for p in plan['parts']],[4,4,2])
            chunks=root/'chunks';chunks.mkdir()
            for p in plan['parts']:ar.spool(archive,p,chunks/p['name'])
            result=root/'joined.zst';ar.join(chunks,plan,result);self.assertEqual(result.read_bytes(),archive.read_bytes())
            (chunks/plan['parts'][1]['name']).write_bytes(b'xxxx')
            with self.assertRaises(ValueError):ar.join(chunks,plan,root/'corrupt.zst')
            self.assertFalse((root/'corrupt.zst').exists())
            with self.assertRaises(ValueError):ar.join(chunks,plan,result)
    def test_existing_remote_asset_must_match_its_locked_digest(self):
        self.assertIsNotNone(ar)
        part={'name':'part-0000','bytes':4,'sha256':'a'*64}
        self.assertTrue(ar.asset_matches({'name':'part-0000','size':4,'digest':'sha256:'+'a'*64},part))
        self.assertFalse(ar.asset_matches({'name':'part-0000','size':4,'digest':'sha256:'+'b'*64},part))
    def test_transient_api_timeout_is_bounded_and_retried(self):
        import subprocess
        from unittest.mock import patch
        error=subprocess.CalledProcessError(1,['gh','api'],stderr=b'TLS handshake timeout')
        with patch.object(ar.subprocess,'check_output',side_effect=[error,b'[]']) as call,patch.object(ar.time,'sleep'):
            self.assertEqual(ar.api('repos/example/releases'),[]);self.assertEqual(call.call_count,2)
