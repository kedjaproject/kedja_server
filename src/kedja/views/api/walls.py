import colander
from cornice.resource import resource
from cornice.resource import view
from cornice.validators import colander_validator
from kedja.interfaces import IWall
from kedja.permissions import VIEW

from kedja.resources.wall import WallSchema
from kedja.utils import get_valid_acls
from kedja.views.api.base import BaseResponseAPISchema
from kedja.views.api.base import ResourceAPISchema
from kedja.views.api.base import ResourceAPIBase
from kedja.views import validators
from kedja import _


class WallBodyAPISchema(BaseResponseAPISchema):
    data = WallSchema()


class ResponseSchema(colander.Schema):
    title = "Wall"
    body = WallBodyAPISchema()


class CreateWallSchema(colander.Schema):
    title = "Create a new wall"
    body = WallSchema(description="JSON payload")


class UpdateWallAPISchema(ResourceAPISchema, CreateWallSchema):
    title = "Update a specific wall"


response_schemas = {
    '200': ResponseSchema(description='Return resource'),
    '202': ResponseSchema(description='Return resource'),
    '201': ResponseSchema(description='Return resource'),
}


@resource(path='/api/1/walls/{rid}',
          collection_path='/api/1/walls',
          response_schemas=response_schemas,
          validators=(colander_validator,),
          cors_origins=('*',),
          tags=['Walls'],
          factory='kedja.root_factory')
class WallsAPIView(ResourceAPIBase):
    """ Resources """
    type_name = 'Wall'
    parent_type_name = 'Root'

    @view(schema=ResourceAPISchema(), validators=(colander_validator, validators.VIEW_RESOURCE))
    def get(self):
        return self.base_get(self.request.matchdict['rid'], type_name='Wall')

    @view(schema=UpdateWallAPISchema(), validators=(colander_validator,  validators.EDIT_RESOURCE))
    def put(self):
        return self.base_put(self.request.matchdict['rid'], type_name='Wall')

    @view(schema=ResourceAPISchema(), validators=(colander_validator, validators.DELETE_RESOURCE))
    def delete(self):
        return self.base_delete(self.request.matchdict['rid'], type_name='Wall')

    def _get_walls(self):
        for obj in self.context.values():
            if IWall.providedBy(obj) and \
                bool(obj.get_roles(self.request.authenticated_userid)) and \
                    self.request.registry.content.has_permission_type(obj, self.request, VIEW):
                yield obj

    @view(schema=None)
    def collection_get(self):
        return list(self._get_walls())

    @view(schema=CreateWallSchema(), validators=(colander_validator, validators.ADD_WALL))
    def collection_post(self):
        return self.base_collection_post(self.type_name, parent_rid=1, parent_type_name=self.parent_type_name)


@resource(path='/api/1/walls/{rid}/structure',
          validators=(colander_validator,),
          cors_origins=('*',),
          tags=['Walls'],
          factory='kedja.root_factory')
class WallStructureAPIView(ResourceAPIBase):
    type_name = 'Wall'

    @view(schema=ResourceAPISchema(), validators=(colander_validator, validators.VIEW_RESOURCE))
    def get(self):
        """
        Return a structure with all contained items. It has to be a list since we want to keep order.

        It could look something like this:
        [
            [10, [
                [101, []], [201, []], [301, []]
            ]],
            [20, [
                [102, []], [202, []], [302, []]
            ]],
            [30, [
                [103, []], [203, []], [303, []]
            ]]
        ]
        """
        wall = self.base_get(self.request.matchdict['rid'], type_name='Wall')
        if wall:
            results = []
            self.get_structure(wall, results)
            return results

    def get_structure(self, context, data):
        for v in context.values():
            contained_data = []
            data.append([v.rid, contained_data])
            self.get_structure(v, contained_data)


@resource(path='/api/1/walls/{rid}/content',
          cors_origins=('*',),
          tags=['Walls'],
          factory='kedja.root_factory')
class WallContentAPIView(ResourceAPIBase):
    type_name = 'Wall'

    @view(schema=ResourceAPISchema(), validators=(colander_validator, validators.VIEW_RESOURCE))
    def get(self):
        """ Get a structure with all of the content within this wall.
            It returns a dict where the resource ID is the key.
        """
        wall = self.base_get(self.request.matchdict['rid'], type_name='Wall')
        if wall:
            results = {}
            self.get_content(wall, results)
            # Load relations etc too
            return {'resources': results}

    def get_content(self, context, data):
        for v in context.values():
            data[v.rid] = v
            self.get_content(v, data)


class WallACLSchema(colander.Schema):
    acl_name = colander.SchemaNode(
        colander.String(),
        title=_("ACL policy to use"),
    )


class WallACLResourceSchema(ResourceAPISchema):
    title = "Change the used ACL"
    body = WallACLSchema()


@resource(path='/api/1/walls/{rid}/acl',
          cors_origins=('*',),
          tags=['Walls'],
          factory='kedja.root_factory')
class WallACLAPIView(ResourceAPIBase):
    type_name = 'Wall'

    @view(schema=ResourceAPISchema(), validators=(colander_validator, validators.VIEW_RESOURCE))
    def get(self):
        """ Get available ACLs and information about them
        """
        wall = self.base_get(self.request.matchdict['rid'], type_name='Wall')
        if wall:
            results = []
            for acl in get_valid_acls(wall, registry=self.request.registry):
                results.append(acl.details_for(wall))
            return results

    @view(schema=WallACLResourceSchema(), validators=(colander_validator, validators.EDIT_RESOURCE))
    def put(self):
        """ Set ACL policy to use
        """
        wall = self.base_get(self.request.matchdict['rid'], type_name='Wall')
        if wall:
            valid_acl_names = [acl.name for acl in get_valid_acls(wall, registry=self.request.registry)]
            appstruct = self.get_json_appstruct()
            acl_name = appstruct.get('acl_name', '')
            if acl_name not in valid_acl_names:
                self.error("%r is not a valid acl_name", type='body', status=400)
                return
            wall.acl_name = acl_name
            return {'acl_name': acl_name}


def includeme(config):
    config.scan(__name__)
