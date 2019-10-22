from unittest import TestCase

import colander
from pyramid import testing

from kedja.interfaces import ISchemaBound


class DummySchema(colander.Schema):
    pass


class SchemaIntegrationTests(TestCase):

    def setUp(self):
        self.config = testing.setUp()
        self.config.include('kedja.core.schemas')

    def tearDown(self):
        testing.tearDown()

    def test_patched_method(self):
        L = []

        def subs(event):
            L.append(event)

        self.config.add_subscriber(subs, ISchemaBound)
        schema = DummySchema()
        schema = schema.bind(hello='world')
        self.assertEqual(len(L), 1)
        self.assertIs(L[0].schema, schema)
        self.assertEqual(L[0].hello, 'world')
