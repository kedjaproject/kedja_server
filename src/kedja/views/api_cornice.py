from cornice.resource import resource as cornice_resource
from cornice.resource import view as cornice_view


class ResourceAPIBase(object):

    def __init__(self, request, root=None):
        self.request = request
        self.root = root
        import pdb;pdb.set_trace()
        self._lookup_cache = {}

    def get_resource(self, rid):
        if isinstance(rid, str):
            try:
                rid = int(rid)
            except ValueError:
                return self.error(self.request, "Supplied RID is not a valid integer", status=400)
        return self._lookup_cache.setdefault(rid, self.request.root.rid_map.get_resource(rid))

    def error(self, request, msg="Doesn't exist", type='path', status=404):
        request.errors.add(type, msg)
        request.errors.status = status

    def validate_type_name(self, request, **kw):
        type_name = request.matchdict.get('type_name', object())
        if type_name not in request.registry.content:
            return self.error(request, msg="'type_name' specified doesn't exist.")

    def validate_rid(self, request, **kw):
        """ RID must be numeric and exist. """
        try:
            rid = int(self.request.matchdict['rid'])
        except ValueError:
            return self.error(request, "rid must be numeric", status=400)
        if self.get_resource(rid) is None:
            return self.error(request, "No resource with that rid exists")

    def validate_type_name(self, request, **kw):
        type_name = request.matchdict['type_name']
        if type_name not in request.registry.content:
            return self.error(request, "No resource called %s" % type_name)

    def base_get(self):
        """ Get specific resource """
        return self.get_resource(self.request.matchdict['rid'])

    def base_put(self):
        """ Update a resource """
        rid = self.request.matchdict['rid']
        resource = self.get_resource(rid)
        # FIXME: json decoding errors
        appstruct = self.request.json_body
        # Note: The mutator API will probably change!
        with self.request.get_mutator(resource) as mutator:
            changed = mutator.update(appstruct)
        # Log changed
        return resource

    def base_delete(self):
        """ Delete a resource """
        rid = self.request.matchdict['rid']
        resource = self.get_resource(rid)
        parent = resource.__parent__
        parent.remove(resource.__name__)
        return {'removed': rid}


# Cornice doesn't respect pyramids root factory - beware!
@cornice_resource(path='/api/1/rid/{rid}',
                  validators=('validate_rid',), factory='kedja.root_factory')
class ResourceAPI(ResourceAPIBase):
    """ Resources """

    #def __acl__(self):
    #    return [(Allow, Everyone, 'everything')]

    def get(self):
        return self.base_get()

    def put(self):
        return self.base_put()

    def delete(self):
        return self.base_delete()


@cornice_resource(path='/api/1/walls/{rid}', collection_path='/api/1/walls', factory='kedja.root_factory')
class WallsAPI(ResourceAPIBase):
    """ Resources """

    #def __acl__(self):
    #    return [(Allow, Everyone, 'everything')]

    @cornice_view(validators=('validate_rid',))
    def get(self):
        resource = self.base_get()
        # FIXME: Check type
        return resource

    @cornice_view(validators=('validate_rid',))
    def put(self):
        return self.base_put()

    @cornice_view(validators=('validate_rid',))
    def delete(self):
        return self.base_delete()

    def collection_get(self):
        return list(self.context.values())

    def collection_post(self):
        new_res = self.request.registry.content("Wall")
        new_res.rid = self.root.rid_map.new_rid()
        # Should be the root
        self.context.add(str(new_res.rid), new_res)
        # FIXME: json decoding errors
        appstruct = self.request.json_body
        # Note: The mutator API will probably change!
        with self.request.get_mutator(new_res) as mutator:
            changed = mutator.update(appstruct)
        self.request.response.status = 202  # Accepted
        return {'changed': list(changed)}


class ContainedAPI(ResourceAPIBase):

    def collection_get(self):
        return list(self.context.values())

    def collection_post(self):
        new_res = self.request.registry.content("Wall")
        new_res.rid = self.root.rid_map.new_rid()
        # Should be the root
        self.context.add(str(new_res.rid), new_res)
        # FIXME: json decoding errors
        appstruct = self.request.json_body
        # Note: The mutator API will probably change!
        with self.request.get_mutator(new_res) as mutator:
            changed = mutator.update(appstruct)
        return {'changed': list(changed)}


# Cornice can't decorate the same class, hence this

@cornice_resource(collection_path='/api/1/walls/{rid}/collections',
                  path='/api/1/walls/{rid}/collections/{subrid}',
                  factory='kedja.root_factory')
class ContainedCollectionsAPI(ContainedAPI):
    pass


@cornice_resource(collection_path='/api/1/collections/{rid}/cards',
                  path='/api/1/collections/{rid}/cards/{subrid}',
                  factory='kedja.root_factory')
class ContainedCardsAPI(ContainedAPI):
    pass



"""
URL	Description
/api	The API entry point
/api/:coll	A top-level collection named “coll”
/api/:coll/:id	The resource “id” inside collection “coll”
/api/:coll/:id/:subcoll	Sub-collection “subcoll” under resource “id”
/api/:coll/:id/:subcoll/:subid	The resource “subid” inside “subcoll”
GET	collection	Retrieve all resources in a collection
GET	resource	Retrieve a single resource
HEAD	collection	Retrieve all resources in a collection (header only)
HEAD	resource	Retrieve a single resource (header only)
POST	collection	Create a new resource in a collection
PUT	resource	Update a resource
PATCH	resource	Update a resource
DELETE	resource	Delete a resource
OPTIONS	any	Return available HTTP methods and other options
"""

def includeme(config):
    config.scan(__name__)