import colander
from kedja.core.folder import Folder
from kedja.core.permissions import Permissions
from zope.interface import implementer

from kedja import _
from kedja.interfaces import ICard
from kedja.resources.mixins import JSONRenderable


class CardSchema(colander.Schema):
    title = colander.SchemaNode(
        colander.String(),
        title=_("Title"),
        missing=colander.drop,
    )
    int_indicator = colander.SchemaNode(
        colander.Int(),
        title=_("Simple value for indicator"),
        missing=colander.drop,
    )

    def after_bind(self, node, kw):
        """ Use this instead of deferred, since cornice can't handle schema binding. """
        pass


@implementer(ICard)
class Card(Folder, JSONRenderable):
    title = ""
    int_indicator = -1

    def __init__(self, **kw):
        super().__init__(**kw)
        self.order = ()  # Enable ordering


CARD_PERMISSIONS = Permissions(Card)


def includeme(config):
    config.add_content(Card)
    config.add_default_schema(Card, CardSchema)
    config.add_permissions(CARD_PERMISSIONS)
