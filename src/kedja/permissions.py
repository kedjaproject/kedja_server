

from arche.content import (
    ADD,
    EDIT,
    DELETE,
    VIEW,
)


# The redefinition is to make editors happy.
# These are the basic permission types. Content types will have permissions like 'Wall:Edit' based on this.
ADD = ADD
EDIT = EDIT
DELETE = DELETE
VIEW = VIEW

# Manage visibility of something
VISIBILITY = 'Visibility'

# Invite users
INVITE = 'Invite'

MANAGE_TEMPLATES = 'ManageTemplates'