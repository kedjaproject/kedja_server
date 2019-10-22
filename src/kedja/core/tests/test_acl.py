from unittest import TestCase

from pyramid import testing
from pyramid.security import Allow, Deny, Everyone, Authenticated, ALL_PERMISSIONS
from zope.interface import Interface, implementer

from kedja.interfaces import IRoot


class IDummyResource(Interface):
    pass


@implementer(IDummyResource)
class DummyResource(testing.DummyResource):
    pass


class NamedACLTests(TestCase):

    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    @property
    def _cut(self):
        from kedja.core.acl import NamedACL
        return NamedACL

    @property
    def Role(self):
        from kedja.core.acl import Role
        return Role

    def test_add_allow(self):
        acl = self._cut('test')
        manager = self.Role('Manager')
        acl.add_allow(manager, ['filibuster', 'inspect'])
        self.assertEqual([(Allow, manager, ('filibuster', 'inspect'))], acl)

    def test_add_deny(self):
        acl = self._cut('test')
        manager = self.Role('Manager')
        acl.add_allow(manager, ['filibuster', 'inspect'])
        acl.add_deny(manager, 'spy')
        self.assertEqual(
            [
                (Allow, manager, ('filibuster', 'inspect')),
                (Deny, manager, ('spy',))
            ],
            acl)

    def test_translate_simple(self):
        acl = self._cut('test')
        manager = self.Role('Manager')
        other = self.Role('Other')
        acl.add_allow(manager, ['filibuster', 'inspect'])
        acl.add_deny(manager, 'spy')
        mapping = {'1': [manager, other], '2': [other]}
        self.assertEqual(tuple(acl.get_translated_acl(mapping)),
                         (('Allow', '1', ('filibuster', 'inspect')), ('Deny', '1', ('spy',))))

    def test_translate_with_pyramids_roles(self):
        acl = self._cut('test')
        manager = self.Role('Manager')
        other = self.Role('Other')
        acl.add_allow(manager, ['filibuster', 'inspect'])
        acl.add_allow(Authenticated, 'view')
        acl.add_deny(manager, 'spy')
        acl.add_deny(Everyone, 'edit')
        mapping = {'1': [manager, other], '2': [other]}

        expected = (
            ('Allow', '1', ('filibuster', 'inspect')),
            ('Allow', 'system.Authenticated', ('view',)),
            ('Deny', '1', ('spy',)),
            ('Deny', 'system.Everyone', ('edit',))
        )
        self.assertEqual(tuple(acl.get_translated_acl(mapping)), expected)

    def test_translate_all_permissions(self):
        acl = self._cut('test')
        manager = self.Role('Manager')
        acl.add_allow(manager, ALL_PERMISSIONS)

        mapping = {'1': [manager]}
        self.assertEqual(list(acl.get_translated_acl(mapping)),
                         [('Allow', '1', ALL_PERMISSIONS)])

    def test_required_as_none(self):
        acl = self._cut('Batman')
        self.assertTrue(acl.usable_for(object()))
        self.assertTrue(acl.usable_for(None))

    def test_required_as_iface(self):
        acl = self._cut('Batman', required=IDummyResource)
        self.assertFalse(acl.usable_for(object()))
        dummy = DummyResource()
        self.assertTrue(acl.usable_for(dummy))

    def test_required_as_list(self):
        acl = self._cut('Batman', required=[IRoot, IDummyResource])
        self.assertFalse(acl.usable_for(object()))
        dummy = DummyResource()
        self.assertTrue(acl.usable_for(dummy))

    def test_required_as_empty_list(self):
        acl = self._cut('Batman', required=[])
        self.assertFalse(acl.usable_for(object()))
        dummy = DummyResource()
        self.assertFalse(acl.usable_for(dummy))


class RoleTests(TestCase):

    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    @property
    def _cut(self):
        from kedja.core.acl import Role
        return Role

    def test_required_as_none(self):
        role = self._cut('Batman')
        self.assertTrue(role.assignable(object()))
        self.assertTrue(role.assignable(None))

    def test_required_as_iface(self):
        role = self._cut('Batman', required=IDummyResource)
        self.assertFalse(role.assignable(object()))
        dummy = DummyResource()
        self.assertTrue(role.assignable(dummy))

    def test_required_as_list(self):
        role = self._cut('Batman', required=[IRoot, IDummyResource])
        self.assertFalse(role.assignable(object()))
        dummy = DummyResource()
        self.assertTrue(role.assignable(dummy))

    def test_required_as_empty_list(self):
        role = self._cut('Batman', required=[])
        self.assertFalse(role.assignable(object()))
        dummy = DummyResource()
        self.assertFalse(role.assignable(dummy))
