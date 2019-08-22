from unittest import TestCase

from pyramid import testing
from pyramid.request import apply_request_extensions

from kedja.models.appmaker import root_populator


def _fixture(config):
    content = config.registry.content
    root = content('Root')
    return root


# Use same data as exporter
_data = {'contained': {'contained': {'data': {'int_indicator': -1,
                                              'title': 'Hello from Card'},
                                     'rid': 4,
                                     'type_name': 'Card'},
                       'data': {'title': ''},
                       'rid': 3,
                       'type_name': 'Collection'},
         'data': {'title': ''},
         'rid': 2,
         'type_name': 'Wall'}


_data_single = {
    'data': {'title': 'Hello world'},
    'rid': 2,
    'type_name': 'Wall'
}


class ImporterTests(TestCase):

    def setUp(self):
        self.config = testing.setUp()
        self.config.include('kedja.testing.minimal')
        self.config.include('kedja.resources.root')
        self.config.include('kedja.resources.wall')
        self.config.include('kedja.resources.collection')
        self.config.include('kedja.resources.card')

    def tearDown(self):
        testing.tearDown()

    @property
    def _fut(self):
        from kedja.models.importer import import_structure
        return import_structure

    def test_import_single_resource(self):
        root = _fixture(self.config)
        request = testing.DummyRequest()
        apply_request_extensions(request)
        self.config.begin(request)
        self._fut(root, request, _data_single)
        self.assertIn('2', root)
        self.assertEqual(root['2'].title, 'Hello world')
        self.assertEqual(root['2'].rid, 2)

    def test_import_resource_tree(self):
        root = _fixture(self.config)
        request = testing.DummyRequest()
        apply_request_extensions(request)
        self.config.begin(request)
        self._fut(root, request, _data)
        self.assertEqual(root['2']['3']['4'].title, "Hello from Card")
