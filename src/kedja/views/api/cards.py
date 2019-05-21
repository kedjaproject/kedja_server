from cornice.resource import resource
from cornice.resource import view
from cornice.validators import colander_validator

from kedja.views.api.base import ResourceAPIBase
from kedja.views.api.base import SubResourceAPISchema
from kedja.views.api.base import ResourceAPISchema


@resource(collection_path='/api/1/collections/{rid}/cards',
          path='/api/1/collections/{rid}/cards/{subrid}',  # This isn't used, but cornice needs this path?
          tags=['Cards'],
          schema=SubResourceAPISchema(),
          validators=(colander_validator,),
          cors_origins=('*',),
          factory='kedja.root_factory')
class ContainedCardsAPI(ResourceAPIBase):
    type_name = 'Card'
    parent_type_name = 'Collection'

    def get(self):
        return self.base_get(self.request.matchdict['subrid'], type_name=self.type_name)

    # FIXME schemas?
    def put(self):
        return self.base_put(self.request.matchdict['subrid'], type_name=self.type_name)

    def delete(self):
        return self.base_delete(self.request.matchdict['subrid'], type_name=self.type_name)

    @view(schema=ResourceAPISchema())
    def collection_get(self):
        parent = self.base_get(self.request.matchdict['rid'], type_name=self.parent_type_name)
        return self.base_collection_get(parent, type_name=self.type_name)

    @view(schema=ResourceAPISchema())
    def collection_post(self):
        return self.base_collection_post(self.type_name, parent_rid=self.request.matchdict['rid'], parent_type_name=self.parent_type_name)

    def options(self):
        # FIXME:
        return {}


def includeme(config):
    config.scan(__name__)