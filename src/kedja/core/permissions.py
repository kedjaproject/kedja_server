from collections import UserDict
from inspect import isclass

from kedja.permissions import ADD
from kedja.permissions import VIEW
from kedja.permissions import EDIT
from kedja.permissions import DELETE


_DEFAULT_CATEGORIES = (ADD, VIEW, EDIT, DELETE)


class Permissions(UserDict):
    """ A simple dict to keep track of content categorized permissions. Essentially instead of using just
        "Edit" we create permissions called "Wall:Edit".
    """

    def __init__(self, content_type, *permissions):
        """ Add permissions to content type. Defaults to _DEFAULT_CATEGORIES if nothing is specified. """
        super().__init__()
        if not isinstance(content_type, str):
            assert isclass(content_type)
            content_type = content_type.__name__
        self.content_type = content_type
        if not permissions:
            self.add(*_DEFAULT_CATEGORIES)

    def add(self, *permissions):
        for p in permissions:
            self[p] = "{}:{}".format(self.content_type, p)

    def __str__(self):
        return "<Permissions '{}' with {}>".format(self.content_type, self.values())
