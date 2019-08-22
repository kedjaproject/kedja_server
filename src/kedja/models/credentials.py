import base64
import json
from collections import UserDict
from datetime import timedelta
from logging import getLogger
from random import choice
from string import ascii_letters, digits

from arche.content import ContentType
from pyramid.decorator import reify
from pyramid.threadlocal import get_current_registry
from zope.interface import implementer

from kedja.interfaces import ICredentials
from kedja.utils import get_redis_conn
from kedja import _


_DEFAULT = int(timedelta(days=7).total_seconds())
logger = getLogger(__name__)


def _generate_token(length=50):
    out = ""
    for i in range(length):
        out += choice(ascii_letters + digits)
    return out


@implementer(ICredentials)
class Credentials(UserDict):
    prefix = 'cred'

    def __init__(self, userid:str, token:str=None, expires:int=_DEFAULT, registry=None, **kw):
        assert isinstance(userid, str), "Must be a string"
        if registry is None:
            registry = get_current_registry()
        self.registry = registry
        if token is None:
            token = _generate_token()
        super().__init__(userid=userid, token=token, expires=expires, **kw)

    def get_key(self):
        return "{}.{}.{}".format(self.prefix, self.userid, self.token)

    @reify
    def _conn(self):
        return get_redis_conn(self.registry)

    def save(self):
        payload = json.dumps(dict(self))
        key = self.get_key()
        expires = self.get('expires', None)
        if expires:
            self._conn.setex(key, expires, payload)
        else:
            self._conn.set(key, payload)

    def reset_expire(self):
        expires = self.get('expires', None)
        if expires:
            self._conn.expire(self.get_key(), expires)
            return expires

    def valid_until(self):
        return self._conn.ttl(self.get_key())

    @classmethod
    def load(cls, userid, token, registry=None):
        if registry is None:
            registry = get_current_registry()
        key =  "{}.{}.{}".format(cls.prefix, userid, token)
        conn = get_redis_conn(registry)
        payload = conn.get(key)
        if payload:
            payload = payload.decode()
            data = json.loads(payload)
            inst = cls(registry=registry, **data)
            inst.reset_expire()
            return inst

    def clear(self):
        self._conn.delete(self.get_key())

    def header(self):
        merged = "%s:%s" % (self.userid, self.token)
        merged = bytes(merged, encoding='utf-8')
        return 'Basic %s' % base64.b64encode(merged).decode('utf-8')

    def __json__(self, request):
        try:
            user = request.root['users'][self.userid]
        except KeyError:
            user = None
        return {'Authorization': self.header(), 'userid': self.userid, 'user': user}

    def __bool__(self):
        return True

    @property
    def userid(self):
        return self['userid']

    @property
    def token(self):
        return self['token']


def get_valid_credentials(userid:str, token:str, registry=None):
    cred = Credentials.load(userid, token, registry)
    if isinstance(cred, Credentials):
        return cred


def remove_credentials(userid:str, token:str, registry=None):
    cred = Credentials.load(userid, token, registry)
    if isinstance(cred, Credentials):
        cred.clear()


CredentialsContent = ContentType(factory=Credentials, title=_("Credentials"))


def includeme(config):
    config.add_content(CredentialsContent)
