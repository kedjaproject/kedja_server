from pyramid.decorator import reify
from pyramid.threadlocal import get_current_request
from pyramid.threadlocal import get_current_registry
from zope.interface import implementer
from zope.interface.interfaces import ObjectEvent

from kedja.interfaces import (
    IResourceEvent,
    IResourceWillBeAdded,
    IResourceAdded,
    IResourceWillBeRemoved,
    IResourceRemoved,
    IResourceUpdated,
)


__all__ = ()


@implementer(IResourceEvent)
class ResourceEvent(ObjectEvent):
    __doc__ = IResourceEvent.__doc__

    def __init__(
        self,
        resource,
        parent=None,
        name: str = None,
        duplicating=None,
        moving=None,
        contained_rids=None,
        request=None,
        registry=None,
        **kw
    ):
        self.resource = resource
        self.parent = parent
        self.name = name
        self.duplicating = duplicating
        self.moving = moving
        self._request = request
        self._registry = registry
        self.__dict__.update(**kw)

    @property
    def context(self):
        return self.resource

    @reify
    def request(self):
        """ Fetch current request if it doesn't already exist within the event. Will cache the result. """
        if self._request is None:
            return get_current_request()
        return self._request

    @reify
    def registry(self):
        """ Fetch current registry if it doesn't already exist within the event. Will cache the result. """
        if self._registry is None:
            return get_current_registry()
        return self._registry


@implementer(IResourceWillBeAdded)
class ResourceWillBeAdded(ResourceEvent):
    __doc__ = IResourceWillBeAdded.__doc__


@implementer(IResourceAdded)
class ResourceAdded(ResourceEvent):
    __doc__ = IResourceAdded.__doc__

    def __init__(self, resource, contained_rids: set = None, **kw):
        self.contained_rids = contained_rids
        super().__init__(resource, **kw)


@implementer(IResourceWillBeRemoved)
class ResourceWillBeRemoved(ResourceEvent):
    __doc__ = IResourceWillBeRemoved.__doc__

    def __init__(self, resource, contained_rids: set = None, **kw):
        self.contained_rids = contained_rids
        super().__init__(resource, **kw)


@implementer(IResourceRemoved)
class ResourceRemoved(ResourceEvent):
    __doc__ = IResourceRemoved.__doc__


@implementer(IResourceUpdated)
class ResourceUpdated(ResourceEvent):
    __doc__ = IResourceUpdated.__doc__

    def __init__(self, resource, changed=(), **kw):
        self.changed = set(changed)
        super().__init__(resource, **kw)
