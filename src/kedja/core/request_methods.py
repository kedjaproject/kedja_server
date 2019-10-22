from kedja.core import get_rid_map
from pyramid.interfaces import IRootFactory
from pyramid.traversal import find_root

from kedja.interfaces import IRoot
from kedja.interfaces import IResource


def _get_root(request):
    # This is a bit silly and redundant. But accessing the root from requests regardless of their state  might
    # be exactly what you want.
    rf = request.registry.queryUtility(IRootFactory)
    if rf is not None:
        return rf(request)
    else:
        context = getattr(request, 'context', None)
        if IResource.providedBy(context):
            root = find_root(context)
            if IRoot.providedBy(root):
                return root


def _get_rid_map(request):
    return get_rid_map(request.root)


def get_default_schema(request, resource):
    name = resource.__class__.__name__
    return request.registry.default_schemas.get(name)


def includeme(config):
    config.add_request_method(_get_root, name='root', reify=True)
    config.add_request_method(_get_rid_map, name='rid_map', reify=True)
    config.add_request_method(get_default_schema)
