
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
