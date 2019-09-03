from json import dumps, loads
from unittest import TestCase

from kedja.testing import get_settings
from pyramid import testing
from pyramid.renderers import render
from pyramid.request import apply_request_extensions
from pyramid.request import Request
from transaction import commit
from webtest import TestApp

from kedja.resources.wall import Wall


class WallsAPIViewTests(TestCase):

    def setUp(self):
        self.config = testing.setUp()
        self.config.include('kedja.testing.minimal')
        self.config.include('kedja.resources.root')
        self.config.include('kedja.resources.wall')

    def tearDown(self):
        testing.tearDown()

    @property
    def _cut(self):
        from kedja.views.api.walls import WallsAPIView
        return WallsAPIView

    def _fixture(self):
        content = self.config.registry.content
        root = content('Root')
        root['wall'] = content('Wall', rid=2)
        return root

    def test_get(self):
        root = self._fixture()
        request = testing.DummyRequest()
        apply_request_extensions(request)
        request.matchdict['rid'] = 2
        inst = self._cut(request, context=root)
        response = inst.get()
        self.assertIsInstance(response, Wall)

    def test_put(self):
        root = self._fixture()
        body = bytes(dumps({'title': 'Hello world!'}), 'utf-8')
        request = Request.blank('/', method='PUT', body=body, matchdict={'rid': 2})
        request.registry = self.config.registry
        apply_request_extensions(request)
        inst = self._cut(request, context=root)
        response = inst.put()
        self.assertEqual(response.title, 'Hello world!')
        self.assertIsInstance(response, Wall)

    def test_delete(self):
        root = self._fixture()
        request = testing.DummyRequest()
        apply_request_extensions(request)
        request.matchdict['rid'] = 2
        inst = self._cut(request, context=root)
        response = inst.delete()
        self.assertIsInstance(response, dict)
        self.assertEqual(response, {'removed': 2})
        self.assertNotIn('wall', root)

    def test_collection_get(self):
        root = self._fixture()
        request = testing.DummyRequest()
        apply_request_extensions(request)
        inst = self._cut(request, context=root)
        response = inst.collection_get()
        self.assertIsInstance(response, list)
        self.assertIn(root['wall'], response)

    def test_collection_post(self):
        root = self._fixture()
        body = bytes(dumps({'title': 'Hello world!'}), 'utf-8')
        request = Request.blank('/', method='POST', body=body)
        request.registry = self.config.registry
        apply_request_extensions(request)
        inst = self._cut(request, context=root)
        response = inst.collection_post()
        self.assertIn(response, root.values())
        self.assertEqual(len(root), 2)


class WallsStructureAPIViewTests(TestCase):

    def setUp(self):
        self.config = testing.setUp()
        self.config.include('kedja.testing.minimal')
        self.config.include('kedja.resources')

    def tearDown(self):
        testing.tearDown()

    @property
    def _cut(self):
        from kedja.views.api.walls import WallStructureAPIView
        return WallStructureAPIView

    def _fixture(self):
        content = self.config.registry.content
        root = content('Root')
        root['wall'] = wall = content('Wall', rid=2)
        for i in range(1, 4):
            wall['col%s' % i] = collection = content('Collection', rid=i*10)
            for j in range(1, 4):
                collection['card%s' % j] = content('Card', rid=j*100+i)
        return root

    def test_get(self):
        root = self._fixture()
        request = testing.DummyRequest()
        apply_request_extensions(request)
        request.matchdict['rid'] = 2
        inst = self._cut(request, context=root)
        response = inst.get()
        expected = [
            [10, [
                [101, []], [201, []], [301, []]
            ]],
            [20, [
                [102, []], [202, []], [302, []]
            ]],
            [30, [
                [103, []], [203, []], [303, []]
            ]]
        ]
        self.assertEqual(response, expected)


class WallsContentAPIViewTests(TestCase):

    def setUp(self):
        self.config = testing.setUp()
        self.config.include('kedja.testing.minimal')
        self.config.include('kedja.resources')

    def tearDown(self):
        testing.tearDown()

    @property
    def _cut(self):
        from kedja.views.api.walls import WallContentAPIView
        return WallContentAPIView

    def _fixture(self):
        content = self.config.registry.content
        root = content('Root')
        root['wall'] = wall = content('Wall', rid=2)
        resources = {}
        for i in range(1, 4):
            wall['col%s' % i] = collection = content('Collection', rid=i*10)
            resources[collection.rid] = collection
            for j in range(1, 4):
                collection['card%s' % j] = card = content('Card', rid=j*100+i)
                resources[card.rid] = card
        return root, resources

    def test_get(self):
        root, resources = self._fixture()
        request = testing.DummyRequest()
        apply_request_extensions(request)
        request.matchdict['rid'] = 2
        inst = self._cut(request, context=root)
        response = inst.get()
        self.assertEqual(response, {'resources': resources})


