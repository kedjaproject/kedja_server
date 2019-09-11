""" Special cornice-version validators. """
from kedja.views.api.base import add_error


class HasPermission(object):
    """ This is kind of a hack to get proper permission checks in """

    def __init__(self, permission:str, match='rid', rget='get_resource'):
        self.permission = permission
        self.match = match
        self.rget = getattr(self, rget)

    def __call__(self, request, **kw):
        resource = self.rget(request)
        if resource:
            self.check(resource, request, self.permission)

    def check(self, resource, request, permission):
        if not request.has_permission(permission, resource):
            if request.authenticated_userid:
                add_error(request, msg="You're not allowed to access this", type='path', status=403)
            else:
                add_error(request, msg="You're not authenticated, perhaps you need to login?", type='path', status=401)

    def get_resource(self, request):
        try:
            rid = request.matchdict[self.match]
        except KeyError:
            add_error(request, msg="KeyError: Specified matchdict key %r doesn't exist" % self.match, type='path', status=400)
            return
        if isinstance(rid, str):
            rid = int(rid)
        resource = request.root.rid_map.get_resource(rid)
        if resource is None:
            add_error(request, msg="There's no resource with RID %s " % rid, type='path', status=404)
        else:
            return resource

    def get_root(self, request):
        if request.root is None:
            add_error(request, msg="root resource not found", type='path', status=404)
        else:
            return request.root

    def get_users(self, request):
        users = request.root.get('users', None)
        if users is None:
            add_error(request, msg="users resource not found", type='path', status=404)
        else:
            return users


class HasPermissionType(HasPermission):
    """ Check a permission category on the requested resource instead. """

    def __init__(self, permission:str, match='rid', rget='get_resource', type_name=None):
        super().__init__(permission, match=match, rget=rget)
        self.type_name = type_name

    def check(self, resource, request, permission):
        content = request.registry.content
        if self.type_name is None:
            type_name = content.get_type(resource)
        else:
            type_name = self.type_name
        # This extract the exact permission name, something like 'Edit' -> 'Wall:Edit'
        perm = content[type_name].permissions[permission]
        return super().check(resource, request, perm)
