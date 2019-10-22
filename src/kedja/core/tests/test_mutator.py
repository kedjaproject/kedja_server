from unittest import TestCase

import colander
from pyramid import testing
from zope.interface import implementer

from kedja.interfaces import IResource, IResourceUpdated


@implementer(IResource)
class DummyContent(testing.DummyResource):
    pass


class DummyContentSchema(colander.Schema):
    title = colander.SchemaNode(colander.String())
    with_default = colander.SchemaNode(colander.String(), default="me default")
    nodefault = colander.SchemaNode(colander.Int())


class MutatorTests(TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    @property
    def _cut(self):
        from kedja.core.mutator import Mutator

        return Mutator

    def test_notify(self):
        obj = self._cut(DummyContent(), DummyContentSchema())
        obj.registry = self.config.registry
        L = []

        def subscriber(event):
            L.append(event)

        self.config.add_subscriber(subscriber, IResourceUpdated)
        obj.notify()
        self.assertEqual(len(L), 0)
        obj.changed.add("something")
        obj.notify()
        self.assertEqual(len(L), 1)

    def test_validate_no_data(self):
        obj = self._cut(DummyContent(), DummyContentSchema())
        self.assertRaises(colander.Invalid, obj.validate, {})

    def test_validate_sane_data(self):
        obj = self._cut(DummyContent(), DummyContentSchema())
        self.assertEqual(
            obj.validate({"title": "Hello", "with_default": "What", "nodefault": "1"}),
            {"title": "Hello", "with_default": "What", "nodefault": 1},
        )

    def test_validate_default(self):
        obj = self._cut(DummyContent(), DummyContentSchema())
        self.assertEqual(
            obj.validate({"title": "Hello", "nodefault": "1"}),
            {"title": "Hello", "with_default": "me default", "nodefault": 1},
        )

    def test_appstruct_empty(self):
        obj = self._cut(DummyContent(), DummyContentSchema())
        self.assertEqual(obj.appstruct(), {})

    def test_appstruct_has_data(self):
        resource = DummyContent()
        resource.title = "Hello world"
        resource.nodefault = "Should be int"
        obj = self._cut(resource, DummyContentSchema())
        self.assertEqual(
            obj.appstruct(), {"title": "Hello world", "nodefault": "Should be int"}
        )

    def test_appstruct_strict(self):
        resource = DummyContent()
        resource.title = "Hello world"
        resource.nodefault = "Should be int"
        obj = self._cut(resource, DummyContentSchema())
        self.assertEqual(
            obj.appstruct(strict=True),
            {"title": "Hello world", "with_default": "me default"},
        )

    def test_update(self):
        resource = DummyContent()
        obj = self._cut(resource, DummyContentSchema())
        obj.update(title="Hello", nodefault="123")
        self.assertEqual(resource.nodefault, 123)

    def test_update_missing_required(self):
        resource = DummyContent()
        obj = self._cut(resource, DummyContentSchema())
        self.assertRaises(colander.Invalid, obj.update, title="Hello")

    def test_colander_drops_on_update(self):
        class SchemaWDrop(DummyContentSchema):
            title = colander.SchemaNode(colander.String(), missing=colander.drop)

        resource = DummyContent()
        obj = self._cut(resource, SchemaWDrop())
        self.assertEqual(obj.update(nodefault=3), {"nodefault", "with_default"})

    def test_never_save_null_on_update(self):
        class SchemaWNull(DummyContentSchema):
            title = colander.SchemaNode(colander.String(), missing=colander.null)

        resource = DummyContent()
        obj = self._cut(resource, SchemaWNull())
        result = obj.update(nodefault=3)
        self.assertEqual(result, {"nodefault", "with_default"})
        self.failIf(hasattr(resource, "title"))
