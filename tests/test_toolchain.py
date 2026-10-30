import hashlib,json,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
try:
    import toolchain
except ImportError:
    toolchain=None

class ToolchainTests(unittest.TestCase):
    def test_pinned_inputs_and_local_copy_are_fail_closed(self):
        self.assertIsNotNone(toolchain)
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);f=p/'Dockerfile';f.write_text('FROM scratch\nCOPY --from=dep /cache /\n')
            recipe={'inputs':{'Dockerfile':hashlib.sha256(f.read_bytes()).hexdigest()}}
            toolchain.verify_inputs(p,recipe)
            f.write_text('FROM scratch\nCOPY private-api-config /\n')
            with self.assertRaises(ValueError):toolchain.verify_inputs(p,recipe)
            recipe['inputs']['Dockerfile']=hashlib.sha256(f.read_bytes()).hexdigest()
            with self.assertRaises(ValueError):toolchain.verify_inputs(p,recipe)

    def test_https_mirror_override_is_transport_only_and_requires_exact_anchor(self):
        self.assertIsNotNone(toolchain)
        original=b'dnf -y install epel-release\ndnf config-manager --set-enabled powertools\ndnf -y install gcc-toolset-15-gcc\n'
        result=toolchain.epel_https(original)
        self.assertIn(b'https://dl.fedoraproject.org/pub/epel/',result)
        self.assertIn(b'dnf -y install gcc-toolset-15-gcc',result)
        with self.assertRaises(ValueError):toolchain.epel_https(b'changed upstream step')

    def test_save_archive_requires_every_layer_and_matching_config_digest(self):
        import io,tarfile
        config=json.dumps({'rootfs':{'diff_ids':['sha256:'+hashlib.sha256(b'layer').hexdigest()]}}).encode()
        image='sha256:'+hashlib.sha256(config).hexdigest()
        def fixture(layer=b'layer',unsafe=False):
            buf=io.BytesIO()
            entries={image[7:]+'.json':config,'layer/layer.tar':layer,'manifest.json':json.dumps([{'Config':image[7:]+'.json','Layers':['layer/layer.tar']}]).encode()}
            if unsafe:entries['../escape']=b'no'
            with tarfile.open(fileobj=buf,mode='w') as t:
                for name,data in entries.items():
                    m=tarfile.TarInfo(name);m.size=len(data);t.addfile(m,io.BytesIO(data))
            buf.seek(0);return buf
        self.assertEqual(toolchain.verify_save(fixture(),image)['layers'],1)
        with self.assertRaises(ValueError):toolchain.verify_save(fixture(b'tampered'),image)
        with self.assertRaises(ValueError):toolchain.verify_save(fixture(unsafe=True),image)

    def test_oci_index_id_is_not_confused_with_native_config_and_gzip_layers(self):
        import gzip,io,tarfile
        def blob(value):
            data=json.dumps(value,separators=(',',':')).encode();return 'sha256:'+hashlib.sha256(data).hexdigest(),data
        raw=b'native layer';compressed=gzip.compress(raw);ld='sha256:'+hashlib.sha256(compressed).hexdigest()
        cd,config=blob({'architecture':'amd64','os':'linux','rootfs':{'diff_ids':['sha256:'+hashlib.sha256(raw).hexdigest()]}})
        md,manifest=blob({'schemaVersion':2,'config':{'digest':cd},'layers':[{'digest':ld}]})
        expected,index=blob({'schemaVersion':2,'manifests':[{'digest':md,'platform':{'os':'linux','architecture':'amd64'}}]})
        entries={'blobs/sha256/'+d[7:]:data for d,data in [(expected,index),(md,manifest),(cd,config),(ld,compressed)]}
        entries['manifest.json']=json.dumps([{'Config':'blobs/sha256/'+cd[7:],'Layers':['blobs/sha256/'+ld[7:]]}]).encode()
        b=io.BytesIO()
        with tarfile.open(fileobj=b,mode='w') as t:
            for name,data in entries.items():
                m=tarfile.TarInfo(name);m.size=len(data);t.addfile(m,io.BytesIO(data))
        b.seek(0);result=toolchain.verify_save(b,expected)
        self.assertEqual(result['image_id'],expected);self.assertEqual(result['config_digest'],cd)

class CompatibilityTests(unittest.TestCase):
    def test_changed_compiler_or_qt_is_not_silently_accepted(self):
        recipe={'expected_compatibility':{'gcc':'15.2.1','qt':'6.11.2'}}
        self.assertTrue(toolchain.compatible({'versions':{'gcc':'15.2.1','qt':'6.11.2'}},recipe))
        with self.assertRaises(ValueError):toolchain.compatible({'versions':{'gcc':'15.3.0','qt':'6.11.2'}},recipe)
        with self.assertRaises(ValueError):toolchain.compatible({'versions':{'gcc':'15.2.1','qt':'6.12.0'}},recipe)

class RegistryRecoveryTests(unittest.TestCase):
    def test_explicit_remote_verification_does_not_accept_a_cached_only_result(self):
        from unittest.mock import patch,Mock
        lock={'image_id':'sha256:'+'1'*64,'config_digest':'sha256:'+'2'*64,'registry_reference':'invalid-registry'}
        with patch.object(Path,'read_text',return_value=json.dumps(lock)),patch.object(toolchain.subprocess,'run',return_value=Mock(returncode=0)):
            self.assertEqual(toolchain.restore_registry()['status'],'already_cached')
            with self.assertRaises(ValueError):toolchain.restore_registry(verify_remote=True)

class OfficialQtInspectionTests(unittest.TestCase):
    def test_cmake_qt_install_without_pkgconfig_is_inspectable(self):
        import contextlib,io
        from unittest.mock import patch
        versions={'g++':'15.2.1','cmake':'cmake version 3.26.5','ninja':'1.13.2','qmake':'6.11.2','ld.lld':'LLD 21.1.8'}
        def execute(args,**kwargs):
            if args[:3]==['docker','image','inspect']:return json.dumps([{'Id':'sha256:'+'1'*64,'Size':30,'Config':{'Env':[]}}])
            if args[:2]==['docker','run']:
                code='\n'.join(args[-1].splitlines()[1:-1]);output=io.StringIO()
                with contextlib.redirect_stdout(output),patch.object(Path,'iterdir',return_value=iter(())):exec(code,{})
                return output.getvalue()
            if args[0] not in versions:raise FileNotFoundError('Official static Qt has no pkg-config metadata')
            return versions[args[0]]+'\n'
        with patch.object(toolchain.subprocess,'check_output',side_effect=execute):
            self.assertEqual(toolchain.inspect('pinned')['versions']['qt'],'6.11.2')

class DefaultRecoveryRoutingTests(unittest.TestCase):
    def test_missing_image_never_starts_a_dependency_rebuild(self):
        from unittest.mock import patch,Mock
        with tempfile.TemporaryDirectory() as d,patch.object(toolchain.subprocess,'run',return_value=Mock(returncode=1)),patch.object(Path,'read_text',return_value=json.dumps({'image_id':'sha256:'+'1'*64})):
            with self.assertRaises(ValueError):toolchain.restore_pinned(Path(d))
