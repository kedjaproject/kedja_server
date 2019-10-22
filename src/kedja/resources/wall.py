from types import GeneratorType

import colander
from kedja.core.folder import Folder
from pyramid.threadlocal import get_current_request
from zope.interface import implementer

from kedja import _, logger
from kedja.interfaces import IWall, IResourceAdded
from kedja.models.relations import RelationMap
from kedja.resources.mixins import JSONRenderable
from kedja.resources.security import SecurityAwareMixin
from kedja.security import WALL_OWNER
from kedja.permissions import INVITE
from kedja.permissions import VISIBILITY
from kedja.permissions import MANAGE_ROLES
from kedja.core.permissions import Permissions


class RelationSchema(colander.Schema):
    relation_id = colander.SchemaNode(colander.Int())
    members = colander.SchemaNode(
        colander.Sequence(), colander.SchemaNode(colander.Int())
    )


def generator_to_list(value):
    if isinstance(value, GeneratorType):
        return list(value)
    return value


class WallSchema(colander.Schema):
    title = colander.SchemaNode(
        colander.String(), title=_("Title"), missing=colander.drop
    )
    acl_name = colander.SchemaNode(
        colander.String(), title=_("Used ACL"), missing=colander.drop
    )
    relations = colander.SchemaNode(
        colander.Sequence(),
        RelationSchema(),
        missing=colander.drop,
        # FIXME: This require validators etc...
    )

    def after_bind(self, node, kw):
        """ Use this instead of deferred, since cornice can't handle schema binding. """


@implementer(IWall)
class Wall(Folder, JSONRenderable, SecurityAwareMixin):
    title = ""
    acl_name = "private_wall"

    def __init__(self, **kw):
        super().__init__(**kw)
        self.relations_map = RelationMap()
        self.order = ()  # Enable ordering

    @property
    def relations(self):
        return list(self.relations_map.get_all_as_json())

    @relations.setter
    def relations(self, value):
        self.relations_map.set_all_from_json(value)

    def relations_dict(self):
        return dict(self.relations_map)


WALL_PERMISSIONS = Permissions(Wall)
WALL_PERMISSIONS.add(INVITE, VISIBILITY, MANAGE_ROLES)


def set_wall_owner_from_authenticated(event):
    """ Some content types within the content registry has a specific attribute called ownership_role.
        It only exists so the currently logged in user will get that role automatically.

        This subscriber listens to IResourceAdded events which have ISecurityAware resources.
    """
    if event.request is None:
        request = get_current_request()
    else:
        request = event.request
    resource = event.resource
    try:
        userid = request.authenticated_userid
    except AttributeError:
        logger.exception("request not found, this is okay during unit tests")
        userid = None
    if userid:
        resource.add_user_roles(userid, WALL_OWNER)


def includeme(config):
    config.add_content(Wall)
    config.add_default_schema(Wall, WallSchema)
    config.add_permissions(WALL_PERMISSIONS)
    config.add_subscriber(set_wall_owner_from_authenticated, IResourceAdded, context=IWall)
