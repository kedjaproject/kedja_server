""" Special context-based validators that work with Cornice. """

from kedja import permissions
from kedja.views.permissions import HasPermissionType
from kedja.views.permissions import HasPermission


DELETE_RESOURCE = HasPermissionType(permissions.DELETE)
EDIT_RESOURCE = HasPermissionType(permissions.EDIT)
VIEW_RESOURCE = HasPermissionType(permissions.VIEW)
DELETE_CONTAINED_RESOURCE = HasPermissionType(permissions.DELETE, match='subrid')
EDIT_CONTAINED_RESOURCE = HasPermissionType(permissions.EDIT, match='subrid')
VIEW_CONTAINED_RESOURCE = HasPermissionType(permissions.VIEW, match='subrid')

# Special permissions that require some other context.
# For instance adding something needs to know what kind of resource we want to add.
VIEW_USERS = HasPermissionType(permissions.VIEW, rget='get_users')
ADD_WALL = HasPermissionType(permissions.ADD, rget='get_root', type_name='Wall')
ADD_COLLECTION = HasPermissionType(permissions.ADD, type_name='Collection')
ADD_CARD = HasPermissionType(permissions.ADD, type_name='Card')
ADD_TEMPLATE = HasPermissionType(permissions.MANAGE_TEMPLATES, rget='get_root')
