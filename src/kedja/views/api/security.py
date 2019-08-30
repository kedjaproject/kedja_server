import colander
from cornice.resource import resource
from cornice.resource import view
from cornice.validators import colander_validator
from pyramid.location import lineage

from kedja.interfaces import ISecurityAware
from kedja.views.api.base import APIBase
from kedja.views.api.base import ResourceAPISchema


class PermissionsBodyResponseSchema(colander.Schema):
    allowed = colander.SchemaNode(
        colander.Sequence(),
        colander.SchemaNode(
            colander.String(),
            title="Permission",
        ),
        title="Explicitly allowed",
        missing=[],
    )
    denied = colander.SchemaNode(
        colander.Sequence(),
        colander.SchemaNode(
            colander.String(),
            title="Permission",
        ),
        title="Explicitly denied",
        missing=[],
    )
    all_other_allowed = colander.SchemaNode(
        colander.Bool(),
        title="Are all other permissions implicitly allowed?",
        missing=False,
    )


class PermissionsOKResponseSchema(colander.Schema):
    title = "Valid response"
    body = PermissionsBodyResponseSchema()


permissions_response_schemas = {
    '200': PermissionsOKResponseSchema(description='Response params for simplified permissions lists'),
}


@resource(path='/api/1/permissions/{rid}',
          validators=(colander_validator,),
          cors_origins=('*',),
          tags=['Security'],
          factory='kedja.root_factory',
          response_schemas=permissions_response_schemas)
class PermissionsAPIView(APIBase):
    """ Return a dict of permissions, simplified. """

    @view(schema=ResourceAPISchema(),)
    def get(self):
        requested_resource = self.base_get(self.request.matchdict['rid'])
        if requested_resource is not None:
            for res in lineage(requested_resource):
                if ISecurityAware.providedBy(res):
                    return res.get_simplified_permissions(self.request)


def includeme(config):
    config.scan(__name__)
