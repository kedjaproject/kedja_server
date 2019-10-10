import os
from json import dumps
from shutil import copyfile
from tempfile import TemporaryDirectory
from unittest import TestCase

from kedja.interfaces import ITemplateFileUtil
from pyramid import testing
from pyramid.request import apply_request_extensions
from transaction import commit
from webtest import TestApp

from kedja.testing import get_settings


def get_dummy_structure_fp():
    here = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(here, 'testing_fixtures', '123.yaml')


class FunctionalTemplatesAPIViewTests(TestCase):

    def setUp(self):
        self.tmpdir = TemporaryDirectory()
        copyfile(get_dummy_structure_fp(), os.path.join(self.tmpdir.name, '123.yaml'))
        settings = get_settings()
        settings['kedja.templates_dir'] = self.tmpdir.name
        self.config = testing.setUp(settings=settings)
        self.config.include('kedja.testing')
        self.config.include('pyramid_tm')
        self.config.include('kedja.views.api.templates')
        # FIXME: Actual test of security? :)
        self.config.testing_securitypolicy(permissive=True)

    def tearDown(self):
        self.tmpdir.cleanup()
        testing.tearDown()

    def _fixture(self, request):
        from kedja import root_factory
        root = root_factory(request)
        commit()
        return root

    def test_get(self):
        wsgiapp = self.config.make_wsgi_app()
        app = TestApp(wsgiapp)
        request = testing.DummyRequest()
        apply_request_extensions(request)
        self.config.begin(request)
        self._fixture(request)
        response = app.get('/api/1/templates/123', status=200)
        data = response.json_body
        self.assertEqual(1, data['version'])
        self.assertEqual("Hello from template", data['title'])
        self.assertEqual(2, len(data['export']['contained']))  # The collections

    def test_get_404(self):
        wsgiapp = self.config.make_wsgi_app()
        app = TestApp(wsgiapp)
        request = testing.DummyRequest()
        apply_request_extensions(request)
        self.config.begin(request)
        self._fixture(request)
        response = app.get('/api/1/templates/404nope', status=404)
        self.assertEqual(404, response.status_int)

    def test_get_bad_name(self):
        wsgiapp = self.config.make_wsgi_app()
        app = TestApp(wsgiapp)
        request = testing.DummyRequest()
        apply_request_extensions(request)
        self.config.begin(request)
        self._fixture(request)
        app.get('/api/1/templates/..123', status=404)

    def test_post(self):
        wsgiapp = self.config.make_wsgi_app()
        app = TestApp(wsgiapp)
        request = testing.DummyRequest()
        apply_request_extensions(request)
        self.config.begin(request)
        root = self._fixture(request)
        response = app.post('/api/1/templates/123', status=200)
        data = response.json_body
        self.assertEqual('Wall', data['type_name'])
        wall = root[str(data['rid'])]
        self.assertEqual('En annan', wall.title)

    def test_collection_get(self):
        wsgiapp = self.config.make_wsgi_app()
        app = TestApp(wsgiapp)
        request = testing.DummyRequest()
        apply_request_extensions(request)
        self.config.begin(request)
        self._fixture(request)
        response = app.get('/api/1/templates', status=200)
        data = response.json_body
        self.assertEqual(1, len(data))
        self.assertEqual(1, data[0]['version'])
        self.assertEqual("Hello from template", data[0]['title'])

    def test_collection_post(self):
        wsgiapp = self.config.make_wsgi_app()
        app = TestApp(wsgiapp)
        self.config.include('kedja.models.template')
        request = testing.DummyRequest()
        apply_request_extensions(request)
        self.config.begin(request)
        root = self._fixture(request)
        tpl_util = self.config.registry.getUtility(ITemplateFileUtil)
        appstruct = tpl_util.read_appstruct('123')
        from kedja.models.export_import import import_structure
        # Wall will be created with a new rid
        wall = import_structure(root, request, appstruct['export'])
        commit()
        body = dumps({'rid': wall.rid, 'title': 'My new template'})
        response = app.post('/api/1/templates', status=200, params=body)
        data = response.json_body
        self.assertEqual('My new template', data['title'])
        self.assertEqual(2, len(list(tpl_util.get_all_appstructs())))
