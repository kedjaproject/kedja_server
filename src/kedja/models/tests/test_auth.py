from unittest import TestCase

from kedja.models.credentials import Credentials
from kedja.resources.root import Root
from kedja.resources.user import User
from pyramid import testing
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.request import apply_request_extensions
from zope.interface.verify import verifyObject

from kedja.interfaces import ICredentials
from kedja.interfaces import IOneTimeAuthToken
from kedja.interfaces import IOneTimeRegistrationToken
from kedja.models.appmaker import root_populator


class HTTPHeaderAuthenticationPolicyTests(TestCase):

    def setUp(self):
        self.config = testing.setUp()
        self.config.include('kedja.testing.minimal')
        self.config.include('kedja.resources.root')
        self.config.include('kedja.resources.user')
        self.config.include('kedja.resources.users')
        self.config.include('kedja.models.credentials')

    def tearDown(self):
        testing.tearDown()

    def _fixture(self, request):
        root = Root()
        root_populator(root, request)
        return root

    @property
    def _cut(self):
        from kedja.models.auth import HTTPHeaderAuthenticationPolicy
        return HTTPHeaderAuthenticationPolicy

    @property
    def _Credentials(self):
        from kedja.models.credentials import Credentials
        return Credentials

    @property
    def _get_vc(self):
        from kedja.models.credentials import get_valid_credentials
        return get_valid_credentials

    def test_remember(self):
        request = testing.DummyRequest()
        apply_request_extensions(request)
        root = self._fixture(request)
        auth = self._cut(debug=True)
        auth.remember(request, '10', token='abc', root=root)
        cred = self._get_vc('10', 'abc', registry=request.registry)
        self.assertTrue(cred)
        self.assertEqual('10', cred.userid)
        self.assertEqual('abc', cred.token)

    def test_forget(self):
        request = testing.DummyRequest()
        apply_request_extensions(request)
        root = self._fixture(request)
        auth = self._cut(debug=True)
        auth.remember(request, '10', token='abc')
        cred = self._get_vc('10', 'abc', registry=request.registry)
        request.headers['Authorization'] = cred.header()
        self.assertTrue(cred)
        auth.forget(request)
        cred = self._get_vc('10', 'abc', registry=request.registry)
        self.assertEqual(cred, None)

    def test_authenticated_userid(self):
        self.config.set_authorization_policy(ACLAuthorizationPolicy())
        auth = self._cut(debug=True)
        self.config.set_authentication_policy(auth)
        request = testing.DummyRequest()
        auth.remember(request, '10', token='abc')
        apply_request_extensions(request)
        self._fixture(request)
        cred = self._get_vc('10', 'abc', registry=request.registry)
        request.headers['Authorization'] = cred.header()
        self.assertEqual('10', request.authenticated_userid)

    def test_authenticated_userid_nonexisting_credentials(self):
        self.config.set_authorization_policy(ACLAuthorizationPolicy())
        auth = self._cut(debug=True)
        self.config.set_authentication_policy(auth)
        request = testing.DummyRequest()
        auth.remember(request, '10', token='abc')
        apply_request_extensions(request)
        self._fixture(request)
        cred = self._get_vc('10', 'abc', registry=request.registry)
        request.headers['Authorization'] = cred.header()
        cred.clear()
        self.assertEqual(None, request.authenticated_userid)


class OneTimeRegistrationTokenTests(TestCase):

    def setUp(self):
        self.config = testing.setUp()
        self.config.include('kedja.testing.minimal')
        self.config.include('kedja.resources.root')

    def tearDown(self):
        testing.tearDown()

    @property
    def _cut(self):
        from kedja.models.auth import OneTimeRegistrationToken
        return OneTimeRegistrationToken

    def test_create(self):
        request = testing.DummyRequest()
        apply_request_extensions(request)
        root = Root()
        obj = self._cut(root)
        payload = {'hello': 'world'}
        temp_token = obj.create(payload, registry=self.config.registry)
        self.assertIsInstance(temp_token, str)

    def test_consume(self):
        request = testing.DummyRequest()
        apply_request_extensions(request)
        root = Root()
        obj = self._cut(root)
        payload = {'hello': 'world'}
        temp_token = obj.create(payload, registry=self.config.registry)
        result = obj.consume(temp_token)
        self.assertEqual(payload, result)

    def test_integration(self):
        self.config.include('kedja.models.auth')
        request = testing.DummyRequest()
        apply_request_extensions(request)
        root = Root()
        obj = self.config.registry.queryAdapter(root, IOneTimeRegistrationToken)
        self.assertTrue(verifyObject(IOneTimeRegistrationToken, obj))


class OneTimeAuthTokenTests(TestCase):

    def setUp(self):
        self.config = testing.setUp()
        self.config.include('kedja.testing.minimal')
        self.config.include('kedja.models.credentials')
        self.config.include('kedja.resources')

    def tearDown(self):
        testing.tearDown()

    def _fixture(self, request):
        root = Root()
        root_populator(root, request)
        root['users']['10'] = user = User(rid=10)
        cred = Credentials('10', token='123')
        cred.save()
        return root, cred

    @property
    def _cut(self):
        from kedja.models.auth import OneTimeAuthToken
        return OneTimeAuthToken

    def test_create(self):
        request = testing.DummyRequest()
        apply_request_extensions(request)
        root, cred = self._fixture(request)
        obj = self._cut(root)
        temp_token = obj.create(cred, registry=self.config.registry)
        self.assertIsInstance(temp_token, str)

    def test_consume(self):
        request = testing.DummyRequest()
        apply_request_extensions(request)
        root, cred = self._fixture(request)
        obj = self._cut(root)
        temp_token = obj.create(cred, registry=self.config.registry)
        cred_returned = obj.consume('10', temp_token)
        self.assertTrue(ICredentials.providedBy(cred_returned))
        self.assertEqual(cred_returned, cred)

    def test_integration(self):
        self.config.include('kedja.models.auth')
        request = testing.DummyRequest()
        apply_request_extensions(request)
        root, cred = self._fixture(request)
        obj = self.config.registry.queryAdapter(root, IOneTimeAuthToken)
        self.assertTrue(verifyObject(IOneTimeAuthToken, obj))
