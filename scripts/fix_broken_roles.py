from pyramid.paster import bootstrap

from kedja.interfaces import IWall
from kedja.security import WALL_OWNER, PERSONAL


def fix_broken_roles(root):
    for user in root['users'].values():
        user._rolesdata.clear()
        user.add_user_roles(user.userid, PERSONAL)
    for obj in root.values():
        if IWall.providedBy(obj):
            userids = list(obj._rolesdata.keys())
            obj._rolesdata.clear()
            for userid in userids:
                obj.add_user_roles(userid, WALL_OWNER)


if __name__ == '__main__':
    with bootstrap('etc/development.ini') as env:
        request = env['request']
        request.tm.begin()
        fix_broken_roles(env['root'])
        request.tm.commit()
