import sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
try:import benchmark_dev as bench
except ImportError:bench=None
class BenchmarkSafetyTests(unittest.TestCase):
    def test_temporary_edit_restores_bytes_and_timestamps_on_failure(self):
        self.assertIsNotNone(bench)
        with tempfile.TemporaryDirectory() as d:
            source=Path(d);name='Telegram/SourceFiles/leaf.cpp';p=source/name;p.parent.mkdir(parents=True);p.write_bytes(b'int leaf(){return 1;}\n');old=p.stat()
            with self.assertRaises(RuntimeError):
                with bench.temporary_change(source,[name],comment=True):
                    self.assertNotEqual(p.read_bytes(),b'int leaf(){return 1;}\n');raise RuntimeError('simulated failed compile')
            self.assertEqual(p.read_bytes(),b'int leaf(){return 1;}\n');self.assertEqual(p.stat().st_mtime_ns,old.st_mtime_ns)
            with self.assertRaises(ValueError):
                with bench.temporary_change(source,['../outside.cpp']):pass
    def test_failed_benchmark_does_not_claim_restoration_without_verification(self):
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);source=root/'source';source.mkdir();evidence=root/'evidence'
            # Initial verification passes; case-start verification then detects drift.
            with patch.object(bench.bp,'verify_source',side_effect=[None,ValueError('drift'),ValueError('drift')]):
                with self.assertRaises(ValueError):bench.benchmark(source,evidence)
            import json
            report=json.loads((evidence/'summary.json').read_text())
            self.assertEqual(report['status'],'FAILED');self.assertFalse(report['source_restored'])
    def test_final_restoration_verification_failure_is_raised(self):
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);source=root/'source';source.mkdir()
            for name in ('intro/intro_start.cpp','boxes/about_box.cpp','intro/intro_start.h','platform/linux/specific_linux.cpp'):
                p=source/'Telegram/SourceFiles'/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text('// original\n')
            calls=[0]
            def verify(*args):
                calls[0]+=1
                if calls[0]==13:raise ValueError('Restoration drift')
            values=[dict(duration_seconds=1,recompiled=n,link_seconds=1,build_tree_delta_bytes=0) for n in (0,1,2,2,1,1)]
            with patch.object(bench.bp,'verify_source',side_effect=verify),patch.object(bench.bp,'build',side_effect=values):
                with self.assertRaises(ValueError):bench.benchmark(source,root/'evidence')
