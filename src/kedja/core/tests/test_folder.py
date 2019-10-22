from unittest import TestCase

from kedja.core.rid_map import ResourceIDMap
from pyramid import testing
from zope.interface.verify import verifyObject

from kedja.interfaces import IFolder
from kedja.interfaces import IResourceWillBeAdded
from kedja.interfaces import IResourceAdded
from kedja.interfaces import IResourceRemoved
from kedja.interfaces import IResourceWillBeRemoved


class FolderTests(TestCase):

    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    @property
    def _cut(self):
        from kedja.core.folder import Folder
        return Folder

    def _rid_map_fixture(self):
        from kedja.core.rid_map import ResourceIDMap
        root = self._cut()
        root.rid_map = ResourceIDMap(root)
        return root

    def _folder_fixture(self, root):
        order = ('a', 'b', 'c')
        for n in order:
            obj = self._cut(rid=order.index(n) + 1)
            root[n] = obj
        return order

    def test_iface(self):
        obj = self._cut()
        self.failUnless(verifyObject(IFolder, obj))

    def test_ordering(self):
        root = self._cut()
        order = self._folder_fixture(root)
        self.assertFalse(root.is_ordered())
        root.set_order(order)
        self.assertEqual(root.keys(), order)
        self.assertTrue(root.is_ordered())
        order = ('c', 'b', 'a')
        root.set_order(order)
        self.assertEqual(root.keys(), order)

    def test_get_order_rids(self):
        root = self._rid_map_fixture()
        order = self._folder_fixture(root)
        self.assertFalse(root.is_ordered())
        root.set_order(order)
        self.assertEqual(root.get_order_rids(), (1, 2, 3))
        self.assertTrue(root.is_ordered())
        order = ('c', 'b', 'a')
        root.set_order(order)
        self.assertEqual(root.get_order_rids(), (3, 2, 1))

    def test_get_order_rids_something_removed(self):
        root = self._rid_map_fixture()
        order = self._folder_fixture(root)
        self.assertFalse(root.is_ordered())
        root.set_order(order)
        self.assertEqual(root.get_order_rids(), (1, 2, 3))
        self.assertTrue(root.is_ordered())
        del root['b']
        self.assertEqual(root.get_order_rids(), (1, 3))

    def test_ordering_wrong_count(self):
        root = self._cut()
        order = self._folder_fixture(root)
        self.assertRaises(ValueError, root.set_order, ('a', 'b'))

    def test_ordering_wrong_names(self):
        root = self._cut()
        order = self._folder_fixture(root)
        self.assertRaises(ValueError, root.set_order, ('a', 'b', 'd'))

    def test_ordering_repeated_names(self):
        root = self._cut()
        order = self._folder_fixture(root)
        self.assertRaises(ValueError, root.set_order, ('a', 'b', 'a'))

    def test_remove_ordering(self):
        root = self._cut()
        order = self._folder_fixture(root)
        root.order = ['a', 'b', 'c']
        self.assertTrue(root.is_ordered())
        del root.order
        self.assertFalse(root.is_ordered())

    def test_iter(self):
        root = self._cut()
        order = self._folder_fixture(root)
        iter_keys = [x for x in root]
        self.assertEqual(set(order), set(iter_keys))

    def test_values_respect_ordering(self):
        root = self._cut()
        self._folder_fixture(root)
        order = ['c', 'b', 'a']
        self.assertEqual(set(root.values()), set([root[x] for x in order]))
        root.order = order
        self.assertEqual(root.values(), [root[x] for x in order])

    def test_items_respect_ordering(self):
        root = self._cut()
        self._folder_fixture(root)
        order = ['c', 'b', 'a']
        self.assertEqual(set(root.items()), set([(x, root[x]) for x in order]))
        root.order = order
        self.assertEqual(root.items(), [(x, root[x]) for x in order])

    def test_len(self):
        root = self._cut()
        self._folder_fixture(root)
        self.assertEqual(len(root), 3)

    def test_truthy_empty(self):
        obj = self._cut()
        self.assertTrue(bool(obj))

    def test_repr(self):
        obj = self._cut()
        self.assertEqual(repr(obj), "<kedja.core.folder.Folder object None at %#x>" % id(obj))

    def test_add(self):
        root = self._cut()
        root.add('a', self._cut())
        self.assertIn('a', root)
        root['b'] = self._cut()
        self.assertIn('b', root)
        self.assertEqual(set(root.keys()), {'a', 'b'})

    def test_add_already_attached_causes_error(self):
        root = self._cut()
        one = self._cut()
        root['one'] = one
        self.assertRaises(ValueError, root.add, 'two', one)

    def test_add_moving_and_duplicating_causes_eror(self):
        root = self._cut()
        self.assertRaises(ValueError, root.add, 'one', self._cut(), moving=True, duplicating=True)

    def test_duplicating_replaces_rid(self):
        root = self._rid_map_fixture()
        one = self._cut()
        one.rid = 1
        root['one'] = one
        root['newhome'] = newhome = self._cut()
        root.copy('one', newhome)
        self.assertNotEqual(newhome['one'].rid, 1)
        self.assertTrue(newhome['one'].rid)

    def test_copy_to_same_folder_with_same_name_error(self):
        root = self._rid_map_fixture()
        one = self._cut()
        one.rid = 1
        root['one'] = one
        self.assertRaises(ValueError, root.copy, 'one', root)

    def test_copy_to_same_with_new_name(self):
        pass

    def test_moving_updates_rid_map(self):
        root = self._rid_map_fixture()
        one = self._cut(rid=1)
        root['one'] = one
        self.assertEqual(root.rid_map.get(1), ("", "one"))
        root['newhome'] = newhome = self._cut()
        root.move('one', newhome)
        self.assertEqual(root.rid_map.get(1), ("", "newhome", "one"))
        self.assertNotIn('one', root)
        self.assertEqual(newhome['one'].rid, 1)

    def test_add_updates_ordering_if_ordered(self):
        root = self._rid_map_fixture()
        order = self._folder_fixture(root)
        root.order = order
        newobj = self._cut(rid=4)
        root['d'] = newobj
        self.assertEqual(root.order, ('a', 'b', 'c', 'd'))
        self.assertEqual(root.get_order_rids(), (1, 2, 3, 4))

    def test_add_event_will_be_added(self):
        L = []

        def subscriber(event):
            L.append(event)
            self.assertEqual(event.name, 'a')
            self.assertEqual(event.parent, root)
            self.assertIsNotNone(event.resource)
            self.assertIsNone(event.resource.__parent__)

        self.config.add_subscriber(subscriber, IResourceWillBeAdded)
        root = self._cut()
        root['a'] = self._cut()
        self.assertEqual(len(L), 1)

    def test_add_event_added(self):
        L = []

        def subscriber(event):
            L.append(event)
            self.assertEqual(event.name, 'a')
            self.assertEqual(event.parent, root)
            self.assertEqual(event.resource, root['a'])
            self.assertEqual(event.resource.__parent__, root)

        self.config.add_subscriber(subscriber, IResourceAdded)
        root = self._cut()
        root['a'] = self._cut()
        self.assertEqual(len(L), 1)

    def test_add_no_events(self):
        L = []
        def subscriber(event):
            L.append(event)
        self.config.add_subscriber(subscriber, IResourceAdded)
        root = self._cut()
        root.add('a', self._cut(), send_events=False)
        self.assertEqual(len(L), 0)

    def test_get(self):
        root = self._cut()
        root['1'] = one = self._cut()
        self.assertEqual(root.get('1'), one)
        self.assertIsNone(root.get('404'))
        marker = object()
        self.assertEqual(root.get('404', marker), marker)


