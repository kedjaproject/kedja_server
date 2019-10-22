from collections import UserDict


class ContentTypes(UserDict):

    def add(self, content_type):
        self[content_type.__name__] = content_type

    def __call__(self, content_type, *args, **kw):
        return self[content_type](*args, **kw)


def includeme(config):
    config.registry.content = ContentTypes()
