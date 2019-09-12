from datetime import datetime

from pyramid.interfaces import IRendererFactory


def datetime_adapter(obj: datetime, request):
    return obj.isoformat()


def includeme(config):
    """ Include rendering for datetime objects. """
    json_renderer = config.registry.getUtility(IRendererFactory, name="json")
    json_renderer.add_adapter(datetime, datetime_adapter)
