import os

from pyramid.authentication import CallbackAuthenticationPolicy
from pyramid.interfaces import IAuthenticationPolicy
from zope.interface import implementer


@implementer(IAuthenticationPolicy)
class TestingAuthenticationPolicy(CallbackAuthenticationPolicy):

    def __init__(self, userid=None, callback=None, debug=True):
        self.userid = userid
        self.callback = callback
        self.debug = debug

    def remember(self, request, userid, **kw):
        self.userid = userid

    def forget(self, request):
        self.userid = None

    def unauthenticated_userid(self, request):
        return self.userid


def get_settings():
    here = os.path.abspath(os.path.dirname(__file__))
    return {
        'zodbconn.uri': 'memory://',
        'kedja.authomatic': os.path.join(here, 'views', 'api', 'tests', 'testing_fixtures', 'authomatic.yaml')
    }


def includeme(config):
    """ Include all locals except views. Useful for integration/functional tests too. """
    # Pyramid/Pylons
    from kedja import root_factory

    #config.registry.settings['tm.manager_hook'] = 'pyramid_tm.explicit_manager'
    #config.include('pyramid_tm')
    config.include('pyramid_retry')
    config.include('pyramid_zodbconn')
    config.set_root_factory(root_factory)
    config.include('pyramid_chameleon')
    # Cornice
    config.include('cornice')
    config.include('cornice_swagger')
    config.include(minimal)
    # Internal
    config.include('.core')
    config.include('.security')
    config.include('.models')
    config.include('.resources')


def minimal(config):
    config.include('kedja.core')
