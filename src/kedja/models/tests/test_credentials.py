from unittest import TestCase

from pyramid import testing
from pyramid.authentication import extract_http_basic_credentials
from pyramid.authentication import HTTPBasicCredentials
from pyramid.request import apply_request_extensions
from zope.interface.verify import verifyObject

from kedja.interfaces import ICredentials


class CredentialsTests(TestCase):

    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    @property
    def _cut(self):
        from kedja.models.credentials import Credentials
        return Credentials

    def _fixture(self, request):
        from kedja.models.appmaker import root_populator
        from kedja.resources.root import Root
        root = Root()
        root_populator(root, request)
        return root

    def test_header(self):
        obj = self._cut('1', token="123")
        self.assertEqual(obj.header(), "Basic MToxMjM=")

    def test_compat_with_pyramid(self):
        obj = self._cut('1', token="123")
        request = testing.DummyRequest()
        request.headers['Authorization'] = obj.header()
        results = extract_http_basic_credentials(request)
        expected = HTTPBasicCredentials(username='1', password='123')
        self.assertIsInstance(results, HTTPBasicCredentials)
        self.assertEqual(results, expected)

    def test_json(self):
        self.config.include('kedja.testing')
        request = testing.DummyRequest()
        root = self._fixture(request)
        apply_request_extensions(request)
        request.root = root
        obj = self._cut('1', token="123")
        results = obj.__json__(request)
        self.assertEqual(results['Authorization'], obj.header())
        self.assertEqual(results['userid'], '1')

    def test_iface(self):
        obj = self._cut('1', token="123")
        self.assertTrue(verifyObject(ICredentials, obj))
