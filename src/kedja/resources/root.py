import colander
from kedja.core.folder import Folder
from kedja.core.rid_map import ResourceIDMap
from zope.interface import implementer

from kedja.resources.mixins import JSONRenderable
from kedja.resources.security import SecurityAwareMixin
from kedja.interfaces import IRoot
from kedja.permissions import MANAGE_TEMPLATES
from kedja.permissions import MANAGE_ROLES
from kedja import _
from kedja.core.permissions import Permissions


class RootSchema(colander.Schema):
    title = colander.SchemaNode(
        colander.String(),
        title=_("Title"),
        validator=colander.Length(min=5, max=100),
        missing=colander.drop,
    )

    def after_bind(self, node, kw):
        """ Use this instead of deferred, since cornice can't handle schema binding. """
        pass


@implementer(IRoot)
class Root(Folder, JSONRenderable, SecurityAwareMixin):
    """ Application root - created once. """
    acl_name = 'root'
    title = ""

    def __init__(self):
        super().__init__()
        self.rid = 1
        self.rid_map = ResourceIDMap(self)


ROOT_PERMISSIONS = Permissions(Root)
ROOT_PERMISSIONS.add(MANAGE_TEMPLATES, MANAGE_ROLES)


def includeme(config):
    config.add_content(Root)
    config.add_default_schema(Root, RootSchema)
    config.add_permissions(ROOT_PERMISSIONS)
