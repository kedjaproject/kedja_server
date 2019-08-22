from unittest import TestCase

from kedja.testing import get_settings
from pyramid import testing
from pyramid.request import apply_request_extensions
from transaction import commit
from webtest import TestApp


class FunctionalWallExportAPIViewTests(TestCase):

    def setUp(self):
        self.config = testing.setUp(settings=get_settings())
        self.config.include('kedja.testing')
        self.config.include('pyramid_tm')
        self.config.include('kedja.views.api.export')
        # FIXME: Actual test of security on export? :)
        self.config.testing_securitypolicy(permissive=True)

    def _fixture(self, request):
        from kedja import root_factory
        root = root_factory(request)
        content = self.config.registry.content
        root['wall'] = wall = content('Wall', rid=2)
        results = {}
        for i in range(1, 4):
            wall['col%s' % i] = collection = content('Collection', rid=i*10)
            results[collection.rid] = collection
            for j in range(1, 4):
                collection['card%s' % j] = card = content('Card', rid=j*100+i)
                results[card.rid] = card
        commit()
        return {'resources': results}

    def test_get_no_security(self):
        wsgiapp = self.config.make_wsgi_app()
        app = TestApp(wsgiapp)
        request = testing.DummyRequest()
        apply_request_extensions(request)
        self.config.begin(request)
        #content = self._fixture(request)
        self._fixture(request)
        response = app.get('/api/1/export/2', status=200)
        expected_response = [
            {'type_name': 'Wall', 'rid': 2, 'data': {'title': ''}, 'contained': [
            {'type_name': 'Collection', 'rid': 10, 'data': {'title': ''},
             'contained': [{'type_name': 'Card', 'rid': 101, 'data': {'title': '- Untiled -', 'int_indicator': -1}},
                           {'type_name': 'Card', 'rid': 201, 'data': {'title': '- Untiled -', 'int_indicator': -1}},
                           {'type_name': 'Card', 'rid': 301, 'data': {'title': '- Untiled -', 'int_indicator': -1}}]},
            {'type_name': 'Collection', 'rid': 20, 'data': {'title': ''},
             'contained': [{'type_name': 'Card', 'rid': 102, 'data': {'title': '- Untiled -', 'int_indicator': -1}},
                           {'type_name': 'Card', 'rid': 202, 'data': {'title': '- Untiled -', 'int_indicator': -1}},
                           {'type_name': 'Card', 'rid': 302, 'data': {'title': '- Untiled -', 'int_indicator': -1}}]},
            {'type_name': 'Collection', 'rid': 30, 'data': {'title': ''},
             'contained': [{'type_name': 'Card', 'rid': 103, 'data': {'title': '- Untiled -', 'int_indicator': -1}},
                           {'type_name': 'Card', 'rid': 203, 'data': {'title': '- Untiled -', 'int_indicator': -1}},
                           {'type_name': 'Card', 'rid': 303, 'data': {'title': '- Untiled -', 'int_indicator': -1}}]}]}
        ]
        self.assertEqual(response.json_body, expected_response)
