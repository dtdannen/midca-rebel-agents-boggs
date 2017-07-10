"""
Provides all of the PyHop methods for the Dungeon domain.

All methods interact solely with the Agent as state, and never see the Dungeon as
a whole. This ensures that the planning is completely reliant on the Agent's
knowledge.
"""
from MIDCA.modules._plan import pyhop


def move_to(state, dest):
    """Move the agent to the target destination."""
    if type(dest) is list:
        dest = dest[0]

    path = state.navigate_to(dest)
    if path is None:
        return []
    return [('move', step) for step in path[1:]]


def open_lock(state, dest):
    """Open a locked object at the destination."""
    # First, find the locked object itself
    lockedObj = None
    objsOnDest = state.get_objects_at(dest)
    for obj in objsOnDest:
        if obj.locked:
            lockedObj = obj
    if not lockedObj:
        # There's no plan if there's no object to unlock
        return []

    # See if we have the key or if we can find it
    key = None
    for k in state.keys:
        # Do we own the key?
        if k.unlocks == lockedObj:
            key = k
            return [('move-adjacent', dest), ('unlock', dest)]
    if not key:
        # If not, can we find it?
        for obj in state.known_objects:
            if obj.objType == "KEY" and obj.unlocks == lockedObj:
                key = obj
                return [('fetch-key', key), ('move-adjacent', dest), ('unlock', dest)]
    if not key:
        # If we can't find a key we can't unlock the door
        return []


def fetch_key(state, key):
    """Retrieve the given key."""
    keyLoc = key.location
    return [('move-to', keyLoc), ('takekey', keyLoc)]


def move_adjacent(state, dest):
    """Move the agent to an available adjacent tile to the dest."""
    possibleAdjs = state.map.get_adjacent(dest)
    for moveDir in possibleAdjs:
        tile = possibleAdjs[moveDir]
        if tile is None:
            continue
        if state.can_reach(tile):
            return [('move-to', tile)]


def achieve_goals(state, goals):
    """Base method which allows us to understand different goals."""
    tasks = []
    for goal in goals:
        if goal.kwargs['predicate'] == 'agent-at':
            action = 'move-to'
        else:
            action = goal.kwargs['predicate']
        tasks.append((action, goal.args[0]))
    return tasks


def declare_methods():
    pyhop.declare_methods('move-to', move_to)
    pyhop.declare_methods('achieve_goals', achieve_goals)
    pyhop.declare_methods('open', open_lock)
    pyhop.declare_methods('fetch-key', fetch_key)
    pyhop.declare_methods('move-adjacent', move_adjacent)
