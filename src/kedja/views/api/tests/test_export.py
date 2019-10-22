from unittest import TestCase

from pyramid import testing
from pyramid.request import apply_request_extensions
from transaction import commit
from yaml import safe_load
from webtest import TestApp

from kedja.testing import get_settings


class FunctionalWallExportAPIViewTests(TestCase):

    def setUp(self):
        self.config = testing.setUp(settings=get_settings())
        self.config.include('kedja.testing')
        self.config.include('pyramid_tm')
        self.config.include('kedja.views.api.export_import')
        # FIXME: Actual test of security on export? :)
        self.config.testing_securitypolicy(permissive=True)

    def _fixture(self, request):
        from kedja import root_factory
        root = root_factory(request)
        from kedja.resources.wall import Wall
        from kedja.resources.collection import Collection
        from kedja.resources.card import Card

        root['wall'] = wall = Wall(rid=2, title="Hello wall")
        results = {}
        for i in range(1, 4):
            wall['col%s' % i] = collection = Collection(rid=i*10)
            results[collection.rid] = collection
            for j in range(1, 4):
                collection['card%s' % j] = card = Card(rid=j*100+i)
                results[card.rid] = card
        commit()

    def test_get_no_security(self):
        wsgiapp = self.config.make_wsgi_app()
        app = TestApp(wsgiapp)
        request = testing.DummyRequest()
        apply_request_extensions(request)
        self.config.begin(request)
        self._fixture(request)
        response = app.get('/api/1/export/2', status=200)
        data = safe_load(response.body)
        self.assertEqual(1, data['version'])
        self.assertEqual("Hello wall", data['title'])
        self.assertEqual('Wall', data['export']['type_name'])  # The wall
        self.assertEqual(3, len(data['export']['contained']))  # The collections
