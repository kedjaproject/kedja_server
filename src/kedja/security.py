from kedja.models.acl import NamedACL
from pyramid import security as psec
from pyramid.security import ALL_PERMISSIONS

from kedja.models.acl import Role
from kedja import _


## The different roles within Kedja

INSTANCE_ADMIN = Role(
    'ia',
    title=_("Instance admin"),
    description=_("Super admin for the whole instance")
)


# FIXME: This will be implemented later
# ORG_MANAGER = Role(
#     'om',
#     title=_("Organisation manager"),
#     description=_("Handles an organisation and all walls within it")
# )


PERSONAL = Role(
    'pe',
    title=_("Personal"),
    description=_("About yourself that you should always be albe to access.")
)


WALL_OWNER = Role(
    'wo',
    title=_("Wall owner"),
    description=_("Owner(s) of a wall")
)


COLLABORATOR = Role(
    'co',
    title=_("Collaborator"),
    description=_("Can edit basic things within the wall")
)


GUEST = Role(
    'gu',
    title=_("Guest"),
    description=_("Can view a private wall")
)


# Also note Pyramids Everyone and Authenticated


def default_acl(config):
    from kedja.resources.card import CardPerms
    from kedja.resources.collection import CollectionPerms
    from kedja.resources.wall import WallPerms
    # These are permission categories
    from kedja.permissions import ADD, VIEW, EDIT, DELETE

    base_perm_types = [ADD, VIEW, EDIT, DELETE]

    # Private hidden walls
    private_wall = NamedACL('private_wall', title="Private wall",
                            description="Walls that are private to a specific group of people")
    private_wall.add_allow(INSTANCE_ADMIN, ALL_PERMISSIONS)
    private_wall.add_allow(WALL_OWNER, ALL_PERMISSIONS)
    private_wall.add_allow(COLLABORATOR, [CardPerms[x] for x in base_perm_types])
    private_wall.add_allow(COLLABORATOR, [CollectionPerms[x] for x in base_perm_types])
    private_wall.add_allow(COLLABORATOR, [WallPerms[VIEW], WallPerms[EDIT]])
    private_wall.add_allow(GUEST, CardPerms[VIEW])
    private_wall.add_allow(GUEST, CollectionPerms[VIEW])
    private_wall.add_allow(GUEST, WallPerms[VIEW])

    # Public walls - everything private walls have but with visibility for everyone
    public_wall = NamedACL('public_wall', title="Public wall",
                           description="Publicly accessible")
    public_wall.extend(private_wall)
    public_wall.add_allow(psec.Everyone, CardPerms[VIEW])
    public_wall.add_allow(psec.Everyone, CollectionPerms[VIEW])
    public_wall.add_allow(psec.Everyone, WallPerms[VIEW])

    # User acl
    user = NamedACL('user', title="User  ACL",
                    description="For personal things")
    user.add_allow(PERSONAL, ALL_PERMISSIONS)
    user.add_allow(INSTANCE_ADMIN, ALL_PERMISSIONS)

    # Register ACLs
    config.add_acl(private_wall)
    config.add_acl(public_wall)
    config.add_acl(user)
