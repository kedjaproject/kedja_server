from unittest import TestCase

from pyramid import testing
from pyramid.httpexceptions import HTTPNotFound

from kedja.resources.mixins import ResourceMixin


class DummyResource(testing.DummyResource, ResourceMixin):
    pass


class RIDMapTests(TestCase):


    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    @property
    def _cut(self):
        from kedja.core.rid_map import ResourceIDMap
        return ResourceIDMap

    def _fixture(self):
        root = DummyResource()
        root.rid_map = self._cut(root)
        return root

    def test_getitem(self):
        root = self._fixture()
        rid = root.get_rid()
        self.assertEqual(root.rid_map[rid], ("", ))
        root['n'] = new = DummyResource()
        rid = root.rid_map.add(new)
        self.assertEqual(root.rid_map[rid], ("", "n"))

    def test_delitem(self):
        root = self._fixture()
        rid = root.get_rid()
        self.assertIn(rid, root.rid_map)
        self.assertIn(("", ), root.rid_map.path_to_rid)
        del root.rid_map[rid]
        self.assertNotIn(rid, root.rid_map)
        self.assertNotIn(("", ), root.rid_map.path_to_rid)

    def test_get(self):
        root = self._fixture()
        rid = root.get_rid()
        self.assertEqual(root.rid_map.get(rid), ("", ))
        root['n'] = new = DummyResource()
        rid = root.rid_map.add(new)
        self.assertEqual(root.rid_map.get(rid), ("", "n"))

    def test_contains(self):
        root = self._fixture()
        root['n'] = new = DummyResource()
        rid = root.rid_map.add(new)
        self.assertIn(rid, root.rid_map)
        self.assertIn(("", "n"), root.rid_map)
        self.assertIn(new, root.rid_map)
        self.assertNotIn(None, root.rid_map)

    def test_get_rid(self):
        root = self._fixture()
        root['n'] = new = DummyResource()
        rid = root.rid_map.add(new)
        self.assertEqual(root.rid_map.get_rid(("", "n")), rid)

    def test_get_resource(self):
        root = self._fixture()
        root['n'] = new = DummyResource()
        rid = root.rid_map.add(new)
        self.assertEqual(new, root.rid_map.get_resource(rid))
        self.assertEqual(None, root.rid_map.get_resource(0))  # 0 will never exist

    def test_get_resource_or_404(self):
        root = self._fixture()
        self.assertRaises(HTTPNotFound, root.rid_map.get_resource_or_404, 0)
        rid = root.get_rid()
        self.assertEqual(root.rid_map.get_resource_or_404(rid), root)

    def test_get_new_rid(self):
        root = self._fixture()
        res = root.rid_map.new_rid()
        self.assertIsInstance(res, int)

    def test_add_creates_rid(self):
        root = self._fixture()
        root['n'] = new = DummyResource()
        self.assertIsNone(new.get_rid())
        root.rid_map.add(new)
        self.assertIsInstance(new.get_rid(), int)

    def test_add_not_attached(self):
        root = self._fixture()
        new = DummyResource()
        self.assertRaises(ValueError, root.rid_map.add, new)

    def test_add_duplicate_rid(self):
        root = self._fixture()
        root['n'] = new = DummyResource()
        first_rid = root.rid_map.add(new)
        other = DummyResource()
        other.set_rid(first_rid)
        root['other'] = other
        self.assertRaises(ValueError, root.rid_map.add, other)

    def test_add_same_path(self):
        root = self._fixture()
        root['n'] = new = DummyResource()
        new.set_rid(123)
        root.rid_map.add(new)
        del root.subs['n']
        new2 = DummyResource()
        new2.set_rid(456)
        root['n'] = new2
        self.assertRaises(ValueError, root.rid_map.add, new2)

    def test_add_wrong_object(self):
        root = self._fixture()
        self.assertRaises(TypeError, root.rid_map.add, object())

    def test_contained_rids(self):
        root = self._fixture()
        a = DummyResource()
        a.rid = 1
        b = DummyResource()
        b.rid = 2
        c = DummyResource()
        c.rid = 3
        other = DummyResource()
        other.rid = 100
        root['a'] = a
        a['b'] = b
        b['c'] = c
        root['other'] = other
        # Contained will be added too
        root.rid_map.add(a)
        root.rid_map.add(other)
        contained_rids = root.rid_map.contained_rids
        self.assertEqual(contained_rids(root), {1, 2, 3, 100})
        self.assertEqual(contained_rids(1), {2, 3})
        self.assertEqual(contained_rids(2), {3})
        self.assertEqual(contained_rids(3), set())
        self.assertEqual(contained_rids(b), {3})
        self.assertEqual(contained_rids(("", "a")), {2, 3})
