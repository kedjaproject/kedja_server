from json import dumps
from unittest import TestCase

from pyramid import testing
from pyramid.request import apply_request_extensions
from transaction import commit
from webtest import TestApp

from kedja.security import INSTANCE_ADMIN
from kedja.security import COLLABORATOR
from kedja.security import WALL_OWNER
from kedja.testing import get_settings


class FunctionalRolesAPITests(TestCase):

    def setUp(self):
        self.config = testing.setUp(settings=get_settings())
        self.config.include('kedja.testing')
        self.config.include('kedja.security.default_acl')
        self.config.include('kedja.views.api.roles')

    def _fixture(self, request):
        from kedja import root_factory
        root = root_factory(request)
        root['users']['10'] = request.registry.content('User', rid=10)
        root['users']['100'] = request.registry.content('User', rid=100)
        root['wall'] = request.registry.content('Wall', rid=22)
        root['wall'].add_user_roles('10', WALL_OWNER)
        commit()
        return root

    @property
    def _Role(self):
        from kedja.models.acl import Role
        return Role

    def test_get(self):
        wsgiapp = self.config.make_wsgi_app()
        app = TestApp(wsgiapp)
        request = testing.DummyRequest()
        apply_request_extensions(request)
        self.config.begin(request)
        self._fixture(request)
        credentials = self.config.registry.content('Credentials', '10')
        credentials.save()
        headers = {'Authorization': credentials.header()}
        response = app.get('/api/1/roles/22/userid/10', headers=headers)
        self.assertEqual(['wo'], response.json_body)
        response = app.get('/api/1/roles/22/userid/100', headers=headers)
        self.assertEqual([], response.json_body)

    def test_put_assign_collaborator(self):
        wsgiapp = self.config.make_wsgi_app()
        app = TestApp(wsgiapp)
        request = testing.DummyRequest()
        apply_request_extensions(request)
        self.config.begin(request)
        self._fixture(request)
        credentials = self.config.registry.content('Credentials', '10')
        credentials.save()
        headers = {'Authorization': credentials.header()}
        body = dumps({'add_roles': [str(COLLABORATOR)]})
        response = app.put('/api/1/roles/22/userid/100', headers=headers, params=body)
        self.assertEqual(['co'], response.json_body)

    def test_put_remove_collaborator(self):
        wsgiapp = self.config.make_wsgi_app()
        app = TestApp(wsgiapp)
        request = testing.DummyRequest()
        apply_request_extensions(request)
        self.config.begin(request)
        root = self._fixture(request)
        root['wall'].add_user_roles('100', COLLABORATOR)
        commit()
        credentials = self.config.registry.content('Credentials', '10')
        credentials.save()
        headers = {'Authorization': credentials.header()}
        body = dumps({'remove_roles': [str(COLLABORATOR)]})
        response = app.put('/api/1/roles/22/userid/100', headers=headers, params=body)
        self.assertEqual([], response.json_body)

    def test_get_anon(self):
        wsgiapp = self.config.make_wsgi_app()
        app = TestApp(wsgiapp)
        request = testing.DummyRequest()
        apply_request_extensions(request)
        self.config.begin(request)
        self._fixture(request)
        response = app.get('/api/1/roles/22/userid/10', status=401)
        self.assertEqual(401, response.status_int)

    def test_put_with_root_as_role_context_and_wrong_perm(self):
        wsgiapp = self.config.make_wsgi_app()
        app = TestApp(wsgiapp)
        request = testing.DummyRequest()
        apply_request_extensions(request)
        self.config.begin(request)
        SEE_ALL = self._Role('SeeAll')
        self.config.add_role(SEE_ALL)
        self._fixture(request)
        credentials = self.config.registry.content('Credentials', '100')
        credentials.save()
        headers = {'Authorization': credentials.header()}
        body = dumps({'add_roles': [str(SEE_ALL)]})
        response = app.put('/api/1/roles/1/userid/100', headers=headers, params=body, status=403)
        self.assertEqual(403, response.status_int)

    def test_put_with_root_as_context(self):
        wsgiapp = self.config.make_wsgi_app()
        app = TestApp(wsgiapp)
        request = testing.DummyRequest()
        apply_request_extensions(request)
        self.config.begin(request)
        SEE_ALL = self._Role('SeeAll')
        self.config.add_role(SEE_ALL)
        root = self._fixture(request)
        root.add_user_roles('100', INSTANCE_ADMIN)
        commit()
        credentials = self.config.registry.content('Credentials', '100')
        credentials.save()
        headers = {'Authorization': credentials.header()}
        body = dumps({'add_roles': [str(SEE_ALL)]})
        response = app.put('/api/1/roles/1/userid/10', headers=headers, params=body)
        self.assertEqual(200, response.status_int)
        self.assertEqual([SEE_ALL], response.json_body)

    def test_put_with_root_as_role_context_and_wall_as_context(self):
        wsgiapp = self.config.make_wsgi_app()
        app = TestApp(wsgiapp)
        request = testing.DummyRequest()
        apply_request_extensions(request)
        self.config.begin(request)
        root = self._fixture(request)
        root.add_user_roles('100', INSTANCE_ADMIN)
        commit()
        credentials = self.config.registry.content('Credentials', '100')
        credentials.save()
        headers = {'Authorization': credentials.header()}
        body = dumps({'add_roles': [str(COLLABORATOR)]})
        response = app.put('/api/1/roles/22/userid/100', headers=headers, params=body)
        self.assertEqual(['co'], response.json_body)

    def test_put_with_no_data(self):
        wsgiapp = self.config.make_wsgi_app()
        app = TestApp(wsgiapp)
        request = testing.DummyRequest()
        apply_request_extensions(request)
        self.config.begin(request)
        self._fixture(request)
        credentials = self.config.registry.content('Credentials', '10')
        credentials.save()
        headers = {'Authorization': credentials.header()}
        response = app.put('/api/1/roles/22/userid/100', headers=headers, status=400)
        self.assertEqual(400, response.status_int)

    def test_put_with_bad_data(self):
        wsgiapp = self.config.make_wsgi_app()
        app = TestApp(wsgiapp)
        request = testing.DummyRequest()
        apply_request_extensions(request)
        self.config.begin(request)
        self._fixture(request)
        credentials = self.config.registry.content('Credentials', '10')
        credentials.save()
        headers = {'Authorization': credentials.header()}
        response = app.put('/api/1/roles/22/userid/100', headers=headers, status=400, params='{"blabla": 1}')
        self.assertEqual(400, response.status_int)

    def test_rid_security_aware(self):
        wsgiapp = self.config.make_wsgi_app()
        app = TestApp(wsgiapp)
        request = testing.DummyRequest()
        apply_request_extensions(request)
        self.config.begin(request)
        root = self._fixture(request)
        root['wall']['collection'] = request.registry.content('Collection', rid=123)
        commit()
        credentials = self.config.registry.content('Credentials', '10')
        credentials.save()
        headers = {'Authorization': credentials.header()}
        body = dumps({'add_roles': [str(COLLABORATOR)]})
        response = app.put('/api/1/roles/123/userid/10', headers=headers, status=400, params=body)
        self.assertEqual(400, response.status_int)
