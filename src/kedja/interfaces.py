from arche.interfaces import IFolder
from arche.interfaces import IRoot  # API
from zope.interface import Interface, Attribute


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
