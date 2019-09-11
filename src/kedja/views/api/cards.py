from cornice.resource import resource
from cornice.resource import view
from cornice.validators import colander_validator

from kedja.resources.card import CardSchema
from kedja.views import validators
from kedja.views.api.base import ResourceAPIBase
from kedja.views.api.base import SubResourceAPISchema
from kedja.views.api.base import ResourceAPISchema


class CreateCardSchema(ResourceAPISchema):
    title = "Create a new card"
    body = CardSchema(description="JSON payload")


class UpdateCardAPISchema(SubResourceAPISchema, CreateCardSchema):
    title = "Update a specific card"


@resource(collection_path='/api/1/collections/{rid}/cards',
          path='/api/1/collections/{rid}/cards/{subrid}',  # This isn't used, but cornice needs this path?
          tags=['Cards'],
          validators=(colander_validator,),
          cors_origins=('*',),
          factory='kedja.root_factory')
class ContainedCardsAPI(ResourceAPIBase):
    type_name = 'Card'
    parent_type_name = 'Collection'

    @view(schema=SubResourceAPISchema(), validators=(colander_validator, validators.VIEW_CONTAINED_RESOURCE))
    def get(self):
        collection = self.base_get(self.request.matchdict['rid'], type_name=self.parent_type_name)
        if collection:
            return self.contained_get(collection, self.request.matchdict['subrid'], type_name=self.type_name)

    @view(schema=UpdateCardAPISchema(), validators=(colander_validator, validators.EDIT_CONTAINED_RESOURCE))
    def put(self):
        return self.base_put(self.request.matchdict['subrid'], type_name=self.type_name)

    @view(schema=SubResourceAPISchema(), validators=(colander_validator, validators.DELETE_CONTAINED_RESOURCE))
    def delete(self):
        return self.base_delete(self.request.matchdict['subrid'], type_name=self.type_name)

    @view(schema=ResourceAPISchema(), validators=(colander_validator, validators.VIEW_RESOURCE))
    def collection_get(self):
        parent = self.base_get(self.request.matchdict['rid'], type_name=self.parent_type_name)
        return self.base_collection_get(parent, type_name=self.type_name)

    @view(schema=CreateCardSchema(), validators=(colander_validator, validators.ADD_CARD))
    def collection_post(self):
        return self.base_collection_post(self.type_name, parent_rid=self.request.matchdict['rid'], parent_type_name=self.parent_type_name)


def includeme(config):
    config.scan(__name__)
