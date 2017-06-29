"""Contains the plan validator for the Dungeon environemnt."""

import copy


def dungeonPlanValidator(state, plan):
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
