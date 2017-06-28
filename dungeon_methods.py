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
    print(path[1:])
    return [('move', step) for step in path[1:]]


def achieve_goals(state, goals):
    """Base method which allows us to understand different goals."""
    tasks = []
    for goal in goals:
        tasks.append((goal.kwargs['predicate'], goal.args[0]))
    return tasks


def declare_methods():
    pyhop.declare_methods('move-to', move_to)
    pyhop.declare_methods('achieve_goals', achieve_goals)
