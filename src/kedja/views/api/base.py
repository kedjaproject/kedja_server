from json import JSONDecodeError
from logging import getLogger

import colander
from pyramid.decorator import reify
from pyramid.traversal import find_root

logger = getLogger(__name__)


class ResourceAPIBase(object):

    def __init__(self, request, context=None):
        self.request = request
        self.context = context
        self._lookup_cache = {}
        request.content_type = 'application/json'  # To make Cornice happy, in case someone forgot that header

    @reify
    def root(self):
        return find_root(self.context)

    def get_resource(self, rid):
        if isinstance(rid, str):
            # This should be catched by other means, for instance in the schema
            rid = int(rid)
        resource = self._lookup_cache.setdefault(rid, self.root.rid_map.get_resource(rid))
        if resource is None:
            self.error("No resource with RID %s" % rid, type='path', status=404)
            return
        return resource

    def error(self, msg="Doesn't exist", type='path', status=404, request=None):
        if request is None:
            request = self.request
        request.errors.add(type, msg)
        request.errors.status = status

    # Use this?
    # def validate_rid(self, request, **kw):
    #     """ RID must be numeric and exist. """
    #     rid = self.request.matchdict['rid']
    #     if self.get_resource(rid) is None:
    #         return self.error(request, "No resource with rid %r exists" % rid)

    def get_json_appstruct(self):
        if not self.request.body:
            self.error("no payload received", type='body', status=400)
            return
        try:
            return self.request.json_body
        except JSONDecodeError as exc:
            logger.debug("JSON decode error", exc_info=exc)
            self.error("JSON decode error: %s" % exc, type='body', status=400)
            return

    def check_type_name(self, resource, type_name=None):
        type_ok = type_name is not None and type_name == getattr(resource, 'type_name', object())
        if type_ok:
            return True
        self.error("The fetched resource is not a %r" % type_name, type='path', status=404)
        return False

    def base_get(self, rid, type_name=None):
        """ Get specific resource. Validate type_name if specified. """
        resource = self.get_resource(rid)
        if self.check_type_name(resource, type_name=type_name):
            return resource

    def contained_get(self, parent, rid, type_name=None):
        """ Fetch a resource contained within parent. It wil simply check that the parent matches.
            The name and the rid might not be equivalent."""
        resource = self.base_get(rid, type_name=type_name)
        if resource:
            if resource.__parent__ == parent:
                # All good
                return resource
            # Fail, wrong parent
            self.error("%r is not contained within %r" % (resource, parent), type='path', status=404)
            return

    def base_put(self, rid, type_name=None):
        """ Update a resource """
        resource = self.get_resource(rid)
        self.check_type_name(resource, type_name=type_name)
        appstruct = self.get_json_appstruct()
        # Note: The mutator API will probably change!
        with self.request.get_mutator(resource) as mutator:
            changed = mutator.update(appstruct)
        # Log changed?
        return resource

    def base_delete(self, rid, type_name=None):
        """ Delete a resource """
        resource = self.get_resource(rid)
        if self.check_type_name(resource, type_name=type_name):
            parent = resource.__parent__
            parent.remove(resource.__name__)
            return {'removed': int(rid)}

    def base_collection_get(self, parent, type_name=None):
        if parent is None:
            return
        results = []
        for x in parent.values():
            if type_name is None:
                results.append(x)
            elif getattr(x, 'type_name', object()) == type_name:
                results.append(x)
        return results

    def base_collection_post(self, type_name, parent_rid=None, parent_type_name=None):
        new_res = self.request.registry.content(type_name)
        new_res.rid = self.root.rid_map.new_rid()
        #FIXME Check add permission within this parent
        parent = self.base_get(parent_rid, type_name=parent_type_name)
        # Should be the root
        parent.add(str(new_res.rid), new_res)
        appstruct = self.get_json_appstruct()
        # Note: The mutator API will probably change!
        with self.request.get_mutator(new_res) as mutator:
            changed = mutator.update(appstruct)
        # Log changed?
        return new_res


class RIDPathSchema(colander.Schema):
    rid = colander.SchemaNode(
        colander.Int(),
    )


class SubRIDPathSchema(RIDPathSchema):
    subrid = colander.SchemaNode(
        colander.Int(),
    )


class RelationIDPathSchema(RIDPathSchema):
    relation_id = colander.SchemaNode(
        colander.Int(),
    )


class ResourceAPISchema(colander.Schema):
    path = RIDPathSchema()


class SubResourceAPISchema(colander.Schema):
    path = SubRIDPathSchema()


class RelationAPISchema(colander.Schema):
    path = RelationIDPathSchema()


class BaseResponseAPISchema(colander.Schema):
    rid = colander.SchemaNode(
        colander.Int(),
    )
    type_name = colander.SchemaNode(
        colander.String(),
    )


class ChangedResponseAPISchema(colander.Schema):
    changed = colander.SchemaNode(
        colander.Sequence(),
        colander.SchemaNode(
            colander.String()
        )
    )
