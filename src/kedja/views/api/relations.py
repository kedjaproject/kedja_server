import colander
from cornice.resource import resource
from cornice.resource import view
from cornice.validators import colander_validator
from pyramid.decorator import reify

from kedja.views import validators
from kedja.views.api.base import RIDPathSchema
from kedja.views.api.base import RelationAPISchema
from kedja.views.api.base import RelationIDPathSchema
from kedja.views.api.base import ResourceAPIBase
from kedja.views.api.base import ResourceAPISchema


class RelationSchema(colander.Schema):
    members = colander.SchemaNode(
        colander.Sequence(),
        colander.SchemaNode(
            colander.Int(),
        ),
        validator=colander.Length(2, 1000),
    )


class CreateRelationAPISchema(colander.Schema):
    path = RIDPathSchema()
    body = RelationSchema()


class UpdateRelationAPISchema(colander.Schema):
    path = RelationIDPathSchema()
    body = RelationSchema()


@resource(collection_path='/api/1/walls/{rid}/relations',
          path='/api/1/walls/{rid}/relations/{relation_id}',
          tags=['Relations'],
          validators=(colander_validator,),
          cors_origins=('*',),
          factory='kedja.root_factory')
class RelationsAPIView(ResourceAPIBase):
    #type_name = 'Relation'
    parent_type_name = 'Wall'

    @reify
    def wall(self):
        return self.base_get(self.request.matchdict['rid'], type_name=self.parent_type_name)

    def get_relation_id(self):
        return int(self.request.matchdict['relation_id'])

    def get_relation(self, relation_id):
        if self.wall:
            relation = self.wall.relations_map.get_as_json(relation_id, None)
            if relation is None:
                self.error("No relation with relation_id %r" % relation_id)
            return relation

    @view(schema=RelationAPISchema(), validators=(colander_validator, validators.VIEW_RESOURCE))
    def get(self):
        relation_id = self.get_relation_id()
        return self.get_relation(relation_id)

    @view(schema=UpdateRelationAPISchema(), validators=(colander_validator, validators.EDIT_RESOURCE))
    def put(self):
        relation_id = self.get_relation_id()
        appstruct = self.get_json_appstruct()
        if self.wall:
            self.wall.relations_map[relation_id] = appstruct['members']
            return self.wall.relations_map.get_as_json(relation_id)

    @view(schema=RelationAPISchema(),
          validators=(colander_validator, validators.EDIT_RESOURCE))  # yes, not delete here since the resource isn't touched :)
    def delete(self):
        if self.wall:
            relation_id = self.get_relation_id()
            if relation_id in self.wall.relations_map:
                del self.wall.relations_map[relation_id]
                return {'removed': relation_id}
            self.error("No relation with relation_id %r" % relation_id)

    @view(schema=ResourceAPISchema(), validators=(colander_validator, validators.VIEW_RESOURCE))
    def collection_get(self):
        if self.wall:
            return list(self.wall.relations_map.get_all_as_json())

    @view(schema=CreateRelationAPISchema(), validators=(colander_validator, validators.EDIT_RESOURCE))
    def collection_post(self):
        if self.wall:
            appstruct = self.get_json_appstruct()
            # The members part
            relation_id = self.wall.relations_map.create(appstruct['members'])
            return self.wall.relations_map.get_as_json(relation_id)


def includeme(config):
    config.scan(__name__)
