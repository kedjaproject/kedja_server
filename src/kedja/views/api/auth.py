"""
Authentication procedure


1. What options to we have?

/api/1/auth/methods

Returns a dict with auth info, see AuthMethodsAPIView


2. Use the login url, which will send the user to

/login/<provider_name>

See AuthomaticView


Alt A, User exists:
3A Credentials will be created and a temp login token returned
Returned url will be "<client url>/logging_in?u=<userid>&t=<temp token>"
See AuthomaticView


4A - The auth token is posted back to retrieve the credentials header.
/api/1/auth/credentials/{userid}/{token}
See AuthCredentialsAPIView
The credentials will be returned


Alt B, registration required:
3B - Redirect to client with a registration token
Returned url will be "<client url>/register?t=<a long temp reg token>"

4B - Post reg info back to the server, return credentials
/api/1/auth/register/{token}
The credentials will be returned (same as 4A)
"""
from logging import getLogger
from urllib.parse import urlparse

import colander
from authomatic.adapters import WebObAdapter
from cornice.resource import resource
from cornice.resource import view
from cornice.validators import colander_validator
from pyramid.authentication import extract_http_basic_credentials
from pyramid.decorator import reify
from pyramid.httpexceptions import HTTPBadRequest
from pyramid.httpexceptions import HTTPFound
from pyramid.response import Response
from pyramid.security import forget
from pyramid.view import view_config

from kedja.interfaces import IAuthomatic
from kedja.interfaces import IOneTimeAuthToken
from kedja.interfaces import IOneTimeRegistrationToken
from kedja.models.credentials import get_valid_credentials
from kedja.views.api.base import APIBase
from kedja.views.base import BaseView

logger = getLogger(__name__)


@resource(path='/api/1/auth/methods',
          #validators=(colander_validator,),
          cors_origins=('*',),
          tags=['Authentication'],
          factory='kedja.root_factory')
class AuthMethodsAPIView(APIBase):

    #@view(schema=ResourceAPISchema())
    def get(self):
        """ Return all available authentication methods"""
        authomatic = self.request.registry.queryUtility(IAuthomatic)
        methods = {}
        for (k, v) in authomatic.config.items():
            methods[k] = {
                'url': self.request.route_url('login', provider_name=k),
                'method': 'GET',
                # FIXME: Proper translation system here
                'title': self.request.localizer.translate(v.get('title', k)),
            }
        return methods


class AuthViewMixin(object):

    @reify
    def auth_tokens(self):
        return self.request.registry.getAdapter(self.context, IOneTimeAuthToken)

    @reify
    def reg_tokens(self):
        return self.request.registry.getAdapter(self.context, IOneTimeRegistrationToken)

    def validate_temp_auth_token(self, request, **kw):
        userid = self.request.matchdict['userid']
        token = self.request.matchdict['token']
        if not self.auth_tokens.validate(userid, token, registry=self.request.registry):
            self.error(request, "No such user or auth token", status=400)

    def consume_temp_auth_token(self, userid:str, token:str):
        credentials = self.auth_tokens.consume(userid, token, registry=self.request.registry)
        if credentials:
            return credentials
        # This shouldn't happen due to validation 'validate_temp_auth_token'
        raise HTTPBadRequest("No such user or token")


