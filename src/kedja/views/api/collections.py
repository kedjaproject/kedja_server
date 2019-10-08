import colander
from cornice.resource import resource
from cornice.validators import colander_validator
from cornice.resource import view

from kedja.resources.collection import CollectionSchema
from kedja.utils import validate_schema
from kedja.views import validators
from kedja.views.api.base import SubResourceAPISchema
from kedja.views.api.base import ResourceAPIBase
from kedja.views.api.base import ResourceAPISchema


class CreateCollectonSchema(ResourceAPISchema):
    title = "Create a new collection"
    body = CollectionSchema(description="JSON payload")

    def after_bind(self, node, kw):
        """ Use this instead of deferred, since cornice can't handle schema binding. """
        pass


class UpdateCollectionAPISchema(SubResourceAPISchema, CreateCollectonSchema):
    title = "Update a specific collection"

    def after_bind(self, node, kw):
        """ Use this instead of deferred, since cornice can't handle schema binding. """
        pass


@resource(collection_path='/api/1/walls/{rid}/collections',
          path='/api/1/walls/{rid}/collections/{subrid}',  # This isn't used, but cornice needs  this path?
          tags=['Collections'],
          validators=(colander_validator,),
          cors_origins=('*',),
          factory='kedja.root_factory')
class ContainedCollectionsAPI(ResourceAPIBase):
    type_name = 'Collection'
    parent_type_name = 'Wall'

    @view(schema=SubResourceAPISchema(), validators=(colander_validator, validators.VIEW_CONTAINED_RESOURCE))
    def get(self):
        wall = self.base_get(self.request.matchdict['rid'], type_name=self.parent_type_name)
        if wall:
            return self.contained_get(wall, self.request.matchdict['subrid'], type_name=self.type_name)

    @view(schema=UpdateCollectionAPISchema(), validators=(colander_validator, validators.EDIT_CONTAINED_RESOURCE))
    def put(self):
        return self.base_put(self.request.matchdict['subrid'], type_name=self.type_name)

    @view(schema=SubResourceAPISchema(), validators=(colander_validator, validators.DELETE_CONTAINED_RESOURCE))
    def delete(self):
        return self.base_delete(self.request.matchdict['subrid'], type_name=self.type_name)

    @view(schema=ResourceAPISchema(), validators=(colander_validator, validators.VIEW_RESOURCE))
    def collection_get(self):
        parent = self.base_get(self.request.matchdict['rid'], type_name=self.parent_type_name)
        return self.base_collection_get(parent, type_name=self.type_name)

    @view(schema=CreateCollectonSchema(), validators=(colander_validator, validators.ADD_COLLECTION))
    def collection_post(self):
        return self.base_collection_post(self.type_name, parent_rid=self.request.matchdict['rid'], parent_type_name=self.parent_type_name)



class CardOrderSchema(colander.Schema):
    order = colander.SchemaNode(
        colander.Sequence(),
        colander.SchemaNode(
            colander.Int(),
            preparer=str,  # We change the type to str later to get the correct names for ordering
        )
    )

    def after_bind(self, node, kw):
        """ Use this instead of deferred, since cornice can't handle schema binding. """
        node['order'].validator = ValidateCardOrder(node, kw)


class CollectionCardOrderSchema(ResourceAPISchema):
    title = "Update card order"
    body = CardOrderSchema(description="JSON payload")


class ValidateCardOrder(object):

    def __init__(self, node, kw):
        self.collection = kw['collection']

    def __call__(self, node, value):
        names = self.collection.keys()
        if set(names) != set(value):
            raise colander.Invalid(node, "Must specify all names when changing order")



@resource(path='/api/1/collections/{rid}/order',
          cors_origins=('*',),
          tags=['Collections'],
          factory='kedja.root_factory')
class CollectionsOrderingAPIView(ResourceAPIBase):
    type_name = 'Collection'

    @view(schema=CollectionCardOrderSchema(), validators=(colander_validator, validators.EDIT_RESOURCE))
    def put(self):
        """ Set the order of the contained cards.
            Returns the cards, same as the view to fetch collection content. (As in .cards)
        """
        collection = self.base_get(self.request.matchdict['rid'], type_name=self.type_name)
        if collection is not None:
            appstruct = self.get_json_appstruct()
            schema = CardOrderSchema().bind(request=self.request, context=self.context, collection=collection)
            validated = validate_schema(schema, appstruct)
            # FIXME: Fire event?
            collection.order = validated['order']
            return self.base_collection_get(collection, type_name='Card')


def includeme(config):
    config.scan(__name__)
