"""
The colander function after_bind enables modifications to a schema after it's bound.
However, this only works for the package that first created the schema. We're patching the method
here to allow more than one plugin to have a say by firing a zope event instead.

That way several different packages may subscribe to the after_bind event instead.

The event will fire for each node, regardless of after_bind methods present.

Any original after_bind methods will of course work as expected.
"""
from pyramid.threadlocal import get_current_registry

from kedja.events import SchemaBound


def bind(self, **kw):
    """"
    Patched bind that also sends an event with the cloned node

    Default description: Resolve any deferred values attached to this schema node
    and its children (recursively), using the keywords passed as
    ``kw`` as input to each deferred value.  This function
    *clones* the schema it is called upon and returns the cloned
    value.  The original schema node (the source of the clone)
    is not modified."""
    cloned = self.clone()
    cloned._bind(kw)
    event = SchemaBound(cloned, **kw)
    event.registry.notify(event)
    return cloned


def includeme(config):
    from colander import _SchemaNode
    _SchemaNode.bind = bind
