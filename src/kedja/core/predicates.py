from abc import ABC, abstractmethod

from zope.interface import Interface


class SubscriberObjectPredicate(ABC):

    @property
    @abstractmethod
    def attribute(self):
        pass

    def __init__(self, val, config):
        self.val = val
        self.resolved_val = config.maybe_dotted(val)
        self.is_iface = False
        if issubclass(self.resolved_val, Interface):
            self.is_iface = True

    def text(self):
        return '%s = %s' % (self.attribute, self.val,)
    phash = text

    def __call__(self, event):
        event_obj = getattr(event, self.attribute, None)
        if self.is_iface:
            return self.resolved_val.providedBy(event_obj)
        return isinstance(event_obj, self.resolved_val)


class _SubscriberSchemaPredicate(SubscriberObjectPredicate):
    """ This is instead of the object events used with zope.
        So rather than doing
        config.add_subscriber(callable, [SchemaClass, EventIface])

        We can do this:
        config.add_subscriber(callable, EventIface, schema=SchemaClass)

        It will behave the same way as add_view that way.
    """
    attribute = 'schema'


class _SubscriberContextPredicate(SubscriberObjectPredicate):
    """ Fires only the context attribute exists on the event, and that matches.
        This may be used as a replacement for the object event that's part of the Zope component architechture.

        Note that context may be the same as the object attribute, meaning events that take place
        for a persistent resource.
    """
    attribute = 'context'


def includeme(config):
    config.add_subscriber_predicate('schema', _SubscriberSchemaPredicate)
    config.add_subscriber_predicate('context', _SubscriberContextPredicate)
