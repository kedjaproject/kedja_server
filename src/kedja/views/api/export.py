from cornice.resource import resource, view
from cornice.validators import colander_validator

from kedja.models.exporter import export_structure
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

    @view(schema=ResourceAPISchema(), validators=(colander_validator, 'view_resource_validator'))
    def get(self):
        resource = self.base_get(self.request.matchdict['rid'], type_name='Wall')
        self.request.response.headers['Content-Disposition'] = "attachment; filename={}.json".format(resource.rid)
        return export_structure(resource, self.request)


def includeme(config):
    config.scan(__name__)
