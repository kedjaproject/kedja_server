from zope.interface import Interface, Attribute


class IResource(Interface):
    """ The absolute minimum an object should implement to be able to be added to a resource tree.
        Note that this doesn't require ZODB, it's possible to implement the same structure with
        other kinds of persistance.

        If you do use this with ZODB, intherit the persistent.IPersistent interface too.
    """
    __name__ = Attribute("Name of this resource")
    __parent__ = Attribute("Reference to parent object, used by traversal.")

    def get_rid(default=None):
        """ Returns resource ID"""

    def set_rid(oid):
        """ Set rid. """

    def del_rid():
        """ Remove rid. """

    rid = Attribute("Property for Resource ID")


class IFolder(IResource):
    pass


class IRoot(IResource):
    """ Marks the root object. """


class ICredentials(Interface):
    pass

class ICard(IFolder):
    pass

class ICollection(IFolder):
    pass

class IWall(IFolder):
    pass

class IUsers(IFolder):
    pass

class IUser(IFolder):
    pass


class IAuthomatic(Interface):
    """ The util where authomatic is configured.
    """


class IOneTimeRegistrationToken(Interface):
    """ When an incoming authentication finds no corresponding user, store the information temporarily
        under a token and send that token to a registration form.

        If the registration is completed, retrieve the information and create a user.
    """


class IOneTimeAuthToken(Interface):
    """ Stores quickly expiring tokens in redis. The purpose is to never have to share the actual login header
        via a 302 redirect.

        The value is the header needed to authenticate. a typical stored key might look something like this:

        Key: 'otat.<userid>.<credentials token>
        Value: 'Basic <base64 encoded token here>'
    """
    context = Attribute("The adapted context, should be the Root.")
    prefix = Attribute("Prefix redis keys with this.")

    def __init__(context):
        pass

    def get_key(credentials: ICredentials, token:str):
        """ Return redis key """


    def create(credentials: ICredentials, expires=30, registry=None):
        """ Create and store a token. Returns the token.
        """

    def consume(userid:str, token:str, registry=None):
        """ Consume token and return the real auth header.
        """


class ISecurityAware(Interface):
    """ A resource that will work with Pyramids ACL system and produce an ACL. It may also have roles assigned. """

    acl_name = Attribute("Name of the ACL used for this resource")

    def __acl__():
        """ Called by Pyramids ACLAuthorizationPolicy.
        """

    def add_user_roles(userid:str, *roles):
        """ Add roles, should be instances of kedja.models.acl.Role or Pyramids security Authenticated/Everyone."""

    def remove_user_roles(userid:str, *roles):
        """ Remove roles, should be instances of kedja.models.acl.Role or Pyramids security Authenticated/Everyone."""

    def get_computed_acl(userids=[], request=None):
        """ Figure out permissions for userids based on the roles and named acl lists on each resource.
            Permissions will be fetched by walking towards the root.

            Any roles will be translated to userids.

            Will return a generator with tuples with action, userid or system role, and then permissions.

            It will traverse backwards from self to the root and then insert pyramid.security.DENY_ALL.

            See Pyramids security docs.
        """

    def get_roles_map(userids):
        """ Return a dict with str userid as key, and a set of roles as values.
            Userids with no roles will be skipped.
        """

    def get_acl(registry=None):
        """ Get the current contexts ACL, if any. """




class INamedACL(Interface):
    pass


class IRole(Interface):
    pass


class ITemplateFileUtil(Interface):
    pass



# Marker iface to treat any attribute as changed
ALL = object()


# Events
class IResourceEvent(Interface):
    """ Resource events are object events for objects that have been attached to the resource tree.
        The resource is (usually) what's tied to a view with the context-argument.

        See the Pyramid docs on the term resource.
    """
    resource = Attribute("The instantiated resource this event is for.")
    parent = Attribute("")
    name = Attribute("Name of the resource. Corresponds to __name__ for resource that are already "
                     "a part of the resource tree.")
    request = Attribute("The request object if it was passed along")

    def __init__(resource, parent=None, name=None, request=None, **kw):
        pass


class IResourceWillBeAdded(IResourceEvent):
    """ When a resource is about to be added to a parent. ``parent`` and ``name`` will be None for the root object"""


class IResourceAdded(IResourceEvent):
    """ A resource has been added. """


class IResourceWillBeRemoved(IResourceEvent):
    """ A resource is about to be removed. """


class IResourceRemoved(IResourceEvent):
    """ A resource was removed. """


class IResourceUpdated(IResourceEvent):
    changed = Attribute("Attributes that have changed.")

    def __init__(resource, changed=ALL, **kw):
        pass


class ISchemaEvent(Interface):
    schema = Attribute("The instantiated schema this event is for.")
    request = Attribute("The request object if it was passed along")
    kw = Attribute("Any other attributes passed along.")

    def __init__(resource, request=None, **kw):
        pass


class ISchemaCreated(ISchemaEvent):
    """ Fire this event when schemas are instantiated.
        This always happens before a schema is bound.
    """


class ISchemaBound(ISchemaEvent):
    """ Fire this event when schemas are bound.

        The bound values are stored at schema.bindings
    """
