from unittest import TestCase

from pyramid import testing
from pyramid.request import apply_request_extensions
from transaction import commit
from webtest import TestApp

from kedja.testing import get_settings


_expected = \
"""- contained:
  - contained:
    - data:
        int_indicator: -1
        title: ''
      rid: 101
      type_name: Card
    - data:
        int_indicator: -1
        title: ''
      rid: 201
      type_name: Card
    - data:
        int_indicator: -1
        title: ''
      rid: 301
      type_name: Card
    data:
      title: ''
    rid: 10
    type_name: Collection
  - contained:
    - data:
        int_indicator: -1
        title: ''
      rid: 102
      type_name: Card
    - data:
        int_indicator: -1
        title: ''
      rid: 202
      type_name: Card
    - data:
        int_indicator: -1
        title: ''
      rid: 302
      type_name: Card
    data:
      title: ''
    rid: 20
    type_name: Collection
  - contained:
    - data:
        int_indicator: -1
        title: ''
      rid: 103
      type_name: Card
    - data:
        int_indicator: -1
        title: ''
      rid: 203
      type_name: Card
    - data:
        int_indicator: -1
        title: ''
      rid: 303
      type_name: Card
    data:
      title: ''
    rid: 30
    type_name: Collection
  data:
    title: ''
  rid: 2
  type_name: Wall
"""


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
        self._fixture(request)
        response = app.get('/api/1/export/2', status=200)
        self.assertEqual(response.json_body, _expected)
