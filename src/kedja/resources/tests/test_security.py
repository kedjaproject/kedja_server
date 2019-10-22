from unittest import TestCase

from kedja.exceptions import RoleNotAllowedHere
from pyramid import testing
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.security import ALL_PERMISSIONS, Everyone, Deny, Allow, DENY_ALL
from zope.interface.verify import verifyObject

from kedja.interfaces import ISecurityAware
from kedja.testing import TestingAuthenticationPolicy


class SecurityAwareMixinTests(TestCase):

    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    @property
    def _resource(self):
        from kedja.core.folder import Folder
        from kedja.resources.security import SecurityAwareMixin

        class DummySecurityAware(Folder, SecurityAwareMixin):
            acl_name = ""

        return DummySecurityAware

    @property
    def _named_acl(self):
        from kedja.core.acl import NamedACL
        return NamedACL

    @property
    def _Role(self):
        from kedja.core.acl import Role
        return Role

    def _fixture(self):
        self.config.include('kedja.core')

        # Roles
        ADMIN = self._Role('Admin')
        USER = self._Role('User')
        OWNER = self._Role('Owner')
        self.config.add_role(ADMIN)
        self.config.add_role(USER)
        self.config.add_role(OWNER)

        # ACL fixture
        parent_acl = self._named_acl('parent')
        parent_acl.add_allow('Admin', ['edit', 'comment', 'delete'])
        parent_acl.add_allow('User', 'comment')
        parent_acl.add_allow(Everyone, 'view')

        child_acl = self._named_acl('child')
        child_acl.add_allow('Owner', ['edit', 'delete'])
        self.config.add_acl(parent_acl)
        self.config.add_acl(child_acl)

        # Fixture
        parent = self._resource(acl_name='parent')
        child = self._resource(acl_name='child')
        parent['c'] = child
        parent.add_user_roles(1, 'Admin')
        parent.add_user_roles(2, 'User')
        child.add_user_roles(3, 'Owner')
        return parent

    def test_interface(self):
        resource = self._resource()
        self.failUnless(verifyObject(ISecurityAware, resource))

    def test_add_user_roles(self):
        self.config.include('kedja.core')
        self.config.add_role(self._Role('a'))
        self.config.add_role(self._Role('b'))
        self.config.add_role(self._Role('c'))
        self.config.add_role(self._Role('d'))
        obj = self._resource()
        self.assertEqual(set(), obj.get_roles(1))
        obj.add_user_roles(1, 'a', 'b', 'c')
        self.assertEqual({'a', 'b', 'c'}, obj.get_roles(1))
        obj.add_user_roles('1', 'c', 'd')
        self.assertEqual({'a', 'b', 'c', 'd'}, obj.get_roles(1))

    def test_add_user_roles_not_allowed_in_context(self):
        self.config.include('kedja.core')
        self.config.add_role(self._Role('NotHere', required=[]))
        obj = self._resource()
        self.assertEqual(set(), obj.get_roles(1))
        self.assertRaises(RoleNotAllowedHere, obj.add_user_roles, 1, 'NotHere')

    def test_remove_user_roles(self):
        self.config.include('kedja.core')
        obj = self._resource()
        self.assertEqual(set(), obj.get_roles(1))
        self.config.add_role(self._Role('a'))
        self.config.add_role(self._Role('b'))
        self.config.add_role(self._Role('c'))
        obj.add_user_roles(1, 'a', 'b', 'c')
        self.assertEqual({'a', 'b', 'c'}, obj.get_roles(1))
        obj.remove_user_roles(1, 'c', 'd')
        self.assertEqual({'a', 'b'}, obj.get_roles(1))
        obj.remove_user_roles('1', 'b', 'd')
        self.assertEqual({'a'}, obj.get_roles(1))

    def test_remove_user_roles_dont_die_on_key_error(self):
        obj = self._resource()
        self.assertEqual(set(), obj.get_roles(1))
        obj.remove_user_roles(1, 'c', 'd')

    def test_remove_all_user_roles(self):
        self.config.include('kedja.core')
        obj = self._resource()
        self.assertEqual(set(), obj.get_roles(1))
        self.config.add_role(self._Role('a'))
        obj.add_user_roles(1, 'a')
        self.assertEqual({'a'}, obj.get_roles(1))
        obj.remove_user_roles(1, 'a')
        self.assertEqual(set(), obj.get_roles(1))

    def test_get_computed_acl(self):
        self.config.include('kedja.core')
        self.config.add_role(self._Role('role'))
        named_acl = self._named_acl('test_acl')
        named_acl.add_allow('role', ['perm-one', 'perm-two'])
        self.config.add_acl(named_acl)
        obj = self._resource(acl_name='test_acl')
        request = testing.DummyRequest()
        obj.add_user_roles(1, 'role')
        self.assertEqual([(Deny, Everyone, ALL_PERMISSIONS)], list(obj.get_computed_acl(['2'], request)))
        # As string too
        self.assertEqual([(Deny, Everyone, ALL_PERMISSIONS)], list(obj.get_computed_acl('2', request)))
        self.assertEqual(
            [(Allow, '1', ('perm-one', 'perm-two')), (Deny, Everyone, ALL_PERMISSIONS)],
            list(obj.get_computed_acl(['1'], request))
        )

    def test_get_computed_acl_several(self):
        parent = self._fixture()
        request = testing.DummyRequest()
        self.assertEqual(
            list(parent.get_computed_acl([1, 2, 3], request)),
            [
                (Allow, '1', ('edit', 'comment', 'delete')),
                (Allow, '2', ('comment',)),
                (Allow, Everyone, ('view',)),
                (Deny, Everyone, ALL_PERMISSIONS),
            ]
        )

    def test_get_computed_acl_broken_acl(self):
        parent = self._fixture()
        child = parent['c']
        child.acl_name = '404'
        request = testing.DummyRequest()
        # Simply the parents ACL
        self.assertEqual(
            list(child.get_computed_acl([1, 2, 3], request)),
            [
                (Allow, '1', ('edit', 'comment', 'delete')),
                (Allow, '2', ('comment',)),
                (Allow, Everyone, ('view',)),
                (Deny, Everyone, ALL_PERMISSIONS),
            ]
        )

    def test_get_roles_map(self):
        parent = self._fixture()
        self.assertEqual({'1': {'Admin'}, '2': {'User'}}, parent.get_roles_map([1, 2, 3]))
        child = parent['c']
        self.assertEqual({'3': {'Owner'}}, child.get_roles_map([1, 2, 3]))

    def test_get_acl(self):
        parent = self._fixture()
        acl = parent.get_acl()
        self.assertEqual(
            [
                ('Allow', 'Admin', ('edit', 'comment', 'delete')),
                ('Allow', 'User', ('comment',)),
                ('Allow', 'system.Everyone', ('view',))
            ],
            acl
        )

    def test_get_acl_nothing_registered(self):
        parent = self._fixture()
        parent.acl_name = ''
        self.assertEqual(None, parent.get_acl())

    def test_acl_method(self):
        self.config.testing_securitypolicy(userid='2')
        request = testing.DummyRequest()
        self.config.begin(request)
        parent = self._fixture()
        self.assertEqual(
            [
                (Allow, '2', ('comment',)),
                (Allow, 'system.Everyone', ('view',)),
                DENY_ALL
            ],
            list(parent.__acl__())
        )

    def test_integration(self):
        parent = self._fixture()
        self.config.include('kedja.testing')
        self.config.set_authentication_policy(TestingAuthenticationPolicy(userid='2'))
        request = testing.DummyRequest()
        self.config.begin(request)
        self.assertTrue(request.has_permission('comment', parent))
        self.assertTrue(request.has_permission('view', parent))
        self.assertFalse(request.has_permission('edit', parent))

    def test_get_simplified_permissions(self):
        parent = self._fixture()
        self.config.set_authorization_policy(ACLAuthorizationPolicy())
        self.config.set_authentication_policy(TestingAuthenticationPolicy(userid='1'))
        request = testing.DummyRequest()
        self.config.begin(request)
        response = parent.get_simplified_permissions(request)
        # Handle lists
        response['allowed'] = set(response['allowed'])
        response['denied'] = set(response['denied'])
        self.assertEqual(
            {'all_other_allowed': False,
             'allowed': {'edit', 'view', 'delete', 'comment'},
             'denied': set()},
            response
        )

    def test_get_simplified_permissions_with_deny(self):
        parent = self._fixture()
        self.config.set_authorization_policy(ACLAuthorizationPolicy())
        self.config.set_authentication_policy(TestingAuthenticationPolicy(userid='1'))
        request = testing.DummyRequest()
        self.config.begin(request)
        acl = parent.get_acl()
        acl.insert(0, (Deny, 'Admin', ['Badness']))
        response = parent.get_simplified_permissions(request)
        # Handle lists
        response['allowed'] = set(response['allowed'])
        response['denied'] = set(response['denied'])
        self.assertEqual(
            {'all_other_allowed': False,
             'allowed': {'edit', 'view', 'delete', 'comment'},
             'denied': {'Badness'}},
            response
        )

    def test_get_simplified_permissions_with_deny_and_allow_all(self):
        parent = self._fixture()
        self.config.set_authorization_policy(ACLAuthorizationPolicy())
        self.config.set_authentication_policy(TestingAuthenticationPolicy(userid='1'))
        request = testing.DummyRequest()
        self.config.begin(request)
        acl = parent.get_acl()
        acl.insert(0, (Deny, 'Admin', ['Badness']))
        acl.add_allow('Admin', ALL_PERMISSIONS)
        response = parent.get_simplified_permissions(request)
        # Handle lists
        response['allowed'] = set(response['allowed'])
        response['denied'] = set(response['denied'])
        self.assertEqual(
            {'all_other_allowed': True,
             'allowed': {'edit', 'view', 'delete', 'comment'},
             'denied': {'Badness'}},
            response
        )
