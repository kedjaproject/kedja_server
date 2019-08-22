
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