class FolderContentsIntegrationTests(TestCase):
    """ A bunch of tests to make sure different nested structures are handled in a sane way.
        Much of it integration tests with the mapping system.
    """

    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    @property
    def _cut(self):
        from kedja.core.folder import Folder
        return Folder

    def _fixture(self):
        """ Create a root with a folder. The folder contains 2 other folders.
            Manipulating the folder called 'folder' should change the contained resources.
        """
        root = self._cut(rid=100)
        root.rid_map = ResourceIDMap(root)

        folder = self._cut(rid=1)
        root['folder'] = folder

        items = ('a', 'b')
        for n in items:
            obj = self._cut(rid=items.index(n) + 10)
            folder[n] = obj

        return root

    def test_moving(self):
        root = self._fixture()
        newfolder = self._cut(rid=200)
        root['newfolder'] = newfolder
        root.move('folder', newfolder, newname='movedhere')
        self.assertIn('movedhere', newfolder)
        self.assertNotIn('folder', root)
        rid_map = root.rid_map
        self.assertEqual(rid_map[1], ("", "newfolder", "movedhere"))
        self.assertEqual(rid_map[10], ("", "newfolder", "movedhere", "a"))
        self.assertEqual(rid_map[11], ("", "newfolder", "movedhere", "b"))

    def test_deleting(self):
        root = self._fixture()
        del root['folder']
        rid_map = root.rid_map
        self.assertIn(100, rid_map)
        # No removed rids still here
        self.assertNotIn(1, rid_map)
        self.assertNotIn(10, rid_map)
        self.assertNotIn(11, rid_map)

    def test_copy_to_same(self):
        root = self._fixture()
        root.copy('folder', root, newname='clone')
        # The new 'clone' should've brand new rids
        folder = root['folder']
        clone = root['clone']
        self.assertNotEqual(folder, clone)
        self.assertNotEqual(folder['a'], clone['a'])
        self.assertNotEqual(folder['b'], clone['b'])
        self.assertNotEqual(folder.rid, clone.rid)
        self.assertNotEqual(folder['a'].rid, clone['a'].rid)
        self.assertNotEqual(folder['b'].rid, clone['b'].rid)
        rid_map = root.rid_map
        self.assertEqual(rid_map[folder.rid], ("", "folder"))
        self.assertEqual(rid_map[clone.rid], ("", "clone"))
        self.assertEqual(rid_map[clone['a'].rid], ("", "clone", "a"))
        self.assertEqual(rid_map[clone['b'].rid], ("", "clone", "b"))

    def test_copy_to_other(self):
        root = self._fixture()
        root['newhome'] = newhome = self._cut()
        root.copy('folder', newhome)
        # The new 'clone' should've brand new rids
        folder = root['folder']
        self.assertIn('folder', newhome)
        clone = newhome['folder']
        self.assertNotEqual(folder, clone)
        self.assertNotEqual(folder['a'], clone['a'])
        self.assertNotEqual(folder['b'], clone['b'])
        self.assertNotEqual(folder.rid, clone.rid)
        self.assertNotEqual(folder['a'].rid, clone['a'].rid)
        self.assertNotEqual(folder['b'].rid, clone['b'].rid)
        rid_map = root.rid_map
        self.assertEqual(rid_map[folder.rid], ("", "folder"))
        self.assertEqual(rid_map[clone.rid], ("", "newhome", "folder"))
        self.assertEqual(rid_map[clone['a'].rid], ("", "newhome", "folder", "a"))
        self.assertEqual(rid_map[clone['b'].rid], ("", "newhome", "folder", "b"))

    def test_rename(self):
        root = self._fixture()
        root.rename('folder', 'newfolder')
        self.assertNotIn('folder', root)
        self.assertIn('newfolder', root)
        folder = root['newfolder']
        rid_map = root.rid_map
        self.assertEqual(rid_map[folder.rid], ("", "newfolder"))
        self.assertEqual(rid_map[folder['a'].rid], ("", "newfolder", "a"))
        self.assertEqual(rid_map[folder['b'].rid], ("", "newfolder", "b"))

    def test_add_with_attached_resources(self):
        root = self._fixture()
        newfolder = self._cut(rid=8)
        newfolder['a'] = new_a = self._cut(rid=9)
        root['newfolder'] = newfolder
        rid_map = root.rid_map
        self.assertIn(8, rid_map)
        self.assertIn(9, rid_map)
        self.assertEqual(rid_map[9], ("", "newfolder", "a"))


