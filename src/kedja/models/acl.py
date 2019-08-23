from collections import UserList
from collections import UserString
from logging import getLogger

from pyramid.security import Allow
from pyramid.security import Deny
from pyramid.security import Everyone
from pyramid.security import Authenticated
from pyramid.security import ALL_PERMISSIONS
from zope.interface import implementer, Interface

from kedja.interfaces import INamedACL, ISecurityAware
from kedja.interfaces import IRole

logger = getLogger(__name__)


@implementer(IRole)
class Role(UserString):

    def __init__(self, role_id: str, title: str = None, description: str = ""):
        super().__init__(role_id)
        if title is None:
            title = "role: %s" % role_id
        self.title = title
        self.description = description


@implementer(INamedACL)
class NamedACL(UserList):
    """ A simple object to keep track of abstract ACLs ment to describe permissions for different roles.
    """
    name = ""
    title = ""
    description = ""
    required = None

    def __init__(self, name: str = "", title: str = "", description: str = "", required = None):
        self.name = name
        self.title = title
        self.description = description
        if self.required is not None:
            self.add_required(required)
        super().__init__()

    def add_allow(self, ace_role, ace_permissions):
        return self._add(Allow, ace_role, ace_permissions)

    def add_deny(self, ace_role, ace_permissions):
        return self._add(Deny, ace_role, ace_permissions)

    def _add(self, ace_action, ace_role, ace_permissions):
        assert ace_action in (Allow, Deny)
        if not IRole.providedBy(ace_role) and ace_role not in (Everyone, Authenticated):
            logger.warning("%r is not a Role instance or Pyramids 'Everyone'/'Authenticated'", ace_role)
        if isinstance(ace_permissions, str):
            ace_permissions = (ace_permissions,)
        if ace_permissions is ALL_PERMISSIONS:
            pass
        elif not isinstance(ace_permissions, tuple):
            ace_permissions = tuple(ace_permissions)
        self.append((ace_action, ace_role, ace_permissions))

    def get_translated_acl(self, mapping):
        for (ace_action, ace_role, ace_permissions) in self:
            if ace_role in (Everyone, Authenticated):
                yield (ace_action, ace_role, ace_permissions)
            else:
                for (userid, roles_iter) in mapping.items():
                    assert isinstance(userid, str), "userid must be a string"
                    if ace_role in roles_iter:
                        yield (ace_action, userid, ace_permissions)

    def add_required(self, ifaces):
        """ Set a specific interface as a requirement to use this ACL.
            This is not enforced but can be used for UIs.
        """
        if self.required is None:
            self.required = set()
        if Interface.providedBy(ifaces):
            ifaces = [ifaces]
        self.required.extend(ifaces)

    def usable_for(self, resource):
        """ Check if this ACL can be used for 'resource'. """
        if self.required is None:
            return True
        for iface in self.required:
            if iface.providedBy(resource):
                return True
        return False

    def details_for(self, resource):
        """ Returns a dict with details for this acl. """
        assert ISecurityAware.providedBy(resource)
        return {
            'active': resource.acl_name == self.name,
            'name': self.name,
            'title': self.title,
            'description': self.description,
        }
