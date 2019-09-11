from json import dumps
from unittest import TestCase

from kedja.testing import get_settings
from pyramid import testing
from pyramid.request import apply_request_extensions
from transaction import commit
from webtest import TestApp


class FunctionalUsersAPITests(TestCase):

    def setUp(self):
        self.config = testing.setUp(settings=get_settings())
        self.config.include('kedja.testing')
        self.config.include('kedja.security.default_acl')
        self.config.include('kedja.views.api.users')

    def _fixture(self, request):
        from kedja import root_factory
        root = root_factory(request)
        root['users']['10'] = request.registry.content('User', rid=10, first_name='Jeff')
        root['users']['11'] = request.registry.content('User', rid=11, first_name='Jane')
        cred = request.registry.content('Credentials', '10')
        cred.save()
        commit()
        return root, cred

    def test_get(self):
        wsgiapp = self.config.make_wsgi_app()
        app = TestApp(wsgiapp)
        request = testing.DummyRequest()
        apply_request_extensions(request)
        root, cred = self._fixture(request)
        response = app.get('/api/1/users/10', status=200, headers={'Authorization': cred.header()})
        self.assertEqual(response.json_body, {'data': {'first_name': 'Jeff'}, 'rid': 10, 'type_name': 'User'})

    def test_get_401(self):
        wsgiapp = self.config.make_wsgi_app()
        app = TestApp(wsgiapp)
        request = testing.DummyRequest()
        apply_request_extensions(request)
        self._fixture(request)
        response = app.get('/api/1/users/10', status=401)
        self.assertEqual(response.json_body.get('status', None), 'error')

    def test_get_403(self):
        wsgiapp = self.config.make_wsgi_app()
        app = TestApp(wsgiapp)
        request = testing.DummyRequest()
        apply_request_extensions(request)
        root, cred = self._fixture(request)
        response = app.get('/api/1/users/11', status=403, headers={'Authorization': cred.header()})
        self.assertEqual(response.json_body.get('status', None), 'error')

    def test_get_404(self):
        wsgiapp = self.config.make_wsgi_app()
        app = TestApp(wsgiapp)
        request = testing.DummyRequest()
        apply_request_extensions(request)
        self._fixture(request)
        response = app.get('/api/1/users/404', status=404)
        self.assertEqual(response.json_body.get('status', None), 'error')

    def test_put(self):
        wsgiapp = self.config.make_wsgi_app()
        app = TestApp(wsgiapp)
        request = testing.DummyRequest()
        apply_request_extensions(request)
        root, cred = self._fixture(request)
        response = app.put('/api/1/users/10',
                           params=dumps({'first_name': 'Jane', 'last_name': 'Doe'}),
                           headers={'Authorization': cred.header()},
                           status=200)
        self.assertEqual({"type_name": "User", "rid": 10, "data": {'first_name': 'Jane', 'last_name': 'Doe'}}, response.json_body)

    def test_delete(self):
        wsgiapp = self.config.make_wsgi_app()
        app = TestApp(wsgiapp)
        request = testing.DummyRequest()
        apply_request_extensions(request)
        root, cred = self._fixture(request)
        response = app.delete('/api/1/users/10', status=200,
                              headers={'Authorization': cred.header()},)
        self.assertEqual({"removed": 10}, response.json_body)

    # def test_collection_get(self):
    #     wsgiapp = self.config.make_wsgi_app()
    #     app = TestApp(wsgiapp)
    #     request = testing.DummyRequest()
    #     apply_request_extensions(request)
    #     self._fixture(request)
    #     response = app.get('/api/1/collections/3/cards', status=200)
    #     self.assertEqual([{'data': {}, 'rid': 4, 'type_name': 'Card'}], response.json_body)
    #
    # def test_collection_post(self):
    #     wsgiapp = self.config.make_wsgi_app()
    #     app = TestApp(wsgiapp)
    #     request = testing.DummyRequest()
    #     apply_request_extensions(request)
    #     root = self._fixture(request)
    #     response = app.post('/api/1/collections/3/cards', params=dumps({'title': 'Hello world!'}), status=200)
    #     # Find the new object
    #     keys = list(root['wall']['collection'].keys())
    #     keys.remove('card')
    #     self.assertEqual(len(keys), 1)
    #     new_rid = int(keys[0])
    #     self.assertEqual({'data': {'title': 'Hello world!'}, 'rid': new_rid, 'type_name': 'Card'}, response.json_body)
    #
    # def test_collection_post_bad_data(self):
    #     wsgiapp = self.config.make_wsgi_app()
    #     app = TestApp(wsgiapp)
    #     request = testing.DummyRequest()
    #     apply_request_extensions(request)
    #     self._fixture(request)
    #     app.post('/api/1/collections/3/cards', params=dumps({'title': 123}), status=400)
    #
    # def test_options(self):
    #     wsgiapp = self.config.make_wsgi_app()
    #     app = TestApp(wsgiapp)
    #     request = testing.DummyRequest()
    #     apply_request_extensions(request)
    #     self._fixture(request)
    #     headers = (('Access-Control-Request-Method', 'PUT'), ('Origin', 'http://localhost'))
    #     app.options('/api/1/collections/3/cards/4', status=200, headers=headers)
    #
    # def test_collection_options(self):
    #     wsgiapp = self.config.make_wsgi_app()
    #     app = TestApp(wsgiapp)
    #     request = testing.DummyRequest()
    #     apply_request_extensions(request)
    #     self._fixture(request)
    #     headers = (('Access-Control-Request-Method', 'POST'), ('Origin', 'http://localhost'))
    #     app.options('/api/1/collections/3/cards', status=200, headers=headers)
