from kedja.utils import utcnow


EXPORT_VERSION = 1


def export_structure(context, request, contained=None):
    """ Export schema data from context and everything contained within it.
        Note that things that aren't saved in the schema won't be stored here!
    """
    if contained is None:
        contained = []
    data = context.__json__(request)
    contained.append(data)
    if len(context):
        data['contained'] = contained_data = []
        for x in context.values():
            export_structure(x, request, contained=contained_data)
    return contained


def export_appstruct(export, version=EXPORT_VERSION, title=None, created=utcnow()):
    """ A helper to create a dict that conforms with export structure.

        Important keys

        - version (export version)
        - export (the actual data from export structure)
        - title
        - created
    """
    if title is None:
        # The first item should be the walls title
        title = export[0]['data']['title']
    return {
        'export': export,
        'version': version,
        'title': title,
        'created': created,
        'id': export[0]['rid']
    }


def import_structure(context, request, data:dict):
    """ Import a nested structure where data contains:
        - type_name
        - rid
        - data (a new dict to send to the mutator)
        - contained (a list of nested objects)
    """
    content = request.registry.content
    new_resource = content(data['type_name'])
    new_resource.rid = data['rid']
    context.add(str(data['rid']), new_resource)
    with request.get_mutator(new_resource) as mutator:
        mutator.update(data['data'])
    contained_data = data.get('contained', {})
    if contained_data:
        import_structure(new_resource, request, contained_data)
