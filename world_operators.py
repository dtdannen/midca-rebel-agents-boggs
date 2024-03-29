"""
Provides all of the PyHop operators for the World domain.

All operators interact solely with the Agent as state, and never see the World as
a whole. This ensures that the planning is completely reliant on the Agent's
knowledge.
"""
from midca.modules._plan import pyhop


# Movement operator
def move(state, moveDir):
    """
    Move the agent one tile in a cardinal direction, if possible.

    `state` is the Agent object and `dir` is which direction to move in ('n', 'e',
    's', 'w').
    """
    try:
        state.move(moveDir)
    except ValueError:
        print("{} is not a valid movement direction".format(moveDir))
    return state


def takekey(state, keyLoc):
    try:
        state.take_key(keyLoc)
    except ValueError:
        print("{} is not a valid location in the world".format(keyLoc))
    return state


def unlock(state, target):
    try:
        state.unlock(target)
    except ValueError:
        print("{} is not a valid location in the world".format(target))
    return state


def bomb(state, range):
    """
    Have Agent detonate its bomb at its location.

    Arguments:
        ``state``, *Agent*:
            The current state for PyHop's planning, which will be an ``Agent``.

        ``range``, *int*:
            The range of the bomb. DUmmy variable for now.
    """
    state.bomb()
    return state


def arm(state, turns):
    """Arm agent so that it may detonate bomb next action."""
    state.arm()
    return state


def declare_operators():
    pyhop.declare_operators(move, takekey, unlock, bomb, arm)
