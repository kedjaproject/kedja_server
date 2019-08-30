from unittest import TestCase

from pyramid import testing
from pyramid.request import apply_request_extensions
from transaction import commit
from webtest import TestApp

from kedja.testing import get_settings
from kedja.interfaces import IOneTimeRegistrationToken
from kedja.interfaces import IOneTimeAuthToken


class FunctionalAuthenticationAPITests(TestCase):
    """ Authentication tests post OAuth2 """

    def setUp(self):
        self.config = testing.setUp(settings=get_settings())
        self.config.include('kedja.testing')
        self.config.include('kedja.views.api.auth')

    def _fixture(self, request):
        from kedja import root_factory
        root = root_factory(request)
        root['users']['10'] = request.registry.content('User', rid=10)
        commit()
        return root

    def test_auth_methods(self):
        wsgiapp = self.config.make_wsgi_app()
        app = TestApp(wsgiapp)
        request = testing.DummyRequest()
        apply_request_extensions(request)
        self._fixture(request)
        response = app.get("/api/1/auth/methods")
        self.assertIn('google', response.json_body)

    def test_registraton(self):
        wsgiapp = self.config.make_wsgi_app()
        app = TestApp(wsgiapp)
        request = testing.DummyRequest()
        apply_request_extensions(request)
        root = self._fixture(request)
        # Create registration token
        reg_tokens = self.config.registry.getAdapter(root, IOneTimeRegistrationToken)
        token = reg_tokens.create({'hello': 'world', 'provider': 'Google', 'id': 123})
        response = app.post("/api/1/auth/register/{}".format(token))
        self.assertIn('Authorization', response.json_body)

    def test_login_get_credentials(self):
        wsgiapp = self.config.make_wsgi_app()
        app = TestApp(wsgiapp)
        request = testing.DummyRequest()
        apply_request_extensions(request)
        root = self._fixture(request)
        # Create login token
        credentials = self.config.registry.content('Credentials', '10')
        credentials.save()
        commit()
        auth_tokens = self.config.registry.getAdapter(root, IOneTimeAuthToken)
        token = auth_tokens.create(credentials)
        response = app.post("/api/1/auth/credentials/{}/{}".format('10', token))
        self.assertIn('Authorization', response.json_body)

    def test_valid_with_no_header(self):
        wsgiapp = self.config.make_wsgi_app()
        app = TestApp(wsgiapp)
        request = testing.DummyRequest()
        apply_request_extensions(request)
        self._fixture(request)
        response = app.get('/api/1/auth/valid', status=200)
        self.assertEqual({'userid': None, 'valid_until': None}, response.json_body)

    def test_valid_with_credentials(self):
        wsgiapp = self.config.make_wsgi_app()
        app = TestApp(wsgiapp)
        request = testing.DummyRequest()
        apply_request_extensions(request)
        self._fixture(request)
        # Create auth token
        credentials = self.config.registry.content('Credentials', '10')
        credentials.save()
        headers = {'Authorization': credentials.header()}
        response = app.get('/api/1/auth/valid', status=200, headers=headers)
        self.assertEqual({'userid': '10', 'valid_until': credentials.get('expires', object())}, response.json_body)