class AuthomaticView(BaseView, AuthViewMixin):
    """ This view has several functions:

        1) Send the user to the provider to initiate login
        2) Make sure the login worked correctly
        3) Lookup any existing user
        4a) If a user exists, create credentials and a temporary access token. Redirect to the client
        4b) If a user doesn't exist, store the information from the provider with a temporary registration token and
            redirect to the client.
    """

    @view_config(route_name='login', renderer='json')
    def login(self):
        # We will need the response to pass it to the WebObAdapter.
        response = Response()

        # Get the internal provider name URL variable.
        provider_name = self.request.matchdict.get('provider_name')

        authomatic = self.request.registry.queryUtility(IAuthomatic)
        if authomatic is None:
            raise HTTPBadRequest("We don't know how to process login - no providers configured.")

        came_from = self.request.GET.pop('came_from', None)
        if came_from:
            self.request.session['came_from'] = came_from
            self.request.session.changed()

        # Start the login procedure.
        result = authomatic.login(WebObAdapter(self.request, response), provider_name)

        # Do not write anything to the response if there is no result!
        if result:
            # If there is result, the login procedure is over and we can write to
            # response.
            # The question here is what kind of status does this page have...?
            #response.write('<a href="..">Home</a>')

            if result.error:
                # Login procedure finished with an error.
                logger.debug("Authomatic login with provider '%s' caused error:\n%s", provider_name, result.error)
                response.write(
                    u'<h2>Damn that error: {0}</h2>'.format(result.error))

            elif result.user:
                # Hooray, we have the user!

                # OAuth 2.0 and OAuth 1.0a provide only limited user data on login,
                # We need to update the user to get more info.
                # However, as long as we have the ID we should be fine here
                updated = False
                if not result.user.id:
                    result.user.update()
                    updated = True

                # context should be root here
                users = self.context['users']
                user = users.find_providers_user(result)

                # FIXME: The result will contain information on wether the email is verified and so on.
                # In case it is, the provider should be added to existing user instead.

                # Check incoming came from param, here we want to remove it.
                came_from = self.request.session.get('came_from', None)

                # Allow any URL on a registered domain?
                if came_from is None:
                    came_from = self.request.registry.settings['kedja.client_url']
                else:
                    # Validate, pick first registered if none exist
                    # TODO: Allow other URLs
                    parsed = urlparse(came_from)
                    if not parsed.hostname in ['localhost', '127.0.0.1']:
                        # Nuke incoming in case it isn't localhost
                        came_from = self.request.registry.settings['kedja.client_url']
                    self.request.session.changed()

                if user is None:
                    # Now we do need more info
                    if not updated:
                        result.user.update()
                    # Create a temporary registration with this user
                    reg_tokens = self.request.registry.getAdapter(self.context, IOneTimeRegistrationToken)
                    token = reg_tokens.create(result.user.to_dict())
                    # Redirect back to client with the token
                    # self.request.registry.settings['kedja.client_url']
                    registration_url = came_from + '/register?t=' + token
                    return HTTPFound(location=registration_url)

                # Update existing user in case something differs, but don't change usernames if they exist
                userdata = result.user.to_dict()
                for k in ('first_name', 'last_name'):
                    currdata = getattr(user, k, None)
                    if currdata:
                        userdata.pop(k, None)
                with self.request.get_mutator(user) as mutator:
                    mutator.update(userdata)

                # Login user
                cred = self.request.registry.content('Credentials', user.userid)
                cred.save()
                auth_token = self.auth_tokens.create(cred)
                login_url = "{}/logging_in?u={}&t={}".format(
                    came_from,
                    user.userid,
                    auth_token
                )
                return HTTPFound(location=login_url)

        # It won't work if you don't return the response
        return response


@resource(path='/api/1/auth/register/{token}',
          #validators=(colander_validator,),
          cors_origins=('*',),
          tags=['Authentication'],
          factory='kedja.root_factory')
class AuthRegisterAPIView(APIBase, AuthViewMixin):

    @view(validators=('validate_reg_token'))
    def post(self):
        userpayload = self.reg_tokens.consume(self.request.matchdict['token'], registry=self.request.registry)
        users = self.root['users']
        user = self.request.registry.content('User', rid=self.request.root.rid_map.new_rid())
        users[user.userid] = user
        users.add_provider(user, userpayload)
        # FIXME: Handle all other updates from POST?
        with self.request.get_mutator(user) as mutator:
             mutator.update(userpayload)
        cred = self.request.registry.content('Credentials', user.userid)
        cred.save()
        return cred

    def validate_reg_token(self, request, **kw):
        token = self.request.matchdict['token']
        if not self.reg_tokens.validate(token, registry=self.request.registry):
            self.error(request, "No such registration token", status=400)


@resource(path='/api/1/auth/credentials/{userid}/{token}',
          validators=(colander_validator,),
          cors_origins=('*',),
          tags=['Authentication'],
          factory='kedja.root_factory')
class AuthCredentialsAPIView(APIBase, AuthViewMixin):
    """ Retrieve the actual credentials from a temp token. """

    @view(validators=('validate_temp_auth_token'))
    def post(self):
        userid = self.request.matchdict['userid']
        token = self.request.matchdict['token']
        return self.consume_temp_auth_token(userid, token)


class AuthValidBodyResponseSchema(colander.Schema):
    userid = colander.SchemaNode(
        colander.String(),
        missing=None,
    )
    valid_until = colander.SchemaNode(
        colander.Int(),
        missing=None,
    )


class AuthValidOKResponseSchema(colander.Schema):
    title = "Valid response"
    body = AuthValidBodyResponseSchema()


auth_valid_response_schemas = {
    '200': AuthValidOKResponseSchema(description='Response params for authentication check'),
}


@resource(path='/api/1/auth/valid',
          validators=(colander_validator,),
          cors_origins=('*',),
          tags=['Authentication'],
          factory='kedja.root_factory',
          response_schemas=auth_valid_response_schemas)
class AuthValidAPIView(APIBase):
    """ Check if an authentication is valid. """

    @view()
    def get(self):
        userid = self.request.authenticated_userid
        if userid:
            # If the user is authenticated, both the http_creds and the credentials will exist.
            http_creds = extract_http_basic_credentials(self.request)
            cred = get_valid_credentials(http_creds.username, http_creds.password, registry=self.request.registry)
            return {
                'userid': self.request.authenticated_userid,
                'valid_until': cred.valid_until()
            }
        else:
            return {
                'userid': None,
                'valid_until': None
            }


@resource(path='/api/1/auth/logout',
          #validators=(colander_validator,),
          cors_origins=('*',),
          tags=['Authentication'],
          factory='kedja.root_factory')
class LogoutView(APIBase):

    def post(self):
        userid = self.request.authenticated_userid
        forget(self.request)
        return {'bye': userid}


def includeme(config):
    config.add_route('login', '/login/{provider_name}')
    config.scan(__name__)
