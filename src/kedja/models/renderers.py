from yaml import dump
from yaml import safe_dump
#try:
#    from yaml import CDumper as Dumper
#except ImportError:
#    from yaml import Dumper


class YamlRenderer:

    def __init__(self, info):
        """ Constructor: info will be an object having the
        following attributes: name (the renderer name), package
        (the package that was 'current' at the time the
        renderer was registered), type (the renderer type
        name), registry (the current application registry) and
        settings (the deployment settings dictionary). """

    def __call__(self, value, system):
        """ Call the renderer implementation with the value
        and the system value passed in as arguments and return
        the result (a string or unicode object).  The value is
        the return value of a view.  The system value is a
        dictionary containing available system values
        (e.g., view, context, and request). """

        request = system.get('request')
        if request is not None:
            response = request.response
            ct = response.content_type
            if ct == response.default_content_type:
                response.content_type = 'application/yaml'
        return safe_dump(value)


def includeme(config):
    config.add_renderer(name='yaml', factory=YamlRenderer)
