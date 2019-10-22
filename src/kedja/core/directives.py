from kedja.core.permissions import Permissions
from kedja.interfaces import INamedACL
from kedja.interfaces import IRole


def add_acl(config, acl: INamedACL):
    assert INamedACL.providedBy(acl)
    assert acl.name
    config.registry.registerUtility(acl, name=acl.name)


def add_role(config, role: IRole):
    assert IRole.providedBy(role)
    config.registry.registerUtility(role, name=str(role))


def add_content(config, content_type):
    config.registry.content.add(content_type)


def add_default_schema(config, content_type, schema_cls):
    reg = config.registry
    if not hasattr(reg, "default_schemas"):
        reg.default_schemas = {}
    if isinstance(content_type, str):
        name = content_type
    else:
        name = content_type.__name__
    reg.default_schemas[name] = schema_cls


def add_permissions(config, permissions: Permissions):
    assert isinstance(permissions, Permissions)
    reg = config.registry
    if not hasattr(reg, "permissions"):
        reg.permissions = {}
    reg.permissions[permissions.content_type] = permissions


def includeme(config):
    config.add_directive("add_acl", add_acl)
    config.add_directive("add_role", add_role)
    config.add_directive("add_content", add_content)
    config.add_directive("add_default_schema", add_default_schema)
    config.add_directive("add_permissions", add_permissions)
