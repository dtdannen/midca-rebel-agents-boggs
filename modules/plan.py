"""Contains the plan validator for the World environemnt."""

import copy
import math
from MIDCA import base, goals


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


class OperatorPlanGoals(base.BaseModule):
    """
    Generate goals for various inactive agents and preliminarily assign them.

    This module allows the automatic operator to generate a goal for each inactive
    agent (i.e. an agent without a current goal). Currently it just tells each
    agent to kill the living enemy closest to it. Once each goal is generated, it
    stores the goal-agent pairs in MIDCA's memory.
    """

    def init(self, world, mem):
        """Give the module crucial MIDCA information about memory and state."""
        self.mem = mem
        self.client = world

    def get_closest_enemy(self, agt, enemies):
        """
        Return the enemy closest to the agent given.

        Distance is calculated using the Pythagorean theorem, meaning it does not
        factor in the actual number of tiles which need to be traversed.

        Arguments:

        ``agt``, *Agent*:
            The ``Agent`` object which will be the subject of the goal.

        ``enemeis``, *sequence*:
            A list of ``Npc`` objects which are potential targets.

        ``returns``, *Npc*:
            The closest enemy to the given agent, as the crow flies.
        """
        invalidTargets = self.mem.get("INVALID_TARGETS")
        if invalidTargets is None:
            invalidTargets = []
        agentObj = self.client.operator().map.get_user(agt)
        closestVal = float("inf")
        closest = None
        for enemy in enemies:
            if enemy.id in invalidTargets:
                continue
            dist = math.sqrt((agentObj.at[0] - enemy.location[0])**2 + (agentObj.at[1] - enemy.location[1])**2)
            if dist < closestVal:
                closestVal = dist
                closest = enemy

        return closest

    def run(self, cycle, verbose=2):
        """
        Create a goal for each inactive agent and remember the pairings.

        This function looks at each inactive agent, calculates the closest living
        enemy to that agent, and assigns the goal of killing that enemy to the
        agent. It does **not** actually order the agents to complete the goals,
        though.
        """
        availAgents = self.mem.get("AVAIL_AGENTS")
        enemies = self.mem.get("ENEMIES")
        optr = self.client.operator()
        while optr is None:
            optr = self.client.operator()

        goalPairs = []
        for agt in availAgents:
            target = self.get_closest_enemy(agt, enemies)
            if target is None:
                continue
            goal = goals.Goal(target.id, predicate='killed', user=optr.id)
            goalPairs.append((agt, goal))

        self.mem.set("PLANNED_GOALS", goalPairs)
