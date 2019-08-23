from kedja.interfaces import INamedACL
from kedja.interfaces import IRole


def add_acl(config, acl:INamedACL):
    assert INamedACL.providedBy(acl)
    assert acl.name
    config.registry.registerUtility(acl, name=acl.name)

def add_role(config, role:IRole):
    assert IRole.providedBy(role)
    config.registry.registerUtility(role, name=str(role))

def includeme(config):
    config.add_directive('add_acl', add_acl)
    config.add_directive('add_role', add_role)
