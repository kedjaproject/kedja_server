from pyramid.paster import bootstrap

from kedja.core.rid_map import ResourceIDMap


def migrate(root):
    root._rid_map = root.rid_map
    delattr(root, 'rid_map')
    root.rid_map = ResourceIDMap(root)
    root.rid_map.rid_to_path.update(root._rid_map.rid_to_path.items())
    root.rid_map.path_to_rid.update(root._rid_map.path_to_rid.items())
    delattr(root, '_rid_map')


if __name__ == '__main__':
    with bootstrap('etc/development.ini') as env:
        request = env['request']
        request.tm.begin()
        migrate(env['root'])
        request.tm.commit()
