from zope.interface import implementer

from kedja.core.mutator import Mutator
from kedja.interfaces import IResource
from kedja.utils import init_schema


@implementer(IResource)
class ResourceMixin(object):
    __doc__ = IResource.__doc__
    __name__ = None
    __parent__ = None

    def get_rid(self, default=None) -> int:
        try:
            return self._rid
        except AttributeError:
            return

    def set_rid(self, rid:int):
        self._rid = rid

    def del_rid(self):
        self._rid = None

    rid = property(get_rid, set_rid, del_rid)


class JSONRenderable(object):

    def __json__(self, request):
        schema_factory = request.get_default_schema(self)
        if schema_factory is None:
            appstruct = {}
        else:
            schema = init_schema(schema_factory, registry=request.registry, resource=self)
            with Mutator(self, schema, registry=request.registry) as m:
                appstruct = m.appstruct()
        return {'type_name': self.__class__.__name__, 'rid': self.rid, 'data': appstruct}
