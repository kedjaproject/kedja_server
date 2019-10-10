from random import randrange

from BTrees import family64
from BTrees.OOBTree import OOSet
from arche.interfaces import IResourceWillBeRemoved
from persistent import Persistent
from pyramid.traversal import find_interface

from kedja.interfaces import ICard
from kedja.interfaces import ICollection
from kedja.interfaces import IWall


def relation_dict(relation_id:int, members:list=()):
    return {'relation_id': relation_id, 'members': list(members)}


class RelationMap(Persistent):
    family = family64

    def __init__(self):
        self.rid_to_relations = self.family.IO.BTree()
        self.relation_to_rids = self.family.IO.BTree()

    def __getitem__(self, relation_id:int):
        return self.relation_to_rids[relation_id]

    def __delitem__(self, relation_id:int):
        for x in self.get(relation_id, ()):
            linked = self.rid_to_relations.get(x, ())
            if relation_id in linked:
                linked.remove(relation_id)
                if not linked:
                    del self.rid_to_relations[x]
        del self.relation_to_rids[relation_id]

    def __setitem__(self, relation_id, rids):
        assert isinstance(relation_id, int)
        self.can_create_relation(rids)
        if relation_id in self:
            del self[relation_id]
        for x in rids:
            assert isinstance(x, int)
            if x not in self.rid_to_relations:
                self.rid_to_relations[x] = OOSet()
            self.rid_to_relations[x].add(relation_id)
        self.relation_to_rids[relation_id] = tuple(rids)

    def __contains__(self, relation_id:int):
        return relation_id in self.relation_to_rids

    def clear(self):
        """ Clear all relations. """
        self.rid_to_relations.clear()
        self.relation_to_rids.clear()

    def create(self, rids):
        relation_id = self.new_relation_id()
        self[relation_id] = rids
        return relation_id

    def can_create_relation(self, rids):
        """ Make sure a relation don't exist between these rids already"""
        if len(rids) < 2:
            raise ValueError("It takes at least 2 to tango!")
        rids = tuple(rids)
        existing = self.find_relations(rids[0], *rids[1:])
        if existing:
            cmp_set = set(rids)
            for rel_id in existing:
                if self.get(rel_id) == cmp_set:
                    raise ValueError("Already has relations: %s" % ", ".join(existing))

    def get(self, relation_id, default=None):
        return self.relation_to_rids.get(relation_id, default)

    def get_as_json(self, relation_id, default=None):
        members = self.get(relation_id, None)
        if members is not None:
            return relation_dict(relation_id, members)
        return default

    def get_all_as_json(self):
        for k in self.keys():
            yield self.get_as_json(k)

    def set_all_from_json(self, value:list):
        """ Set all relations at once, probably from an import.
            Will clear existing relations!

            value must be a list with dicts that have the same structure as returned via 'get_as_json'.
        """
        self.clear()
        for item in value:
            relation_id = item['relation_id']
            members = item['members']
            self[relation_id] = members

    def new_relation_id(self):
        """ Get an unused ID. It's not reserved in any way, so make sure to use it within the current transaction.
            In the unlikely case that the same ID would be used, a transaction error will occur.
        """
        relation_id = None
        js_maxint = 2**53-1
        while not relation_id:  # We don't like 0 either
            relation_id = randrange(-js_maxint, js_maxint)
            if relation_id in self.relation_to_rids: # pragma: no cover
                relation_id = None
        return relation_id

    def find_relations(self, rid:int, *rids):
        """ Get relations that has one or more rids in them. All RIDs specified will be required for a match.
        """
        first = set(self.rid_to_relations.get(rid, ()))
        if rids:
            return first.intersection(*[self.rid_to_relations.get(x, set()) for x in rids])
        return first

    def find_relevant_relation_ids(self, rids):
        """ Return all relation_ids that have anything to do with any of the specified rids.
        """
        if isinstance(rids, int):
            rids = [rids]
        found = set()
        for x in rids:
            found.update(self.find_relations(x))
        return found

    def keys(self):
        return self.relation_to_rids.keys()

    def __len__(self):
        return len(self.relation_to_rids)

    def __iter__(self):
        return self.relation_to_rids.iteritems()


def remove_contained_cards_relations(event):
    """ If a collection is removed, cleanup all relevant relations to/from cards that will be removed.
    """
    resource = event.context
    wall = find_interface(resource, IWall)
    for rid in event.contained_rids:
        for relation_id in wall.relations_map.find_relations(rid):
            del wall.relations_map[relation_id]


def remove_card_relations(event):
    """ In case a card is removed. cleanup all relations to/from that card.
    """
    resource = event.context
    wall = find_interface(resource, IWall)
    for relation_id in wall.relations_map.find_relations(resource.rid):
        del wall.relations_map[relation_id]


def includeme(config):
    config.add_subscriber(remove_contained_cards_relations, IResourceWillBeRemoved, context=ICollection)
    config.add_subscriber(remove_card_relations, IResourceWillBeRemoved, context=ICard)
