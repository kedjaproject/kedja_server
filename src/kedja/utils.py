
from datetime import datetime

import pytz
from kedja.events import SchemaCreated
from pyramid.interfaces import INewRequest
from pyramid.threadlocal import get_current_registry
from redis import StrictRedis

from kedja.interfaces import INamedACL, IResource
from kedja.interfaces import IRole


def utcnow():
    return pytz.utc.localize(datetime.utcnow())


def get_redis_conn(registry=None):
    if registry is None:
        registry = get_current_registry()
    try:
        connection = registry.redis_conn
    except AttributeError:
        if registry.package_name == 'testing':
            # This is a unit test
            from fakeredis import FakeStrictRedis
            registry.redis_conn = connection = FakeStrictRedis()
        else:
            registry.redis_conn = connection = StrictRedis.from_url(registry.settings['kedja.redis_url'])
    return connection


def _redis_conn_rm(request):
    return get_redis_conn(request.registry)


def get_role(name='', registry=None):
    if registry is None:
        registry = get_current_registry()
    return registry.getUtility(IRole, name=str(name))


def get_acl(name='', registry=None):
    if registry is None:
        registry = get_current_registry()
    return registry.getUtility(INamedACL, name=name)


def get_valid_acls(resource, registry=None):
    if registry is None:
        registry = get_current_registry()
    for acl in registry.getAllUtilitiesRegisteredFor(INamedACL):
        if acl.usable_for(resource):
            yield acl


def inject_auth_header(config):

    def inject_header_subscriber(event):
        auth = event.request.params.get('Authorization', None)
        if auth:
            event.request.headers['Authorization'] = auth

    config.add_subscriber(inject_header_subscriber, INewRequest)


def validate_appstruct(schema, appstruct):
    serialized = schema.serialize(appstruct)
    return schema.deserialize(serialized)


def init_schema(SchemaFactory, registry=None, **kw):
    """ Initialize a schema class and send ISchemaCreated event. Also bind the schema with passed keywords."""
    if registry is None:
        registry = get_current_registry()
    schema = SchemaFactory()
    event = SchemaCreated(schema, registry=registry, **kw)
    registry.notify(event)
    # This bind will cause a ISchemaBound event to fire
    return schema.bind(registry=registry, **kw)


def get_resource_type(resource):
    # This might change later on
    return resource.__class__.__name__


def get_permission_name(resource:IResource, permission_type:str, registry=None):
    """
    :param resource: object to check permission type for
    :param permission_type: what kind of permission to look up, for instance 'Edit' -> 'Wall:Edit'
    :param registry:
    :return: The combined permission name to check against: '<content_type>:<permission_type>'
    """
    if registry is None:
        registry = get_current_registry()
    content_type = get_resource_type(resource)
    assert content_type in registry.content
    assert content_type in registry.permissions
    return registry.permissions[content_type][permission_type]
