from copy import deepcopy

from arche.objectmap import get_rid_map

from kedja.utils import utcnow


EXPORT_VERSION = 1


def export_structure(context, request, contained=None):
    """ Export schema data from context and everything contained within it.
        Note that things that aren't saved in the schema won't be stored here!
    """
    is_export_root = contained is None
    if contained is None:
        contained = []
    data = context.__json__(request)
    if not is_export_root:
        contained.append(data)
    if len(context):
        data['contained'] = contained_data = []
        for x in context.values():
            export_structure(x, request, contained=contained_data)
    return data


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
        title = export['data']['title']
    return {
        'export': export,
        'version': version,
        'title': title,
        'created': created,
        'id': export['rid']
    }


def import_structure(context, request, data:dict, new_rids=True):
    """ Import a nested structure where data contains:
        - type_name
        - rid
        - data (a new dict to send to the mutator)
        - contained (a list of nested objects)
    """
    if new_rids:
        data = deepcopy(data)
        rid_map = get_rid_map(context)
        set_new_rids(rid_map, data)
    content = request.registry.content
    new_resource = content(data['type_name'])
    new_resource.rid = data['rid']
    context.add(str(data['rid']), new_resource)
    with request.get_mutator(new_resource) as mutator:
        mutator.update(data['data'])
    for contained_data in data.get('contained', []):
        import_structure(new_resource, request, contained_data, new_rids=new_rids)


def set_new_rids(rid_map, data:dict, mapping=None, relations=None):
    """ Make sure the RIDs within the import data gets set to new values.
        Adjusts data in place!
    """
    is_import_root = mapping is None
    if mapping is None:
        mapping = {}
    if relations is None:
        relations = []
    assert rid_map is not None

    old_rid = data['rid']
    new_rid = rid_map.new_rid()
    mapping[old_rid] = new_rid
    data['rid'] = new_rid
    if data['type_name'] == 'Wall':
        relations.extend(data['data'].get('relations', []))

    for x in data.get('contained', ()):
        set_new_rids(rid_map, x, mapping=mapping, relations=relations)
    if is_import_root:
        # Walk through relations and replace rids
        # Looks something like this:
        # {'relation_id': <int>, 'members': [<int>, <int>]}
        # see the wall schema for more info
        # We only need to repoint the members to the correct rids
        for relation in relations:
            members = []
            for rid in relation['members']:
                members.append(mapping[rid])
            # Should we remove relations with faulty rids? Currently it will cause a crash instead
            relation['members'] = members
