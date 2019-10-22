from random import randrange

from BTrees import family64
from persistent import Persistent
from pyramid.httpexceptions import HTTPNotFound
from pyramid.traversal import find_resource
from pyramid.traversal import resource_path_tuple

from kedja.interfaces import IResource


class ResourceIDMap(Persistent):
    """ Maps resource id and path tuple. Essentially a way to make indexing, referencing and similar more lightweight.
    """
    family = family64

    def __init__(self, root):
        self.root = root
        # we can use either: self.family.minint, self.family.maxint
        # or the max int javascript can handle, which is 2**53-1
        self._maxint = 2**53-1
        self._minint = -self._maxint
        self.rid_to_path = self.family.IO.BTree()
        self.path_to_rid = self.family.OI.BTree()
        self.add(root)

    def __getitem__(self, rid):
        return self.rid_to_path[rid]

    def __contains__(self, item):
        if isinstance(item, int):
            return item in self.rid_to_path
        if isinstance(item, tuple):
            return item in self.path_to_rid
        if IResource.providedBy(item):
            rid = item.get_rid()
            return rid and rid in self.rid_to_path
        return False

    def get(self, rid, default=None):
        return self.rid_to_path.get(rid, default)

    def get_rid(self, path_tuple:tuple, default=None):
        """ Use get_rid on any resource instead of this if you simply want to get the rid and have the resource.
            If you have the path, this is the correct way to do a lookup.
        """
        return self.path_to_rid.get(path_tuple, default)

    def get_resource(self, rid, default=None):
        try:
            path_tuple = self.rid_to_path[rid]
            return find_resource(self.root, path_tuple)
        except KeyError:
            return default

    def get_resource_or_404(self, rid):
        resource = self.get_resource(rid)
        if resource is None:
            raise HTTPNotFound("Can't find any resource with the ID %r" % rid)
        return resource

    def new_rid(self):
        """ Get an unused ID. It's not reserved in any way, so make sure to use it within the current transaction.
            In the unlikely case that the same ID would be used, a transaction error will occur.
        """
        rid = None
        while not rid:  # We don't like 0 either
            rid = randrange(self._minint, self._maxint)
            if rid in self.rid_to_path:
                rid = None
        return rid

    def check_rids(self, resource, reset:bool=False):
        """ Walk through object tree and make sure all objects have an RID. """
        if IResource.providedBy(resource):
            if reset or not resource.rid:
                resource.rid = self.new_rid()
            for contained in resource.values():
                self.check_rids(contained, reset=reset)

    def add(self, resource):
        """ Add a new resource too the map. It must already be attached to the resource tree.
        """
        self._check_resource(resource)
        path_tuple = resource_path_tuple(resource)
        rid = resource.get_rid()
        if rid is None:
            rid = self.new_rid()
            resource.set_rid(rid)
        # check if resource already exist
        path_exist = path_tuple in self
        rid_exist = rid in self
        if path_exist and not rid_exist:
            raise ValueError('rid_exist %s already exists' % (path_tuple,))
        elif rid_exist and not path_exist:
            raise ValueError('ID %s already exists' % (rid,))
        elif path_exist and rid_exist:
            # Already exist, simply pass
            pass
        else:
            self.path_to_rid[path_tuple] = rid
            self.rid_to_path[rid] = path_tuple
        for contained in resource.values():
            self.add(contained)
        return rid

    def __delitem__(self, rid:int):
        to_remove = self.contained_rids(rid)
        to_remove.add(rid)
        for ridx in to_remove:
            remove_path = self.rid_to_path[ridx]
            del self.path_to_rid[remove_path]
            del self.rid_to_path[ridx]

    def contained_rids(self, item):
        """ Return any rids within this object, id or path tuple.
            It might be a good idea to cache this later.
        """
        if isinstance(item, int):
            rid = item
        elif isinstance(item, tuple):
            rid = self.get_rid(item)
        elif IResource.providedBy(item):
            rid = item.get_rid()
        path_tuple = self[rid]
        root_node_len = len(path_tuple)
        found = set()
        for (ptuple, id) in self.path_to_rid.items():
            if len(ptuple) > root_node_len:
                if ptuple[:root_node_len] == path_tuple:
                    found.add(id)
        return found

    def _check_resource(self, resource):
        if not IResource.providedBy(resource):
            raise TypeError("Not a resource, must provide kedja.interfaces.IResource")
        if resource.__parent__ is None and resource is not self.root:
            raise ValueError("Resource isn't attached to the root.")
