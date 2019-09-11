from cornice.resource import resource
from cornice.resource import view
from cornice.validators import colander_validator
from pyramid.response import Response
from slugify import slugify
from yaml import safe_dump

from kedja.models.export_import import export_appstruct
from kedja.models.export_import import export_structure
from kedja.views import validators
from kedja.views.api.base import ResourceAPIBase
from kedja.views.api.base import ResourceAPISchema


@resource(path='/api/1/export/{rid}',
          validators=(colander_validator,),
          cors_origins=('*',),
          tags=['Walls'],
          factory='kedja.root_factory')
class ExportAPIView(ResourceAPIBase):
    """ Export """
    type_name = 'Wall'

    @view(schema=ResourceAPISchema(), validators=(colander_validator, validators.VIEW_RESOURCE))
    def get(self):
        resource = self.base_get(self.request.matchdict['rid'], type_name='Wall')
        fname = slugify(resource.title, to_lower=True, max_length=50)
        headers  = {}
        if 'view' not in self.request.params:
            headers['Content-Disposition'] = "attachment; filename={}.yaml".format(fname)
        data = export_structure(resource, self.request)
        appstruct = export_appstruct(data)
        out = safe_dump(appstruct, default_flow_style=False)
        return Response(body=out, content_type = 'text/yaml', headers=headers)


def includeme(config):
    config.scan(__name__)
