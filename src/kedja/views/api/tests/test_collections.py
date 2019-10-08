from json import dumps
from unittest import TestCase

from kedja.testing import get_settings
from pyramid import testing
from pyramid.request import apply_request_extensions, Request
from transaction import commit
from webtest import TestApp

from kedja.resources.collection import Collection


class CollectionsAPIViewTests(TestCase):

    def setUp(self):
        self.config = testing.setUp()
        self.config.include('arche.content')
        self.config.include('arche.mutator')
        self.config.include('kedja.resources.root')
        self.config.include('kedja.resources.wall')
        self.config.include('kedja.resources.collection')

    def tearDown(self):
        testing.tearDown()

    @property
    def _cut(self):
        from kedja.views.api.collections import ContainedCollectionsAPI
        return ContainedCollectionsAPI

    def _fixture(self):
        content = self.config.registry.content
        root = content('Root')
        root['wall'] = wall = content('Wall', rid=2)
        wall['collection'] = content('Collection', rid=3)
        return root

    def test_get(self):
        root = self._fixture()
        request = testing.DummyRequest()
        apply_request_extensions(request)
        request.matchdict['rid'] = 2
        request.matchdict['subrid'] = 3
        inst = self._cut(request, context=root)
        response = inst.get()
        self.assertIsInstance(response, Collection)

    def test_put(self):
        root = self._fixture()
        body = bytes(dumps({'title': 'Hello world!'}), 'utf-8')
        request = Request.blank('/', method='PUT', body=body, matchdict={'rid': 2, 'subrid': 3})
        request.registry = self.config.registry
        apply_request_extensions(request)
        inst = self._cut(request, context=root)
        response = inst.put()
        self.assertEqual(response.title, 'Hello world!')
        self.assertIsInstance(response, Collection)

    def test_delete(self):
        root = self._fixture()
        request = testing.DummyRequest()
        apply_request_extensions(request)
        request.matchdict['rid'] = 2
        request.matchdict['subrid'] = 3
        inst = self._cut(request, context=root)
        response = inst.delete()
        self.assertIsInstance(response, dict)
        self.assertEqual(response, {'removed': 3})
        self.assertNotIn('collection', root['wall'])

    def test_collection_get(self):
        root = self._fixture()
        request = testing.DummyRequest()
        request.matchdict['rid'] = 2
        apply_request_extensions(request)
        inst = self._cut(request, context=root)
        response = inst.collection_get()
        self.assertIsInstance(response, list)
        self.assertIn(root['wall']['collection'], response)

    def test_collection_post(self):
        root = self._fixture()
        body = bytes(dumps({'title': 'Hello world!'}), 'utf-8')
        request = Request.blank('/', method='POST', body=body, matchdict={'rid': 2})
        request.registry = self.config.registry
        apply_request_extensions(request)
        inst = self._cut(request, context=root)
        response = inst.collection_post()
        self.assertIn(response, root['wall'].values())
        self.assertEqual(len(root['wall']), 2)