class FunctionalWallsAPITests(TestCase):

    def setUp(self):
        self.config = testing.setUp(settings=get_settings())
        self.config.include('kedja.testing')
        self.config.include('pyramid_tm')
        self.config.include('kedja.views.api.walls')
        self.config.testing_securitypolicy(permissive=True)

    def _fixture(self, request):
        from kedja import root_factory
        root = root_factory(request)
        root['wall'] = request.registry.content('Wall', rid=2)
        commit()
        return root

    def test_get(self):
        wsgiapp = self.config.make_wsgi_app()
        app = TestApp(wsgiapp)
        request = testing.DummyRequest()
        apply_request_extensions(request)
        self._fixture(request)
        response = app.get('/api/1/walls/2', status=200)
        self.assertEqual(response.json_body,
                         {'data': {'title': '', 'acl_name': 'private_wall', 'relations': [],}, 'rid': 2, 'type_name': 'Wall'})

    def test_get_404(self):
        wsgiapp = self.config.make_wsgi_app()
        app = TestApp(wsgiapp)
        request = testing.DummyRequest()
        apply_request_extensions(request)
        self._fixture(request)
        response = app.get('/api/1/walls/10', status=404)
        self.assertEqual(response.json_body.get('status', None), 'error')

    def test_put(self):
        wsgiapp = self.config.make_wsgi_app()
        app = TestApp(wsgiapp)
        request = testing.DummyRequest()
        apply_request_extensions(request)
        self._fixture(request)
        response = app.put('/api/1/walls/2', params=dumps({'title': 'Hello world!'}), status=200)
        self.assertEqual({"type_name": "Wall", "rid": 2, "data":
            {"title": "Hello world!", 'acl_name': 'private_wall', 'relations': []}},
                         response.json_body)

    def test_put_bad_data(self):
        wsgiapp = self.config.make_wsgi_app()
        app = TestApp(wsgiapp)
        request = testing.DummyRequest()
        apply_request_extensions(request)
        self._fixture(request)
        response = app.put('/api/1/walls/2', params=dumps({'title': 100}), status=400)
        self.assertEqual(response.json_body.get('status'), 'error')

    def test_delete(self):
        wsgiapp = self.config.make_wsgi_app()
        app = TestApp(wsgiapp)
        request = testing.DummyRequest()
        apply_request_extensions(request)
        self._fixture(request)
        response = app.delete('/api/1/walls/2', status=200)
        self.assertEqual({"removed": 2}, response.json_body)

    def test_delete_404(self):
        wsgiapp = self.config.make_wsgi_app()
        app = TestApp(wsgiapp)
        request = testing.DummyRequest()
        apply_request_extensions(request)
        self._fixture(request)
        response = app.delete('/api/1/walls/10', status=404)
        self.assertEqual(response.json_body.get('status', None), 'error')

    def test_collection_get(self):
        wsgiapp = self.config.make_wsgi_app()
        app = TestApp(wsgiapp)
        request = testing.DummyRequest()
        apply_request_extensions(request)
        self._fixture(request)
        response = app.get('/api/1/walls', status=200)
        self.assertEqual([{'data': {'acl_name': 'private_wall', 'relations': [], 'title': ''}, 'rid': 2, 'type_name': 'Wall'}],
                         response.json_body)

    def test_collection_post(self):
        wsgiapp = self.config.make_wsgi_app()
        app = TestApp(wsgiapp)
        request = testing.DummyRequest()
        apply_request_extensions(request)
        root = self._fixture(request)
        response = app.post('/api/1/walls', params=dumps({'title': 'Hello world!'}), status=200)
        # Find the new object
        keys = list(root.keys())
        keys.remove('users')
        keys.remove('wall')
        self.assertEqual(len(keys), 1)
        new_rid = int(keys[0])
        self.assertEqual({'data': {'title': 'Hello world!', 'acl_name': 'private_wall', 'relations': []}, 'rid': new_rid, 'type_name': 'Wall'},
                         response.json_body)

    def test_collection_post_bad_data(self):
        wsgiapp = self.config.make_wsgi_app()
        app = TestApp(wsgiapp)
        request = testing.DummyRequest()
        apply_request_extensions(request)
        self._fixture(request)
        app.post('/api/1/walls', params=dumps({'title': 123}), status=400)

    def test_options(self):
        wsgiapp = self.config.make_wsgi_app()
        app = TestApp(wsgiapp)
        request = testing.DummyRequest()
        apply_request_extensions(request)
        self._fixture(request)
        headers = (('Access-Control-Request-Method', 'PUT'), ('Origin', 'http://localhost'))
        app.options('/api/1/walls/123', status=200, headers=headers)

    def test_collection_options(self):
        wsgiapp = self.config.make_wsgi_app()
        app = TestApp(wsgiapp)
        request = testing.DummyRequest()
        apply_request_extensions(request)
        self._fixture(request)
        headers = (('Access-Control-Request-Method', 'POST'), ('Origin', 'http://localhost'))
        app.options('/api/1/walls', status=200, headers=headers)


