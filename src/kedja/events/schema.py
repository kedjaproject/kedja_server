from pyramid.threadlocal import get_current_registry
from zope.interface import implementer, Interface

from kedja.interfaces import ISchemaBound
from kedja.interfaces import ISchemaCreated


__all__ = ()


class _SchemaBaseEvent(object):

    def __init__(self, schema, registry = None, **kw):
        self.schema = schema
        if registry is None:
            registry = get_current_registry()
        self.registry = registry
        self.__dict__.update(kw)
        self.kw = kw


@implementer(ISchemaCreated)
class SchemaCreated(_SchemaBaseEvent):
    __doc__ = ISchemaCreated.__doc__


@implementer(ISchemaBound)
class SchemaBound(_SchemaBaseEvent):
    __doc__ = ISchemaBound.__doc__
