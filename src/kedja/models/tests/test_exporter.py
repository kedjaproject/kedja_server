from unittest import TestCase

from pyramid import testing
from pyramid.request import apply_request_extensions

from kedja.models.appmaker import root_populator


def _fixture(config):
    content = config.registry.content
    root = content('Root')
    root['wall'] = wall = content('Wall', rid=2)
    wall['collection'] = collection = content('Collection', rid=3)
    collection['card'] = content('Card', rid=4)
    collection['card2'] = content('Card', rid=5)
    return root


class ExporterTests(TestCase):

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
        from kedja.models.exporter import export_structure
        return export_structure

    def test_export_single_resource(self):
        root = _fixture(self.config)
        card = root['wall']['collection']['card']
        request = testing.DummyRequest()
        apply_request_extensions(request)
        self.config.begin(request)
        data = self._fut(card, request)
        self.assertEqual([{'type_name': 'Card', 'rid': 4, 'data': {'int_indicator': -1, 'title': '- Untiled -'}}], data)

    def test_export_resource_tree(self):
        root = _fixture(self.config)
        card = root['wall']
        request = testing.DummyRequest()
        apply_request_extensions(request)
        self.config.begin(request)
        data = self._fut(card, request)
        self.assertEqual(
            [{'contained': [{'contained': [{'data': {'int_indicator': -1,
                                                     'title': '- Untiled -'},
                                            'rid': 4,
                                            'type_name': 'Card'},
                                           {'data': {'int_indicator': -1,
                                                     'title': '- Untiled -'},
                                            'rid': 5,
                                            'type_name': 'Card'}],
                             'data': {'title': ''},
                             'rid': 3,
                             'type_name': 'Collection'}],
              'data': {'title': ''},
              'rid': 2,
              'type_name': 'Wall'}]
            , data)
