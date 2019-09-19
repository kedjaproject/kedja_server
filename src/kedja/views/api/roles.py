import colander
from cornice.resource import resource
from cornice.resource import view
from cornice.validators import colander_validator

from kedja.interfaces import ISecurityAware
from kedja.views import validators
from kedja.views.api.base import APIBase
from kedja.views.api.base import RIDPathSchema


class RIDAndUserIDSchema(RIDPathSchema):
    userid = colander.SchemaNode(
        colander.Int(),
    )


class GetRolesAPISchema(colander.Schema):
    path = RIDAndUserIDSchema()


class AssignRolesSchema(colander.Schema):
    add_roles = colander.SchemaNode(
        colander.Sequence(),
        colander.SchemaNode(
            colander.String(),
            title="Role",
        ),
        title="Roles to add",
        missing=[],
    )
    remove_roles = colander.SchemaNode(
        colander.Sequence(),
        colander.SchemaNode(
            colander.String(),
            title="Role",
        ),
        title="Roles to remove",
        missing=[],
    )


class PutRolesAPISchema(GetRolesAPISchema):
    body = AssignRolesSchema()


@resource(path='/api/1/roles/{rid}/userid/{userid}',
          validators=(colander_validator,),
          cors_origins=('*',),
          tags=['Security'],
          factory='kedja.root_factory')
class RolesAPIView(APIBase):

    # FIXME: Permission to check this?

    @view(schema=GetRolesAPISchema(),
          validators=(colander_validator, 'validate_userid', 'rid_security_aware', validators.MANAGE_ROLES))
    def get(self):
        resource = self.base_get(self.request.matchdict['rid'])
        if ISecurityAware.providedBy(resource):
            return list(resource.get_roles(self.request.matchdict['userid']))

    @view(schema=PutRolesAPISchema(),
          validators=(colander_validator, 'validate_userid', 'rid_security_aware', validators.MANAGE_ROLES))
    def put(self):
        resource = self.base_get(self.request.matchdict['rid'])
        if ISecurityAware.providedBy(resource):
            appstruct = self.get_json_appstruct()
            if not appstruct:
                # Appstruct is None here
                return
            # FIXME: validation through schema
            # schema = PutRolesAPISchema().bind(context=resource, request=self.request)
            if 'add_roles' not in appstruct and 'remove_roles' not in appstruct:
                self.error('No roles to add or remove', status=400)
                return
            userid = self.request.matchdict['userid']
            add_roles = appstruct.get('add_roles', [])
            if add_roles:
                resource.add_user_roles(userid, *add_roles)
            remove_roles = appstruct.get('remove_roles', [])
            if remove_roles:
                resource.remove_user_roles(userid, *remove_roles)
            return list(resource.get_roles(userid))

    def validate_userid(self, request, **kw):
        self.base_get(self.request.matchdict['userid'], type_name='User')

    def rid_security_aware(self, request, **kw):
        resource = self.base_get(self.request.matchdict['rid'])
        if not ISecurityAware.providedBy(resource):
            self.error("The resource %r can't have roles set to it. It doesn't implement ISecurityAware.",
                       status=400)


def includeme(config):
    config.scan(__name__)
