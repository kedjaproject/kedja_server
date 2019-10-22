import BTrees
from BTrees.Length import Length
from persistent import Persistent
from pyramid.threadlocal import get_current_registry
from zope.interface import implementer
from zope.copy import copy

from kedja.core import get_rid_map
from kedja.events import ResourceWillBeAdded, ResourceRemoved, ResourceWillBeRemoved
from kedja.events import ResourceAdded
from kedja.resources.mixins import ResourceMixin
from kedja.interfaces import IFolder


_MARKER = object()


@implementer(IFolder)
class Folder(Persistent, ResourceMixin):
    """ A folder implementation which acts much like a Python dictionary.

    Keys must be Unicode strings; values must be things addable to the resource tree.
    """

    __name__ = None
    __parent__ = None
    # Default uses ordering of underlying BTree.
    _order = None  # tuple of names
    _order_rids = None  # tuple of rids

    def __init__(self, appstruct=_MARKER, **kw):
        self.data = BTrees.family64.OO.BTree()
        self._num_objects = Length()
        if appstruct is not _MARKER:
            assert isinstance(appstruct, dict)
            kw.update(appstruct)
        for (k, v) in kw.items():
            setattr(self, k, v)

    def set_order(self, names):
        """ Sets the folder order. ``names`` is a list of names for existing
        folder items, in the desired order.  All names that currently exist in
        the folder must be mentioned in ``names``, or a :exc:`ValueError` will
        be raised.
        """
        nameset = set(names)
        if len(names) != len(nameset):
            raise ValueError("No repeated items allowed in names")
        if nameset != set(self.keys()):
            raise ValueError("Must specify all names when calling set_order")

        order = []
        order_rids = []

        for name in names:
            assert isinstance(name, str)
            order.append(name)
            rid = self[name].rid
            assert rid, "Must not be falsy"
            order_rids.append(rid)

        self._order = tuple(order)
        self._order_rids = tuple(order_rids)

    def del_order(self):
        """ Remove set order from a folder, making it unordered, and
        non-reorderable."""
        if self._order is not None:
            del self._order
        if self._order_rids is not None:
            del self._order_rids

    def is_ordered(self):
        """ Return true if the folder has a manually set ordering, false
        otherwise."""
        return self._order is not None

    def keys(self):
        """ Return an iterable sequence of object names present in the folder.

        Respect order, if set.
        """
        if self.is_ordered():
            return self._order
        return self.data.keys()

    order = property(keys, set_order, del_order)

    def get_order_rids(self, default=None):
        """ Return the ordering according to resource IDs.
        """
        if self.is_ordered():
            return self._order_rids
        return default

    def __iter__(self):
        """ An alias for ``keys``
        """
        return iter(self.keys())

    def values(self):
        """ Return an iterable sequence of the values present in the folder.

        Respect ``order``, if set.
        """
        if self._order is not None:
            return [self.data[name] for name in self.keys()]
        return self.data.values()

    def items(self):
        """ Return an iterable sequence of (name, value) pairs in the folder.

        Respect ``order``, if set.
        """
        if self.is_ordered():
            return [(name, self.data[name]) for name in self.keys()]
        return self.data.items()

    def __len__(self):
        """ Return the number of objects in the folder.
        """
        return self._num_objects()

    def __nonzero__(self):
        """ Return ``True`` unconditionally.
        """
        return True

    __bool__ = __nonzero__

    def __repr__(self):
        klass = self.__class__
        classname = "%s.%s" % (klass.__module__, klass.__name__)
        return "<%s object %r at %#x>" % (classname, self.__name__, id(self))

    def add(
        self,
        name: str,
        resource,
        send_events: bool = True,
        duplicating=None,
        moving=None,
        registry=None,
    ):
        """
        If ``send_events`` is False, suppress the sending of folder events.

        If ``duplicating`` not ``None``, it must be the object which is being
        duplicated; a result of a non-``None`` duplicating means that rrids will
        be replaced in objectmap.  If ``moving`` is not ``None``, it must be
        the folder from which the object is moving; this will be the ``moving``
        attribute of events sent by this function too.
        """

        if duplicating is not None and moving is not None:
            raise ValueError(
                "A resource can't move and be duplicated at the same time."
            )

        if registry is None:
            registry = get_current_registry()

        if getattr(resource, "__parent__", None):
            raise ValueError(
                "obj %s added to folder %s already has a __parent__ attribute, "
                "please remove it completely from its existing parent (%s) "
                "before trying to readd it to this one"
                % (resource, self, self.__parent__)
            )

        if name in self:
            raise KeyError(
                "%s already contains a resource with the name %r" % (self, name)
            )

        rid_map = get_rid_map(self)
        if rid_map is not None:
            # Make surer the rid exist. If this is a new instance of an existing object, reset all contained rids
            rid_map.check_rids(resource, reset=duplicating is not None)

        if send_events:
            event = ResourceWillBeAdded(
                resource,
                parent=self,
                name=name,
                duplicating=duplicating,
                moving=moving,
                registry=registry,
            )
            registry.notify(event)

        resource.__parent__ = self
        resource.__name__ = name

        self.data[name] = resource
        self._num_objects.change(1)

        if self.is_ordered():
            rid = resource.get_rid()
            assert rid, "Must exist for resource objects"
            self._order += (name,)
            self._order_rids += (rid,)

        if rid_map is not None:
            rid_map.add(resource)

        if send_events:
            if rid_map is not None:
                contained_rids = rid_map.contained_rids(resource)
            else:
                contained_rids = None
            event = ResourceAdded(
                resource,
                parent=self,
                name=name,
                duplicating=duplicating,
                moving=moving,
                contained_rids=contained_rids,
                registry=registry,
            )
            registry.notify(event)

        return name

    def __setitem__(self, name, resource):
        return self.add(name, resource)

    def __getitem__(self, name: str):
        return self.data[name]

    def get(self, name: str, default=None):
        if name in self:
            return self[name]
        return default

    def remove(self, name: str, send_events=True, moving=None, registry=None):
        """ Same thing as ``__delitem__``.

        If ``send_events`` is false, suppress the sending of folder events.

        If ``moving`` is not ``None``, the ``moving`` argument must be the
        folder to which the named object will be moving.  This value will be
        passed along as the ``moving`` attribute of the events sent as the
        result of this action.  If ``loading`` is ``True``, the ``loading``
        attribute of events sent as a result of calling this method will be
        ``True`` too.
        """
        resource = self.data[name]

        if registry is None:
            registry = get_current_registry()

        rid_map = get_rid_map(self)
        if rid_map is not None:
            contained_rids = rid_map.contained_rids(self[name])
        else:
            contained_rids = None

        if send_events:
            event = ResourceWillBeRemoved(
                resource,
                parent=self,
                name=name,
                moving=moving,
                contained_rids=contained_rids,
                registry=registry,
            )
            registry.notify(event)

        if hasattr(resource, "__parent__"):
            try:
                del resource.__parent__
            except AttributeError:  # pragma: no cover
                # this might be a broken object
                pass

        if hasattr(resource, "__name__"):
            try:
                del resource.__name__
            except AttributeError:  # pragma: no cover
                # this might be a broken object
                pass

        del self.data[name]
        self._num_objects.change(-1)

        # del will clean up contained too
        if resource.rid and rid_map is not None:
            del rid_map[resource.rid]

        if self.is_ordered():
            order = list(self._order)
            order.remove(name)
            self._order = tuple(order)
            order_rids = list(self._order_rids)
            rid = resource.get_rid()
            order_rids.remove(rid)
            self._order_rids = tuple(order_rids)

        if send_events:
            event = ResourceRemoved(
                resource, parent=self, name=name, moving=moving, registry=registry
            )
            registry.notify(event)

        return resource

    def __delitem__(self, name):
        return self.remove(name)

    def copy(self, name: str, newparent, newname: str = None, registry=None):
        """
        Copy a subobject named ``name`` from this folder to the folder
        represented by ``newparent``.  If ``newname`` is not none, it is used as
        the target object name; otherwise the existing subobject name is
        used.
        """
        if newname is None:
            if self is newparent:
                raise ValueError(
                    "You must specify newname if you create a copy in the same folder."
                )
            newname = name

        obj = self[name]
        newobj = copy(obj)
        return newparent.add(newname, newobj, duplicating=obj, registry=registry)

    def move(self, name: str, newparent, newname: str = None, registry=None):
        """
        Move a subobject named ``name`` from this folder to the folder
        represented by ``newparent``.  If ``newname`` is not none, it is used as
        the target object name; otherwise the existing subobject name is
        used.

        This operation is done in terms of a remove and an add.  The Removed
        and WillBeRemoved events as well as the Added and WillBeAdded events
        sent will indicate that the object is moving.
        """
        if newname is None:
            newname = name
        if registry is None:
            registry = get_current_registry()
        ob = self.remove(name, moving=newparent, registry=registry)
        newparent.add(newname, ob, moving=self, registry=registry)
        return ob

    def rename(self, oldname: str, newname: str, registry=None):
        """
        Rename a subobject from oldname to newname.

        This operation is done in terms of a remove and an add.  The Removed
        and WillBeRemoved events sent will indicate that the object is
        moving.
        """
        return self.move(oldname, self, newname, registry=registry)
