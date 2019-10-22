import os
from unittest import TestCase

from pyramid import testing
from pyramid.request import apply_request_extensions

from kedja.resources.root import Root
from kedja.resources.card import Card
from kedja.resources.collection import Collection
from kedja.resources.wall import Wall


def _import_fixture(config):
    return Root()


def _export_fixture(config):
    root = Root()
    root["wall"] = wall = Wall(rid=2)
    wall["collection"] = collection = Collection(rid=3)
    collection["card"] = Card(rid=4)
    collection["card2"] = Card(rid=5)
    return root


# Use similar as exporter
_data = {
    "contained": [
        {
            "contained": [
                {
                    "data": {"int_indicator": -1, "title": "Hello from Card"},
                    "rid": 4,
                    "type_name": "Card",
                },
                {
                    "data": {"int_indicator": -1, "title": ""},
                    "rid": 5,
                    "type_name": "Card",
                },
            ],
            "data": {"title": ""},
            "rid": 3,
            "type_name": "Collection",
        }
    ],
    "data": {"acl_name": "private_wall", "relations": [], "title": ""},
    "rid": 2,
    "type_name": "Wall",
}


_data_single = {"data": {"title": "Hello world"}, "rid": 2, "type_name": "Wall"}


class ImporterTests(TestCase):
    def setUp(self):
        self.config = testing.setUp()
        self.config.include("kedja.testing.minimal")
        self.config.include("kedja.resources.root")
        self.config.include("kedja.resources.wall")
        self.config.include("kedja.resources.collection")
        self.config.include("kedja.resources.card")

    def tearDown(self):
        testing.tearDown()

    @property
    def _fut(self):
        from kedja.models.export_import import import_structure

        return import_structure

    def test_import_single_resource(self):
        root = _import_fixture(self.config)
        request = testing.DummyRequest()
        apply_request_extensions(request)
        self.config.begin(request)
        self._fut(root, request, _data_single, new_rids=False)
        self.assertIn("2", root)
        self.assertEqual(root["2"].title, "Hello world")
        self.assertEqual(root["2"].rid, 2)

    def test_import_resource_tree(self):
        root = _import_fixture(self.config)
        request = testing.DummyRequest()
        apply_request_extensions(request)
        self.config.begin(request)
        self._fut(root, request, _data, new_rids=False)
        self.assertEqual(root["2"]["3"]["4"].title, "Hello from Card")

    def test_dual_import_breaks(self):
        root = _import_fixture(self.config)
        request = testing.DummyRequest()
        apply_request_extensions(request)
        self.config.begin(request)
        self._fut(root, request, _data_single, new_rids=False)
        self.assertIn("2", root)
        self.assertRaises(
            KeyError, self._fut, root, request, _data_single, new_rids=False
        )

    def test_dual_import_with_new_rids(self):
        root = _import_fixture(self.config)
        request = testing.DummyRequest()
        apply_request_extensions(request)
        self.config.begin(request)
        self._fut(root, request, _data_single, new_rids=False)
        self.assertIn("2", root)
        self.assertEqual(1, len(root))
        self._fut(root, request, _data_single, new_rids=True)
        self.assertEqual(2, len(root))

    def test_import_complex_example(self):
        from kedja.models.template import TemplateFileUtil

        here = os.path.abspath(os.path.dirname(__file__))
        tpl_path = os.path.join(here, "testing_fixtures")
        self.config.registry.settings["kedja.templates_dir"] = tpl_path
        root = _import_fixture(self.config)
        request = testing.DummyRequest()
        apply_request_extensions(request)
        self.config.begin(request)
        tpl_util = TemplateFileUtil(self.config.registry)
        data = tpl_util.read_appstruct("123")
        self._fut(root, request, data["export"], new_rids=False)
        # Make sure it's possible to import the same structure twice and keep the relations
        self._fut(root, request, data["export"], new_rids=True)

    def test_import_complex_check_relations(self):
        from kedja.models.template import TemplateFileUtil

        here = os.path.abspath(os.path.dirname(__file__))
        tpl_path = os.path.join(here, "testing_fixtures")
        self.config.registry.settings["kedja.templates_dir"] = tpl_path
        root = _import_fixture(self.config)
        request = testing.DummyRequest()
        apply_request_extensions(request)
        self.config.begin(request)
        tpl_util = TemplateFileUtil(self.config.registry)
        data = tpl_util.read_appstruct("123")
        wall = self._fut(root, request, data["export"], new_rids=True)
        relations_dict = wall.relations_dict()
        # There's a relation called 5267045789483324 in the import
        for rid in relations_dict[5267045789483324]:
            self.assertIsNotNone(root.rid_map.get_resource(rid))


class ExporterTests(TestCase):
    def setUp(self):
        self.config = testing.setUp()
        self.config.include("kedja.testing.minimal")
        self.config.include("kedja.resources.root")
        self.config.include("kedja.resources.wall")
        self.config.include("kedja.resources.collection")
        self.config.include("kedja.resources.card")

    def tearDown(self):
        testing.tearDown()

    @property
    def _fut(self):
        from kedja.models.export_import import export_structure

        return export_structure

    def test_export_single_resource(self):
        root = _export_fixture(self.config)
        card = root["wall"]["collection"]["card"]
        request = testing.DummyRequest()
        apply_request_extensions(request)
        self.config.begin(request)
        data = self._fut(card, request)
        self.assertEqual(
            {"type_name": "Card", "rid": 4, "data": {"int_indicator": -1, "title": ""}},
            data,
        )

    def test_export_resource_tree(self):
        root = _export_fixture(self.config)
        request = testing.DummyRequest()
        apply_request_extensions(request)
        self.config.begin(request)
        data = self._fut(root["wall"], request)
        self.assertEqual(
            {
                "contained": [
                    {
                        "contained": [
                            {
                                "data": {"int_indicator": -1, "title": ""},
                                "rid": 4,
                                "type_name": "Card",
                            },
                            {
                                "data": {"int_indicator": -1, "title": ""},
                                "rid": 5,
                                "type_name": "Card",
                            },
                        ],
                        "data": {"title": ""},
                        "rid": 3,
                        "type_name": "Collection",
                    }
                ],
                "data": {"acl_name": "private_wall", "relations": [], "title": ""},
                "rid": 2,
                "type_name": "Wall",
            },
            data,
        )
