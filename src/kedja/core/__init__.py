from pyramid.traversal import find_root


RID_MAP_ATTR = 'rid_map'


def get_rid_map(resource):
    root = find_root(resource)
    return getattr(root, RID_MAP_ATTR, None)


def includeme(config):
    config.include('.content')
    config.include('.directives')
    config.include('.predicates')
    config.include('.request_methods')
    config.include('.schemas')
