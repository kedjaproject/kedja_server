import colander
from kedja import logger
from kedja.events.resource import ResourceUpdated
from kedja.interfaces import IResource
from kedja.utils import validate_appstruct
from pyramid.threadlocal import get_current_registry


_MARKER = object()


class Mutator(object):

    def __init__(self, resource, schema, send_events=True, registry=None, event_factory=ResourceUpdated):
        assert IResource.providedBy(resource)
        assert isinstance(schema, colander.SchemaNode)
        self.resource = resource
        self.schema = schema
        self.send_events = send_events
        self.changed = set()
        if registry is None:
            registry = get_current_registry()
        self.registry = registry
        self.event_factory = event_factory

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.send_events:
            self.notify()

    @property
    def has_changed(self):
        return bool(self.changed)

    def notify(self):
        """ Send ResourceUpdated event or something similar if the resource has been updated.
            'always' means always send event regardless of changes
        """
        if self.has_changed:
            event = self.event_factory(self.resource, registry=self.registry, schema=self.schema,
                                       changed=self.changed)
            self.registry.notify(event)

    def validate(self, appstruct):
        return validate_appstruct(self.schema, appstruct)

    def appstruct(self, strict=False):
        appstruct = {}
        for field in self.schema.children:
            val = getattr(self.resource, field.name, _MARKER)
            if val is _MARKER:
                if strict:
                    val = field.default
            if val is not _MARKER:
                appstruct[field.name] = val
        if strict:
            try:
                appstruct = self.validate(appstruct)
            except colander.Invalid as exc:
                for k in exc.asdict():
                    appstruct.pop(k, None)
        return appstruct

    def update(self, appstruct=None, **kw):
        data = {}
        if appstruct is not None:
            data.update(appstruct)
        data.update(kw)
        validated = self.validate(data)
        dropped = set(data) - set(validated)
        if dropped:
            logger.warning("The following keys were not part of the schema: '{}'".format("','".join(dropped)))
        changed_now = set()
        for (k, v) in validated.items():
            if v == colander.null:
                continue
            curr_val = getattr(self.resource, k, object())
            if curr_val != v:
                setattr(self.resource, k, v)
                changed_now.add(k)
        self.changed.update(changed_now)
        if self.send_events:
            self.notify()
        return changed_now
