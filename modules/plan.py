"""Contains the plan validator for the World environemnt."""

import copy


def worldPlanValidator(state, plan):
    """
    Ensure that the given plan is still valid in the given state.

    Runs through the plan on a copy of the given state, and if any action can't
    be taken it returns false.
    """
    testState = copy.deepcopy(state)
    testPlan = copy.copy(plan)
    actionSuccess = True
    action = True
    while action and actionSuccess:
        action = testPlan.get_next_step()
        if action:
            actionSuccess = testState.apply_action(action)
            testPlan.advance()
    return actionSuccess


def worldGoalComparator(goal1, goal2):
    """
    Compares two goals and returns either -1, 0, or 1.

    If goal1 should be achieved before goal2, this returns -1, and if the
    reverse is true, it returns 1. If neither needs to preceed the other, then
    0 is returned. This function checks whether one goal has the other as its
    parent goal. In the World domain, if a goal engenders another goal, the
    original goal is the parent of the new goal.
    """
    if 'parent' in goal1.kwargs.keys() and goal1.kwargs['parent'] == goal2:
        return -1
    if 'parent' in goal2.kwargs.keys() and goal2.kwargs['parent'] == goal1:
        return 1
    return 0