class FunctionalWallStructureAPIViewTests(TestCase):

    def setUp(self):
        self.config = testing.setUp(settings=get_settings())
        self.config.include('kedja.testing')
        self.config.include('pyramid_tm')
        self.config.include('kedja.views.api.walls')
        self.config.testing_securitypolicy(permissive=True)

    def _fixture(self, request):
        from kedja import root_factory
        content = request.registry.content
        root = root_factory(request)
        root['wall'] = wall = content('Wall', rid=2)
        for i in range(1, 4):
            wall['col%s' % i] = collection = content('Collection', rid=i*10)
            for j in range(1, 4):
                collection['card%s' % j] = content('Card', rid=j*100+i)
        commit()
        return root

    def test_get(self):
        wsgiapp = self.config.make_wsgi_app()
        app = TestApp(wsgiapp)
        request = testing.DummyRequest()
        apply_request_extensions(request)
        self._fixture(request)
        response = app.get('/api/1/walls/2/structure', status=200)
        expected = [
            [10, [
                [101, []], [201, []], [301, []]
            ]],
            [20, [
                [102, []], [202, []], [302, []]
            ]],
            [30, [
                [103, []], [203, []], [303, []]
            ]]
        ]
        self.assertEqual(response.json_body, expected)


class FunctionalWallContentAPIViewTests(TestCase):

    def setUp(self):
        self.config = testing.setUp(settings=get_settings())
        self.config.include('kedja.testing')
        self.config.include('pyramid_tm')
        self.config.include('kedja.views.api.walls')
        self.config.testing_securitypolicy(permissive=True)

    def _fixture(self, request):
        from kedja import root_factory
        root = root_factory(request)
        content = self.config.registry.content
        root['wall'] = wall = content('Wall', rid=2)
        results = {}
        for i in range(1, 4):
            wall['col%s' % i] = collection = content('Collection', rid=i*10)
            results[collection.rid] = collection
            for j in range(1, 4):
                collection['card%s' % j] = card = content('Card', rid=j*100+i)
                results[card.rid] = card
        commit()
        return {'resources': results}

    def test_get(self):
        wsgiapp = self.config.make_wsgi_app()
        app = TestApp(wsgiapp)
        request = testing.DummyRequest()
        apply_request_extensions(request)
        content = self._fixture(request)
        response = app.get('/api/1/walls/2/content', status=200)
        converted = render('json', content, request=request)
        expected = loads(converted)
        self.assertEqual(response.json_body, expected)


class FunctionalACLAPIViewTests(TestCase):

    def setUp(self):
        self.config = testing.setUp(settings=get_settings())
        self.config.include('kedja.testing')
        self.config.include('pyramid_tm')
        self.config.include('kedja.views.api.walls')
        self.config.include('kedja.security.default_acl')
        self.config.testing_securitypolicy(permissive=True)

    def _fixture(self, request):
        from kedja import root_factory
        root = root_factory(request)
        content = self.config.registry.content
        root['wall'] = wall = content('Wall', rid=2)
        commit()
        return wall

    def test_get(self):
        wsgiapp = self.config.make_wsgi_app()
        app = TestApp(wsgiapp)
        request = testing.DummyRequest()
        apply_request_extensions(request)
        self.config.begin(request)
        self._fixture(request)
        response = app.get('/api/1/walls/2/acl', status=200)
        self.assertEqual(1, sum([x['active'] for x in response.json_body]))
        self.assertIn('private_wall', [x['name'] for x in response.json_body])

    def test_put(self):
        wsgiapp = self.config.make_wsgi_app()
        app = TestApp(wsgiapp)
        request = testing.DummyRequest()
        apply_request_extensions(request)
        self.config.begin(request)
        wall = self._fixture(request)
        body = dumps({'acl_name': 'public_wall'})
        self.assertEqual(wall.acl_name, 'private_wall')
        response = app.put('/api/1/walls/2/acl', params=body, status=200)
        self.assertEqual(response.json_body, {'acl_name': 'public_wall'})
        self.assertEqual(wall.acl_name, 'public_wall')

    def test_put_no_data(self):
        wsgiapp = self.config.make_wsgi_app()
        app = TestApp(wsgiapp)
        request = testing.DummyRequest()
        apply_request_extensions(request)
        self.config.begin(request)
        self._fixture(request)
        body = ""
        response = app.put('/api/1/walls/2/acl', params=body, status=400)
        self.assertEqual(response.status_int, 400)

    def test_put_bad_data(self):
        wsgiapp = self.config.make_wsgi_app()
        app = TestApp(wsgiapp)
        request = testing.DummyRequest()
        apply_request_extensions(request)
        self.config.begin(request)
        self._fixture(request)
        body = dumps({'acl_name': 'something_that_doesnt_exist'})
        response = app.put('/api/1/walls/2/acl', params=body, status=400)
        self.assertEqual(response.status_int, 400)