class FolderEventsIntegrationTests(TestCase):
    """ Make sure events has attributes from contained resources etc.
    """

    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    @property
    def _cut(self):
        from kedja.core.folder import Folder
        return Folder

    def _fixture(self):
        """ Create a root with a folder. The folder contains 2 other folders.
            Manipulating the folder called 'folder' should change the contained resources.
        """
        root = self._cut(rid=100)
        root.rid_map = ResourceIDMap(root)
        return root

    def test_event_added(self):
        L = []

        def subscriber(event):
            L.append(event)

        self.config.add_subscriber(subscriber, IResourceAdded)

        root = self._fixture()
        folder = self._cut(rid=1)
        child = self._cut(rid=2)
        folder.add('child', child, send_events=False)

        root['folder'] = folder
        self.assertEqual(len(L), 1)
        event = L[0]
        self.assertEqual(event.contained_rids, {2})

    def test_event_will_be_removed(self):
        L = []

        def subscriber(event):
            L.append(event)

        self.config.add_subscriber(subscriber, IResourceWillBeRemoved)

        root = self._fixture()
        folder = self._cut(rid=1)
        root.add('folder', folder, send_events=False)
        child = self._cut(rid=2)
        folder.add('child', child, send_events=False)
        root.remove('folder')
        self.assertEqual(len(L), 1)
        event = L[0]
        self.assertEqual(event.contained_rids, {2})
