from unittest import TestCase

from pyramid import testing
from pyramid.request import apply_request_extensions
from transaction import commit
from webtest import TestApp

from kedja.security import WALL_OWNER
from kedja.testing import get_settings


class FunctionalAuthPermissionAPITests(TestCase):
    """ Simplified transfer of ACL lists. """

    def setUp(self):
        self.config = testing.setUp(settings=get_settings())
        self.config.include('kedja.testing')
        self.config.include('kedja.security.default_acl')
        self.config.include('kedja.views.api.permissions')

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
        response = app.get('/api/1/permissions/22')
        self.assertEqual(False, response.json_body['all_other_allowed'])
        self.assertNotIn('View:Wall', response.json_body['allowed'])

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
        response = app.get('/api/1/permissions/22', headers=headers)
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
        response = app.get('/api/1/permissions/22', headers=headers)
        self.assertEqual(response.json_body['all_other_allowed'], False)
        self.assertEqual(response.json_body['denied'], [])
        # Change to set to make test sane
        allowed = set(response.json_body['allowed'])
        self.assertTrue({'Collection:View', 'Card:View', 'Wall:View'}.issubset(allowed))
