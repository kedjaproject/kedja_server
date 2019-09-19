from datetime import datetime

from pyramid.interfaces import IRendererFactory


def datetime_adapter(obj, request):
    return obj.isoformat()


def roles_adapter(obj, request):
    return str(obj)


def includeme(config):
    """ Include rendering special objects. """
    from kedja.models.acl import Role

    json_renderer = config.registry.getUtility(IRendererFactory, name="json")
    json_renderer.add_adapter(datetime, datetime_adapter)
    json_renderer.add_adapter(Role, roles_adapter)
