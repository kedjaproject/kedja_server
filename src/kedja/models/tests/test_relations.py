from unittest import TestCase

from kedja.models.appmaker import root_populator
from pyramid import testing
from pyramid.request import apply_request_extensions


class RelationsTests(TestCase):

    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    @property
    def _cut(self):
        from kedja.models.relations import RelationMap
        return RelationMap

    def test_setitem(self):
        map = self._cut()
        map[1] = (1, 2, 3)
        self.assertIn(1, map.relation_to_rids)
        self.assertIn(2, map.relation_to_rids[1])
        self.assertEqual(set(map.relation_to_rids[1]), set([1, 2, 3]))

    def test_del_cleans_up(self):
        map = self._cut()
        map[1] = (1, 2, 3)
        del map[1]
        self.assertFalse(len(map.relation_to_rids))
        self.assertFalse(len(map.rid_to_relations))

    def test_getitem(self):
        map = self._cut()
        map[1] = (1, 2, 3)
        self.assertEqual(set(map[1]), set([1, 2, 3]))

    def test_reset_relation(self):
        map = self._cut()
        map[1] = (1, 2, 3)
        map[1] = (5, 6)
        self.assertEqual(set(map.relation_to_rids[1]), set([5, 6]))

    def test_new_relation_id(self):
        map = self._cut()
        self.assertIsInstance(map.new_relation_id(), int)

    def test_find_relation(self):
        map = self._cut()
        map[1] = (1, 2, 3)
        map[2] = (2, 3)
        self.assertEqual(map.find_relations(1, 2, 3), {1})
        self.assertEqual(map.find_relations(3), {1, 2})
        self.assertEqual(map.find_relations(2, 3), {1, 2})
        self.assertEqual(map.find_relations(1, 2), {1})

    def test_find_relevant_relation_ids(self):
        map = self._cut()
        map[1] = (1, 2, 3)
        map[2] = (2, 3)
        self.assertEqual(map.find_relevant_relation_ids(1), {1})
        self.assertEqual(map.find_relevant_relation_ids(2), {1, 2})
        self.assertEqual(map.find_relevant_relation_ids(4), set())


class RelationsIntegrationTests(TestCase):

    def setUp(self):
        self.config = testing.setUp()
        self.config.include('kedja.testing.minimal')
        self.config.include('kedja.resources')
        self.config.include('kedja.models.relations')

    def tearDown(self):
        testing.tearDown()

    def _fixture(self):
        request = testing.DummyRequest()
        apply_request_extensions(request)
        from kedja.resources.root import Root
        from kedja.resources.wall import Wall
        from kedja.resources.collection import Collection
        from kedja.resources.card import Card
        root = Root()
        root_populator(root, request)
        root['wall'] = wall = Wall()
        wall['collection1'] = c1 = Collection(rid=10)
        c1['c1'] = Card(rid=11)
        c1['c2'] = Card(rid=12)
        c1['c3'] = Card(rid=13)
        wall['collection2'] = c2 = Collection(rid=20)
        c2['c1'] = Card(rid=21)
        c2['c2'] = Card(rid=22)
        c2['c3'] = Card(rid=23)
        return wall, request

    def test_card_removes_connections(self):
        wall, request = self._fixture()
        wall.relations_map[1] = [11, 21]
        del wall['collection1']['c1']
        self.assertNotIn(1, wall.relations_map)

    def test_collection_removes_connections(self):
        wall, request = self._fixture()
        wall.relations_map[1] = [11, 21]
        del wall['collection1']
        self.assertNotIn(1, wall.relations_map)
