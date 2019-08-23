from unittest import TestCase

from pyramid import testing
from pyramid.request import apply_request_extensions
from pyramid.security import forget

from kedja.permissions import VIEW
from kedja.security import WALL_OWNER
from kedja.testing import TestingAuthenticationPolicy


class PrivateWallACLTests(TestCase):

    def setUp(self):
        self.config = testing.setUp()
        self.config.include('kedja.testing.minimal')
        self.config.include('kedja.config')
        self.config.include('kedja.security')
        self.config.include('kedja.security.default_acl')
        self.config.include('kedja.models')
        self.config.include('kedja.resources')
        self.config.set_authentication_policy(TestingAuthenticationPolicy(userid='10'))

    def tearDown(self):
        testing.tearDown()

    def _fixture(self):
        content = self.config.registry.content
        root = content('Root')
        root['wall'] = content('Wall', rid=2)
        return root['wall']

    def test_private_wall(self):
        request = testing.DummyRequest()
        apply_request_extensions(request)
        self.config.begin(request)
        wall = self._fixture()
        # Just to make sure
        self.assertIn(WALL_OWNER, wall.get_roles(10))
        self.assertTrue(request.registry.content.has_permission_type(wall, request, VIEW))

    def test_private_wall_unauthenticated(self):
        request = testing.DummyRequest()
        apply_request_extensions(request)
        self.config.begin(request)
        forget(request)  # Log out user
        # Just to make sure
        self.assertEqual(request.authenticated_userid, None)
        wall = self._fixture()
        self.assertFalse(request.registry.content.has_permission_type(wall, request, VIEW))


class PublicWallACLTests(TestCase):

    def setUp(self):
        self.config = testing.setUp()
        self.config.include('kedja.testing.minimal')
        self.config.include('kedja.config')
        self.config.include('kedja.security')
        self.config.include('kedja.security.default_acl')
        self.config.include('kedja.models')
        self.config.include('kedja.resources')
        self.config.set_authentication_policy(TestingAuthenticationPolicy(userid='10'))

    def tearDown(self):
        testing.tearDown()

    def _fixture(self):
        content = self.config.registry.content
        root = content('Root')
        root['wall'] = content('Wall', rid=2, acl_name='public_wall')
        return root['wall']

    def test_public_wall_unauthenticated(self):
        request = testing.DummyRequest()
        apply_request_extensions(request)
        self.config.begin(request)
        forget(request)  # Log out user
        # Just to make sure
        self.assertEqual(request.authenticated_userid, None)
        wall = self._fixture()
        self.assertTrue(request.registry.content.has_permission_type(wall, request, VIEW))