class FunctionalCollectionsAPITests(TestCase):

    def setUp(self):
        self.config = testing.setUp(settings=get_settings())
        self.config.include('pyramid_tm')
        self.config.include('kedja.testing')
        self.config.include('kedja.views.api.collections')
        # FIXME: Check with permissions too?
        self.config.testing_securitypolicy(permissive=True)

    def _fixture(self, request):
        from kedja import root_factory
        root = root_factory(request)
        root['wall'] = request.registry.content('Wall', rid=2)
        root['wall']['collection'] = request.registry.content('Collection', rid=3)
        commit()
        return root

    def test_get(self):
        wsgiapp = self.config.make_wsgi_app()
        app = TestApp(wsgiapp)
        request = testing.DummyRequest()
        apply_request_extensions(request)
        self._fixture(request)
        response = app.get('/api/1/walls/2/collections/3', status=200)
        self.assertEqual(response.json_body, {'data': {'title': ''}, 'rid': 3, 'type_name': 'Collection'})

    def test_get_404_child(self):
        wsgiapp = self.config.make_wsgi_app()
        app = TestApp(wsgiapp)
        request = testing.DummyRequest()
        apply_request_extensions(request)
        self._fixture(request)
        app.get('/api/1/walls/2/collections/404', status=404)

    def test_get_404_parent(self):
        wsgiapp = self.config.make_wsgi_app()
        app = TestApp(wsgiapp)
        request = testing.DummyRequest()
        apply_request_extensions(request)
        self._fixture(request)
        app.get('/api/1/walls/404/collections/3', status=404)

    def test_put(self):
        wsgiapp = self.config.make_wsgi_app()
        app = TestApp(wsgiapp)
        request = testing.DummyRequest()
        apply_request_extensions(request)
        self._fixture(request)
        response = app.put('/api/1/walls/2/collections/3', params=dumps({'title': 'Hello world!'}), status=200)
        self.assertEqual({"type_name": "Collection", "rid": 3, "data": {"title": "Hello world!"}}, response.json_body)

    def test_put_bad_data(self):
        wsgiapp = self.config.make_wsgi_app()
        app = TestApp(wsgiapp)
        request = testing.DummyRequest()
        apply_request_extensions(request)
        self._fixture(request)
        app.put('/api/1/walls/2/collections/3', params=dumps({'title': 123}), status=400)

    def test_delete(self):
        wsgiapp = self.config.make_wsgi_app()
        app = TestApp(wsgiapp)
        request = testing.DummyRequest()
        apply_request_extensions(request)
        self._fixture(request)
        response = app.delete('/api/1/walls/2/collections/3', status=200)
        self.assertEqual({"removed": 3}, response.json_body)

    def test_delete_404(self):
        wsgiapp = self.config.make_wsgi_app()
        app = TestApp(wsgiapp)
        request = testing.DummyRequest()
        apply_request_extensions(request)
        self._fixture(request)
        app.delete('/api/1/walls/2/collections/404', status=404)

    def test_collection_get(self):
        wsgiapp = self.config.make_wsgi_app()
        app = TestApp(wsgiapp)
        request = testing.DummyRequest()
        apply_request_extensions(request)
        self._fixture(request)
        response = app.get('/api/1/walls/2/collections', status=200)
        self.assertEqual([{'data': {'title': ''}, 'rid': 3, 'type_name': 'Collection'}], response.json_body)

    def test_collection_get_404(self):
        wsgiapp = self.config.make_wsgi_app()
        app = TestApp(wsgiapp)
        request = testing.DummyRequest()
        apply_request_extensions(request)
        self._fixture(request)
        app.get('/api/1/walls/404/collections', status=404)

    def test_collection_post(self):
        wsgiapp = self.config.make_wsgi_app()
        app = TestApp(wsgiapp)
        request = testing.DummyRequest()
        apply_request_extensions(request)
        root = self._fixture(request)
        response = app.post('/api/1/walls/2/collections', params=dumps({'title': 'Hello world!'}), status=200)
        # Find the new object
        keys = list(root['wall'].keys())
        keys.remove('collection')
        self.assertEqual(len(keys), 1)
        new_rid = int(keys[0])
        self.assertEqual({'data': {'title': 'Hello world!'}, 'rid': new_rid, 'type_name': 'Collection'}, response.json_body)

    def test_collection_post_bad_data(self):
        wsgiapp = self.config.make_wsgi_app()
        app = TestApp(wsgiapp)
        request = testing.DummyRequest()
        apply_request_extensions(request)
        self._fixture(request)
        app.post('/api/1/walls/2/collections', params=dumps({'title': 123}), status=400)

    def test_options(self):
        wsgiapp = self.config.make_wsgi_app()
        app = TestApp(wsgiapp)
        request = testing.DummyRequest()
        apply_request_extensions(request)
        self._fixture(request)
        headers = (('Access-Control-Request-Method', 'PUT'), ('Origin', 'http://localhost'))
        app.options('/api/1/walls/2/collections/3', status=200, headers=headers)

    def test_collection_options(self):
        wsgiapp = self.config.make_wsgi_app()
        app = TestApp(wsgiapp)
        request = testing.DummyRequest()
        apply_request_extensions(request)
        self._fixture(request)
        headers = (('Access-Control-Request-Method', 'POST'), ('Origin', 'http://localhost'))
        app.options('/api/1/walls/2/collections', status=200, headers=headers)


class FunctionalCollectionsOrderAPITests(TestCase):

    def setUp(self):
        self.config = testing.setUp(settings=get_settings())
        self.config.include('pyramid_tm')
        self.config.include('kedja.testing')
        self.config.include('kedja.views.api.collections')
        self.config.include('kedja.views.exceptions')
        # FIXME: Check with permissions too?
        self.config.testing_securitypolicy(permissive=True, userid='100')

    def _fixture(self, request):
        from kedja import root_factory
        root = root_factory(request)
        content = request.registry.content
        root['wall'] = content('Wall', rid=2)
        root['wall']['collection'] = collection = content('Collection', rid=3)
        collection['10'] = content('Card', rid=10)
        collection['20'] = content('Card', rid=20)
        collection['30'] = content('Card', rid=30)
        commit()
        return root

    def test_put(self):
        wsgiapp = self.config.make_wsgi_app()
        app = TestApp(wsgiapp)
        request = testing.DummyRequest()
        apply_request_extensions(request)
        self.config.begin(request)
        self._fixture(request)
        response = app.put('/api/1/collections/3/order', params=dumps({'order': [10, 20, 30]}), status=200)
        ordering = [x['rid'] for x in response.json_body]
        self.assertEqual([10, 20, 30], ordering)
        response = app.put('/api/1/collections/3/order', params=dumps({'order': [30, 20, 10]}), status=200)
        ordering = [x['rid'] for x in response.json_body]
        self.assertEqual([30, 20, 10], ordering)

    def test_put_too_many_names(self):
        wsgiapp = self.config.make_wsgi_app()
        app = TestApp(wsgiapp)
        request = testing.DummyRequest()
        apply_request_extensions(request)
        self.config.begin(request)
        self._fixture(request)
        app.put('/api/1/collections/3/order', params=dumps({'order': [10, 20, 30, 40]}), status=400)

    def test_missing_names(self):
        wsgiapp = self.config.make_wsgi_app()
        app = TestApp(wsgiapp)
        request = testing.DummyRequest()
        apply_request_extensions(request)
        self.config.begin(request)
        self._fixture(request)
        app.put('/api/1/collections/3/order', params=dumps({'order': [10, 20]}), status=400)
