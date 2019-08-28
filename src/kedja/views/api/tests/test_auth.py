from unittest import TestCase

from pyramid import testing
from pyramid.request import apply_request_extensions
from transaction import commit
from webtest import TestApp

from kedja.security import WALL_OWNER
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


class FunctionalAuthPermissionAPITests(TestCase):
    """ Simplified transfer of ACL lists. """

    def setUp(self):
        self.config = testing.setUp(settings=get_settings())
        self.config.include('kedja.testing')
        self.config.include('kedja.security.default_acl')
        self.config.include('kedja.views.api.auth')

    def _fixture(self, request):
        from kedja import root_factory
        root = root_factory(request)
        root['users']['10'] = request.registry.content('User', rid=10)
        root['users']['100'] = request.registry.content('User', rid=100)
        root['wall'] = request.registry.content('Wall', rid=22)
        root['wall'].add_user_roles('10', WALL_OWNER)
        commit()
        return root

    def test_wall_private_anon(self):
        wsgiapp = self.config.make_wsgi_app()
        app = TestApp(wsgiapp)
        request = testing.DummyRequest()
        apply_request_extensions(request)
        self.config.begin(request)
        self._fixture(request)
        response = app.get('/api/1/auth/permissions/22')
        self.assertEqual({'all_other_allowed': False, 'allowed': [], 'denied': []},
                         response.json_body)

    def test_wall_owner(self):
        wsgiapp = self.config.make_wsgi_app()
        app = TestApp(wsgiapp)
        request = testing.DummyRequest()
        apply_request_extensions(request)
        self.config.begin(request)
        self._fixture(request)
        credentials = self.config.registry.content('Credentials', '10')
        credentials.save()
        headers = {'Authorization': credentials.header()}
        response = app.get('/api/1/auth/permissions/22', headers=headers)
        self.assertEqual({'all_other_allowed': True, 'allowed': [], 'denied': []},
                         response.json_body)

    def test_public_wall_but_not_owner(self):
        wsgiapp = self.config.make_wsgi_app()
        app = TestApp(wsgiapp)
        request = testing.DummyRequest()
        apply_request_extensions(request)
        self.config.begin(request)
        root = self._fixture(request)
        root['wall'].acl_name = 'public_wall'
        commit()
        credentials = self.config.registry.content('Credentials', '100')
        credentials.save()
        headers = {'Authorization': credentials.header()}
        response = app.get('/api/1/auth/permissions/22', headers=headers)
        self.assertEqual(response.json_body['all_other_allowed'], False)
        self.assertEqual(response.json_body['denied'], [])
        # Change to set to make test sane
        self.assertEqual(set(response.json_body['allowed']), {'Collection:View', 'Card:View', 'Wall:View'})
