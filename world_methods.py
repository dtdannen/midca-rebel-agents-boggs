"""
Provides all of the PyHop methods for the World domain.

All methods interact solely with the Agent as state, and never see the World as
a whole. This ensures that the planning is completely reliant on the Agent's
knowledge.
"""
from midca.modules._plan import pyhop

def move_to(state, dest):
    """Move the agent to the target destination."""
    assert dest is not None, 'Why is dest none in Move_to func'
    if type(dest) is list:
        dest = dest[0]
    path = state.navigate_to(dest)
    if path is None:
        return []
    else:
        return [ ('move', step) for step in path[1:] ]


def open_lock(state, dest):
    """Open a locked object at the destination."""
    lockedObj = None
    objsOnDest = state.get_objects_at(dest)
    for obj in objsOnDest:
        if obj.locked:
            lockedObj = obj

    if not lockedObj:
        return []
    else:
        key = None
        for k in state.keys:
            if k.unlocks == lockedObj:
                key = k
                return [
                 (
                  'move-adjacent', dest), ('unlock', dest)]

        if not key:
            for obj in state.known_objects:
                if obj.objType == 'KEY' and obj.unlocks == lockedObj:
                    key = obj
                    return [
                     (
                      'fetch-key', key), ('move-adjacent', dest), ('unlock', dest)]

        if not key:
            return []
        return


def fetch_key(state, key):
    """Retrieve the given key."""
    keyLoc = key.location
    return [
     (
      'move-to', keyLoc), ('takekey', keyLoc)]


def move_adjacent(state, dest):
    """Move the agent to an available adjacent tile to the dest."""
    adjTile = state.map.get_closest_adjacent(dest, state.at)
    return [
     (
      'move-to', adjTile)]


def achieve_goals(state, goals):
    """Base method which allows us to understand different goals."""
    tasks = []
    for goal in goals:
        if goal.kwargs['predicate'] == 'agent-at':
            action = 'move-to'
            tasks.append((action, goal.args[0]))
        elif goal.kwargs['predicate'] == 'killed':
            targetID = goal.args[0]
            targetLoc = state.map.get_object(targetID).location
            tasks.append(('move-adjacent', targetLoc))
            tasks.append(('arm', 0))
            tasks.append(('arm', 0))
            tasks.append(('bomb', 2))
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
