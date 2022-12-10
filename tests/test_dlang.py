from django.test import TestCase
from django.test.utils import ContextList
from django.template.context import Context, RequestContext
from django_optimizer.dlang import loader
from django.conf import settings
from os.path import join, sep, split, exists
# Create your tests here.
class DLangTest(TestCase):
    def setUp(self, *args, **kwargs):
        settings.DYNAMIC_ROOT = settings.BASE_DIR / 'django_optimizer/tests/dynamic/'
        settings.STATIC_ROOT = settings.BASE_DIR / 'django_optimizer/tests/static/'
        self.test_context:RequestContext = self.client.request().context[0]

    def test_loadfile(self, *args,**kwargs):
        filepath = "example.dcss"
        filenamespace = "username"
        dlang_file = loader.LoadFile(path=filepath, context={
            "test_bg": "red",
            "author": "Esteban Chacon Martin"
        }, namespace=filenamespace)
        dlang_file.process()
        self.assertTrue(dlang_file.get_static_path() == join(settings.STATIC_ROOT, filenamespace, filepath.replace("dcss", "css")))
        
    
    def test_loadfile_context(self, *args, **kwargs):
        filepath = "example.dcss"
        filenamespace = "username"
        self.test_context.update({
            "test_bg": "red",
            "author": "Esteban Chacon Martin"
        })
        dlang_file = loader.LoadFile(path=filepath, context=self.test_context, namespace=filenamespace)
        dlang_file.process()
        self.assertTrue(dlang_file.get_static_path() == join(settings.STATIC_ROOT, filenamespace, filepath.replace("dcss", "css")))
    
    def test_if_block(self, *args, **kwargs):
        filepath = "example.dcss"
        filenamespace = "username"
        self.test_context.update({
            "test_bg": "red",
            "author": "Esteban Chacon Martin",
            "coordinates":{
                "x": 100,
                "y": 1000,
                "z": 10000
            }
        })
        dlang_file = loader.LoadFile(path=filepath, context=self.test_context, namespace=filenamespace)
        dlang_file.process()
        self.assertTrue(dlang_file.get_static_path() == join(settings.STATIC_ROOT, filenamespace, filepath.replace("dcss", "css")))
      

    def test_in_app_dynamic_file(self, *args, **kwargs):
        filepath = "/clients/light/css/base.dcss"
        filenamespace = "username"
        dlang_file = loader.LoadFile(path=filepath, context=self.test_context, namespace=filenamespace)
        dlang_file.process()
        path, basename = split(filepath.replace("dcss", "css").removeprefix(sep))
        self.assertTrue(exists(dlang_file.get_static_path()))

    def test_supported_dynamic(self, *args, **kwargs):
        self.assertTrue(loader.LoadFile.is_dynamic("some/path/file.dcss"))
        self.assertTrue(loader.LoadFile.is_dynamic("some/path/file.djs"))
        self.assertTrue(loader.LoadFile.is_dynamic("file.dcss"))
        self.assertFalse(loader.LoadFile.is_dynamic("some/path/dcss"))
        self.assertFalse(loader.LoadFile.is_dynamic("some/path/djs"))
        self.assertFalse(loader.LoadFile.is_dynamic("some/path/css"))
        self.assertFalse(loader.LoadFile.is_dynamic("some/path/file.css"))
        self.assertFalse(loader.LoadFile.is_dynamic("dcss"))

    def test_multiple_is_dynamic(self, *args, **kwargs):
        filepath = "example.dcss"
        filenamespace = "username"
        dlang_file = loader.LoadFile(path=filepath, context={
            "test_bg": "red",
            "author": "Esteban Chacon Martin"
        }, namespace=filenamespace)
        dlang_file.process()
        self.assertTrue(dlang_file.is_dynamic)
        self.assertTrue(dlang_file.__class__.is_dynamic(filepath))
