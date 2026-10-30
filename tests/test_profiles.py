import json,sys,tempfile,unittest
from unittest import mock
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
try:import build_profile as bp
except ImportError:bp=None

class ProfileTests(unittest.TestCase):
    def test_dev_removes_image_lto_and_keeps_optimized_release(self):
        self.assertIsNotNone(bp)
        flags='-g -gdwarf64 -gz -O3 -flto=auto -ffat-lto-objects -pipe -fhardened'
        result=bp.dev_flags(flags)
        self.assertNotIn('-flto',result);self.assertNotIn('-ffat-lto-objects',result)
        self.assertIn('-O3',result);self.assertIn('-g1',result);self.assertIn('-fno-lto',result)
        self.assertIn('-fhardened',result)

    def test_build_states_are_distinct_and_symlinks_rejected(self):
        self.assertIsNotNone(bp)
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);(p/'out').mkdir()
            self.assertEqual(bp.directory(p,'production'),p/'out')
            self.assertEqual(bp.directory(p,'dev-fast'),p/'out/dev-fast')
            (p/'out/dev-fast').symlink_to(p/'out')
            with self.assertRaises(ValueError):bp.directory(p,'dev-fast')

    def test_directory_policy_rejects_drift_before_docker_or_writes(self):
        original=bp.load()
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);source=root/'source';source.mkdir()
            (root/'D1_CONFIG.json').write_text((bp.ROOT/'D1_CONFIG.json').read_text())
            for profile,bad in [('dev-fast','out'),('dev-fast','out/Release'),('dev-fast','out/other'),('production','out/dev-fast')]:
                with self.subTest(profile=profile,directory=bad):
                    value=json.loads(json.dumps(original));value[profile]['directory']=bad
                    (root/'BUILD_PROFILES.json').write_text(json.dumps(value))
                    with mock.patch.object(bp,'ROOT',root),mock.patch.object(bp,'image_id') as image:
                        with self.assertRaisesRegex(ValueError,'directory policy'):bp.load()
                        with self.assertRaisesRegex(ValueError,'directory policy'):bp.command(source,'configure')
                        image.assert_not_called()
                    self.assertFalse((source/'out').exists())

    def test_effective_dev_flags_reject_hidden_lto_and_updater(self):
        self.assertIsNotNone(bp)
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);p.joinpath('CMakeCache.txt').write_text('CMAKE_BUILD_TYPE:STRING=Release\nDESKTOP_APP_DISABLE_AUTOUPDATE:BOOL=ON\n')
            graph='build Jerkgram: CXX_EXECUTABLE_LINKER__Telegram_Release obj.o\n  FLAGS = -O3 -DNDEBUG -g1 -fno-lto\n  LINK_FLAGS = -fno-lto -fno-use-linker-plugin -fuse-ld=lld\n  LINK_LIBRARIES = libQt6Core.a libQt6Gui.a libQt6Widgets.a\n\n'
            p.joinpath('build.ninja').write_text(graph);self.assertTrue(bp.check_dev_configuration(p))
            p.joinpath('build.ninja').write_text(graph+'  FLAGS = -flto=auto -O3\n')
            with self.assertRaises(ValueError):bp.check_dev_configuration(p)
            p.joinpath('build.ninja').write_text(graph);p.joinpath('CMakeCache.txt').write_text('CMAKE_BUILD_TYPE:STRING=Release\nDESKTOP_APP_DISABLE_AUTOUPDATE:BOOL=OFF\n')
            with self.assertRaises(ValueError):bp.check_dev_configuration(p)

    def test_standard_runner_is_not_assumed_to_fit_production_lto(self):
        self.assertIsNotNone(bp)
        with self.assertRaises(ValueError):bp.production_resources(16.8*2**30,3.2*2**30,92*2**30)
        self.assertTrue(bp.production_resources(64*2**30,0,100*2**30))
        self.assertTrue(bp.production_resources(30.12*2**30,15*2**30,100*2**30))

class CMakeDevFixtureTests(unittest.TestCase):
    def test_supported_cache_seed_and_optimized_native_incremental_configuration(self):
        import os,shutil,subprocess
        if not all(shutil.which(x) for x in ('cmake','ninja','g++')):self.skipTest('CMake fixture runs on GitHub/pinned toolchain when host tools absent')
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);src=p/'src';src.mkdir();old=p/'production';old.mkdir();out=p/'dev'
            (old/'CMakeCache.txt').write_text('TDESKTOP_API_ID:STRING=12345\nTDESKTOP_API_HASH:STRING='+'a'*32+'\nTDESKTOP_API_TEST:BOOL=OFF\n')
            (src/'CMakeLists.txt').write_text('cmake_minimum_required(VERSION 3.25)\nproject(Fixture LANGUAGES CXX)\nadd_executable(Jerkgram main.cpp)\n')
            (src/'main.cpp').write_text('int main(){return 0;}\n')
            seed=Path(__file__).resolve().parents[1]/'cmake/reuse_credentials.cmake'
            env=dict(os.environ,JERKGRAM_PRODUCTION_OUT=str(old),CXXFLAGS=bp.dev_flags('-O3 -g -flto=auto -ffat-lto-objects'))
            proc=subprocess.run(['cmake','-S',str(src),'-B',str(out),'-G','Ninja','-DCMAKE_BUILD_TYPE=Release','-DCMAKE_INTERPROCEDURAL_OPTIMIZATION=OFF','-DCMAKE_EXPORT_COMPILE_COMMANDS=ON','-C',str(seed)],env=env,capture_output=True,text=True)
            self.assertEqual(proc.returncode,0,proc.stdout+proc.stderr)
            command=json.loads((out/'compile_commands.json').read_text())[0]['command']
            self.assertNotIn('-flto=',command);self.assertNotIn('-ffat-lto',command);self.assertIn('-O3',command);self.assertIn('-DNDEBUG',command)
            subprocess.run(['cmake','--build',str(out)],check=True,capture_output=True)
            again=subprocess.run(['cmake','--build',str(out)],check=True,capture_output=True,text=True)
            self.assertIn('no work to do',again.stdout.lower())

class NinjaLogMeasurementTests(unittest.TestCase):
    def test_log_compaction_does_not_hide_new_compile_or_link_records(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);old='10\t20\t100\told.cpp.o\ta\n';new='0\t8\t200\tleaf.cpp.o\tb\n8\t25\t201\tJerkgram\tc\n'
            (p/'.ninja_log').write_text('# ninja log v7\n'+old*100)
            checkpoint=bp.ninja_snapshot(p)
            (p/'.ninja_log').write_text('# ninja log v7\n'+old+new)
            records=bp.ninja_records(p,checkpoint)
            self.assertEqual([r['output'] for r in records],['leaf.cpp.o','Jerkgram'])
