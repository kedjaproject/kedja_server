import colander
from kedja.core.folder import Folder
from zope.interface import implementer

from kedja import _
from kedja.interfaces import ICollection
from kedja.resources.mixins import JSONRenderable
from kedja.core.permissions import Permissions


class CollectionSchema(colander.Schema):
    title = colander.SchemaNode(
        colander.String(),
        title=_("Title"),
        missing=colander.drop,
    )

    def after_bind(self, node, kw):
        """ Use this instead of deferred, since cornice can't handle schema binding. """
        pass


@implementer(ICollection)
class Collection(Folder, JSONRenderable):
    title = ""

    def __init__(self, **kw):
        super().__init__(**kw)
        self.order = ()  # Enable ordering


COLLECTION_PERMISSIONS = Permissions(Collection)


def includeme(config):
    config.add_content(Collection)
    config.add_default_schema(Collection, CollectionSchema)
    config.add_permissions(COLLECTION_PERMISSIONS)
