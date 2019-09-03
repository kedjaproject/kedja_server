from types import GeneratorType

import colander
from arche.folder import Folder
from arche.content import ContentType
from zope.interface import implementer

from kedja import _
from kedja.interfaces import IWall
from kedja.models.relations import RelationMap
from kedja.resources.json import JSONRenderable
from kedja.resources.security import SecurityAwareMixin
from kedja.security import WALL_OWNER
from kedja.permissions import INVITE
from kedja.permissions import VISIBILITY


class RelationSchema(colander.Schema):
    relation_id = colander.SchemaNode(
        colander.Int(),
    )
    members = colander.SchemaNode(
        colander.Sequence(),
        colander.SchemaNode(
            colander.Int(),
        )
    )


def generator_to_list(value):
    if isinstance(value, GeneratorType):
        return list(value)
    return value


class WallSchema(colander.Schema):
    title = colander.SchemaNode(
        colander.String(),
        title=_("Title"),
        missing=colander.drop,
    )
    acl_name = colander.SchemaNode(
        colander.String(),
        title=_("Used ACL"),
        missing=colander.drop,
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
    acl_name = 'private_wall'

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


WallContent = ContentType(factory=Wall, schema=WallSchema, title=_("Wall"), ownership_role=WALL_OWNER)
WallContent.add_permission_type(INVITE)
WallContent.add_permission_type(VISIBILITY)
WallPerms = WallContent.permissions


def includeme(config):
    config.add_content(WallContent)
