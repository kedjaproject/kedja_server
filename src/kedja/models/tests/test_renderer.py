from unittest import TestCase

from pyramid import testing
from pyramid.renderers import render
from pyramid.request import apply_request_extensions


_fixture = {'hello': 'world', 'names': ['Some', 'Kedjas']}

_expected = \
"""hello: world
names:
- Some
- Kedjas
"""

class YamlRendererTests(TestCase):

    def setUp(self):
        self.config = testing.setUp()
        self.config.include('kedja.models.renderers')

    def tearDown(self):
        testing.tearDown()

    @property
    def _cut(self):
        from kedja.models.renderers import YamlRenderer
        return YamlRenderer

    def test_dict(self):
        obj = self._cut({})
        response = obj(_fixture, {'request': testing.DummyRequest()})
        self.assertEqual(_expected, response)

    def test_integration(self):
        request = testing.DummyRequest()
        response = render('yaml', _fixture, request=request)
        self.assertEqual(_expected, response)
