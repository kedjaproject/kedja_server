from logging import getLogger

from pyramid.config import Configurator
from pyramid_zodbconn import get_connection
from translationstring import TranslationStringFactory

from .models.appmaker import appmaker


_ = TranslationStringFactory('kedja')
logger = getLogger(__name__)


def root_factory(request):
    conn = get_connection(request)
    return appmaker(conn.root(), request)


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    with Configurator(settings=settings) as config:
        config.include('kedja')
        config.include('.views')
    return config.make_wsgi_app()


def includeme(config):
    """ Include all locals except views. Useful for integration/functional tests too. """
    # Some sensible defaults
    settings = config.registry.settings
    settings['tm.manager_hook'] = 'pyramid_tm.explicit_manager'

    if 'redis.sessions.secret' not in settings:
        logger.info('Using random secret for sessions, '
                       'set "redis.sessions.secret" in your settings for persistance.')
        from random import choice
        from string import ascii_letters
        secret = ""
        for x in range(40):
            secret += choice(ascii_letters)
        settings['redis.sessions.secret'] = secret

    settings.setdefault('redis.sessions.timeout', 2400)
    settings.setdefault('redis.sessions.cookie_max_age', 2400)

    kedja_redis = settings['kedja.redis_url']
    settings.setdefault('redis.sessions.url', kedja_redis)

    # Pyramid/Pylons
    config.include('pyramid_tm')
    config.include('pyramid_retry')
    config.include('pyramid_zodbconn')
    config.include('pyramid_session_redis')
    config.set_root_factory(root_factory)
    config.include('pyramid_chameleon')
    # Cornice
    config.include('cornice')
    config.include('cornice_swagger')
    # Arche modules - note: will change!
    config.include('arche.predicates')
    config.include('arche.request_methods')
    config.include('arche.content')
    config.include('arche.mutator')
    config.include('arche.schemas')
    # Internal
    config.include('.config')
    config.include('.models')
    config.include('.resources')
    config.include('.security')
    config.include('.security.default_acl')
