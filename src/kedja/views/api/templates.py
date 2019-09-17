
import colander
from cornice.resource import resource
from cornice.resource import view
from cornice.validators import colander_validator
from pyramid.decorator import reify

from kedja.interfaces import ITemplateFileUtil
from kedja.models.export_import import export_appstruct
from kedja.models.export_import import export_structure
from kedja.models.export_import import import_structure
from kedja.views import validators
from kedja.views.api.base import APIBase


class AddTemplateSchema(colander.Schema):
    rid = colander.SchemaNode(
        colander.Int(),
        title="The resource to create a template from",
    )
    title = colander.SchemaNode(
        colander.String(),
        title="Title of the template"
    )


class AddTemplateRequestSchema(colander.Schema):
    body = AddTemplateSchema()


@resource(path='/api/1/templates/{template_id}',
          collection_path='/api/1/templates',
          validators=(colander_validator,),
          cors_origins=('*',),
          tags=['Templates'],
          factory='kedja.root_factory')
class TemplatesAPIView(APIBase):
    """ Templates, create, manage... """

    @reify
    def tpl_util(self):
        return self.request.registry.getUtility(ITemplateFileUtil)

    @view(schema=None, validators=(colander_validator, 'validate_template_id',))
    def get(self):
        return self.tpl_util.read_appstruct(self.request.matchdict['template_id'])

    @view(schema=None, validators=(colander_validator, 'validate_template_id', validators.ADD_WALL))
    def post(self):
        template_id = self.request.matchdict['template_id']
        appstruct = self.tpl_util.read_appstruct(template_id)
        new_resource = import_structure(self.root, self.request, appstruct['export'])
        return new_resource

# Maybe later...
#    @view(schema=None)
#    def delete(self):
#        pass

    @view(schema=None)
    def collection_get(self):
        """ Return all appstructs, but remove the actual export data since this is ment for listings.
        """
        results = []
        for x in self.tpl_util.get_all_appstructs():
            del x['export']
            results.append(x)
        return results

    @view(schema=AddTemplateRequestSchema(), validators=(colander_validator, validators.ADD_TEMPLATE))
    def collection_post(self):
        """ Create a new template from an existing wall. This will require the rid of the wall to be posted.
        """
        appstruct = self.get_json_appstruct()
        rid = appstruct['rid']
        wall = self.base_get(rid, type_name='Wall')
        if wall:
            export = export_structure(wall, self.request)
            exp_appstruct = export_appstruct(export, title=appstruct['title'])
            template_id = self.tpl_util.write(exp_appstruct)
            return self.tpl_util.read_appstruct(template_id)

    def validate_template_id(self, request, **kw):
        template_id = request.matchdict['template_id']
        if template_id not in self.tpl_util.get_existing_filestems():
            self.error("No template with id %r" % template_id, type='path', status=404)


def includeme(config):
    config.scan(__name__)
    # if config.registry.settings.get('kedja.templates_dir'):
