from unittest import TestCase

from kedja.security import WALL_OWNER
from kedja.testing import get_settings
from pyramid import testing
from zope.interface.verify import verifyObject

from kedja.interfaces import IWall


class WallTests(TestCase):

    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    @property
    def _cut(self):
        from kedja.resources.wall import Wall
        return Wall

    def test_interface(self):
        obj = self._cut()
        self.assertTrue(verifyObject(IWall, obj))

    def test_get_relations(self):
        obj = self._cut()
        obj.relations_map[100] = [1,2]
        self.assertEqual(obj.relations, [{'relation_id': 100, 'members': [1,2]}])

    def test_set_relations(self):
        obj = self._cut()
        obj.relations_map[100] = [1,2]
        # Existing relations will be cleared
        obj.relations = [{'relation_id': 10, 'members': [5,6]}]
        self.assertEqual(obj.relations, [{'relation_id': 10, 'members': [5,6]}])


class SetRoleFromAuthenticatedTests(TestCase):

    def setUp(self):
        self.config = testing.setUp(settings=get_settings())
        self.config.include('kedja.testing')
        self.config.include('kedja.resources.wall')
        self.config.testing_securitypolicy(userid='10')

    def tearDown(self):
        testing.tearDown()

    def test_set_role_from_authenticated(self):
        from kedja.resources.root import Root
        from kedja.resources.wall import Wall
        request = testing.DummyRequest()
        self.config.begin(request)
        root = Root()
        root['wall'] = wall = Wall()

        self.assertEqual({WALL_OWNER}, wall.get_roles(10))
