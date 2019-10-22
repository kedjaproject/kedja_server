from copy import deepcopy
from random import randint

from kedja.core import get_rid_map
from kedja.core.mutator import Mutator

from kedja.utils import utcnow, init_schema


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
    maxint = 2**53-1
    return {
        'export': export,
        'version': version,
        'title': title,
        'created': created,
        'id': randint(-maxint, maxint)
    }


def import_structure(context, request, data:dict, new_rids=True):
    """ Import a nested structure where data contains:
        - type_name
        - rid
        - data (a new dict to send to the mutator)
        - contained (a list of nested objects)

        Note that the base of the import is a single object. Usually a wall.
    """
    if new_rids:
        data = deepcopy(data)
        rid_map = get_rid_map(context)
        mapping = set_new_rids(rid_map, data)
        adjust_wall_relations(data, mapping)
        new_rids = False
    content = request.registry.content
    new_resource = content(data['type_name'])
    new_resource.rid = data['rid']
    context.add(str(data['rid']), new_resource)

    schema_factory = request.get_default_schema(new_resource)
    schema = init_schema(schema_factory, resource=new_resource, registry=request.registry)
    with Mutator(new_resource, schema, registry=request.registry) as m:
        m.update(data['data'])

    for contained_data in data.get('contained', []):
        import_structure(new_resource, request, contained_data, new_rids=new_rids)
    return new_resource


def set_new_rids(rid_map, data:dict, mapping=None, relations=None):
    """ Make sure the RIDs within the import data gets set to new values.
        Adjusts data in place!
    """
    if mapping is None:
        mapping = {}
    assert rid_map is not None
    old_rid = data['rid']
    new_rid = rid_map.new_rid()
    mapping[old_rid] = new_rid
    data['rid'] = new_rid
    for x in data.get('contained', ()):
        set_new_rids(rid_map, x, mapping=mapping, relations=relations)
    return mapping


def adjust_wall_relations(data:dict, mapping):
    assert data['type_name'] == 'Wall', "Only walls contain relations"
    for rel in data['data'].get('relations', []):
        members = []
        for rid in rel['members']:
            members.append(mapping[rid])
        rel['members'] = members
