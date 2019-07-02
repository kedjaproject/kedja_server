from logging import getLogger

from arche.interfaces import IResourceAdded
from pyramid.decorator import reify
from pyramid.location import lineage
from pyramid.security import DENY_ALL

from BTrees.LOBTree import LOBTree
from BTrees.OOBTree import OOSet
from pyramid.threadlocal import get_current_request, get_current_registry
from zope.interface import implementer

from kedja.interfaces import INamedACL
from kedja.interfaces import ISecurityAware


logger = getLogger(__name__)


@implementer(ISecurityAware)
class SecurityAwareMixin(object):
    __doc__ = ISecurityAware.__doc__
    acl_name = ''

    @reify
    def _rolesdata(self):
        return LOBTree()

    def add_user_roles(self, userid:str, *roles):
        """ See kedja.interfaces.ISecurityAware """
        if isinstance(userid, str):
            userid = int(userid)
        if userid not in self._rolesdata:
            self._rolesdata[userid] = OOSet()
        self._rolesdata[userid].update(roles)

    def remove_user_roles(self, userid:str, *roles):
        """ See kedja.interfaces.ISecurityAware """
        if isinstance(userid, str):
            userid = int(userid)
        if userid not in self._rolesdata:
            return
        storage = self._rolesdata[userid]
        for k in roles:
            if k in storage:
                storage.remove(k)
        if not len(storage):
            del self._rolesdata[userid]

    def get_roles(self, userid):
        return set(self._rolesdata.get(int(userid), ()))

    def get_roles_map(self, userids):
        """ See kedja.interfaces.ISecurityAware """
        result = {}
        for userid in userids:
            roles = self.get_roles(userid)
            if roles:
                result[str(userid)] = roles
        return result

    def __acl__(self):
        """ See kedja.interfaces.ISecurityAware and Pyarmids docs on ACL/Security. """
        return self.get_computed_acl()

    def get_computed_acl(self, userids=[], request=None):
        """ See kedja.interfaces.ISecurityAware """
        if request is None:
            request = get_current_request()
        if not isinstance(userids, list):
            userids = [userids]
        if request.authenticated_userid and request.authenticated_userid not in userids:
            userids.insert(0, request.authenticated_userid)
        registry = request.registry
        for resource in lineage(self):
            if ISecurityAware. providedBy(resource):
                roles_map = resource.get_roles_map(userids)
                # Get ACL
                named_acl = resource.get_acl(registry)
                if named_acl is not None:
                    yield from named_acl.get_translated_acl(roles_map)
        # Finally, the stop bit!
        yield DENY_ALL

    def get_acl(self, registry=None):
        """ See kedja.interfaces.ISecurityAware """
        if registry is None:
            registry = get_current_registry()
        named_acl = registry.queryUtility(INamedACL, name=self.acl_name)
        if named_acl is None:
            logger.debug("%r found no ACL named %r", self, self.acl_name)
        else:
            logger.debug("%r returns acl %r", self, self.acl_name)
            return named_acl


def set_role_from_authenticated(event):
    """ Some content types within the content registry has a specific attribute called ownership_role.
        It only exists so the currently logged in user will get that role automatically.

        This subscriber listens to IResourceAdded events which have ISecurityAware resources.
    """
    resource = event.context
    type_name = getattr(resource, 'type_name', resource.__class__.__name__)
    ctype = event.registry.content[type_name]
    role = ctype.kwargs.get('ownership_role', None)
    if role is not None:
        try:
            userid = event.request.authenticated_userid
        except AttributeError:
            logger.exception("request not found, this is okay during unit tests")
            userid = None
        if userid:
            resource.add_user_roles(userid, role)


def includeme(config):
    config.add_subscriber(set_role_from_authenticated, IResourceAdded, context=ISecurityAware)
