from cornice.resource import resource, view
from cornice.validators import colander_validator
from pyramid.renderers import render
from slugify import slugify

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
        fname = slugify(resource.title, to_lower=True, max_length=50)
        self.request.response.headers['Content-Disposition'] = "attachment; filename={}.yaml".format(fname)
        return render('yaml', export_structure(resource, self.request), request=self.request)


def includeme(config):
    config.scan(__name__)
