import os
from shutil import copyfile
from tempfile import TemporaryDirectory
from unittest import TestCase

from pyramid import testing
from zope.interface.verify import verifyObject

from kedja.interfaces import ITemplateFileUtil


def get_dummy_structure_fp():
    here = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(here, 'testing_fixtures', '123.yaml')


class TemplateFileUtilTests(TestCase):

    def setUp(self):
        # FIXME: Create temp dir?
        self.tmpdir = TemporaryDirectory()
        copyfile(get_dummy_structure_fp(), os.path.join(self.tmpdir.name, '123.yaml'))
        settings = {
            'kedja.templates_dir': self.tmpdir.name
        }
        self.config = testing.setUp(settings=settings)

    def tearDown(self):
        self.tmpdir.cleanup()
        testing.tearDown()

    @property
    def _cut(self):
        from kedja.models.template import TemplateFileUtil
        return TemplateFileUtil

    def test_get_existing_filestems(self):
        obj = self._cut(self.config.registry)
        self.assertEqual(['123'], obj.get_existing_filestems())

    def test_get_all_appstructs(self):
        obj = self._cut(self.config.registry)
        result = list(obj.get_all_appstructs())
        self.assertEqual(1, len(result))
        self.assertEqual(123, result[0]['id'])

    def test_read_appstruct(self):
        obj = self._cut(self.config.registry)
        result = obj.read_appstruct('123')
        self.assertEqual(result['id'], 123)

    def test_write(self):
        obj = self._cut(self.config.registry)
        appstruct = {
            'version': 1,
            'id': 1000,
            'data': {},
            'title': 'Hello world!',
            'export': []
        }
        result = obj.write(appstruct)
        self.assertEqual('1000', result)
        read_data = obj.read_appstruct(result)
        self.assertEqual(1000, read_data['id'])
        self.assertEqual('Hello world!', read_data['title'])

    def test_remove(self):
        obj = self._cut(self.config.registry)
        obj.remove('123')
        self.assertEqual([], obj.get_existing_filestems())

    def test_integration(self):
        self.config.include('kedja.models.template')
        util = self.config.registry.queryUtility(ITemplateFileUtil)
        self.assertIsNotNone(util)

    def test_iface(self):
        obj = self._cut(self.config.registry)
        self.failUnless(verifyObject(ITemplateFileUtil, obj))
