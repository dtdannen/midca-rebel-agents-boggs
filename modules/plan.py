"""Contains the plan validator for the World environemnt."""
import copy
import math
import logging
import traceback
from MIDCA import base, goals, plans
from MIDCA.modules import _plan

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

    def __init__(self, logger=logging.getLogger('dummy')):
        """Instantiate a ``OperatorPlanGoals`` module; with a logger if desired."""
        super(OperatorPlanGoals, self).__init__()
        self.logger = logger

    def init(self, world, mem):
        """Give the module crucial MIDCA information about memory and state."""
        self.mem = mem
        self.client = world

    def check_enemy_valid(self, agt, enemy):
        """
        Ensure that the given enemy is a valid target for the agent.

        The enemy is not valid if there exists an invalid goal which has the agent
        targetting the enemy. ``invalidGoals`` will be a list of pairs, where the
        first element is an ```Agent`` and the second is a ``Goal``.

        Arguments:
            ``agt``, *Agent*:
                The ``Agent`` object which will be the subject of the goal.

            ``enemy``, *Npc*:
                The enemy which the agent will be targetting.

            ``return``, *bool*:
                Whether the enemy is valid or not.
        """
        self.logger.info('Checking if {} is valid target for {}'.format(enemy, agt))
        valid = True
        invalidGoals = self.mem.get('INVALID_GOALS')
        self.logger.debug('Got invalid goals {}'.format(invalidGoals))
        if not invalidGoals:
            valid = True
        else:
            for goalPair in invalidGoals:
                if goalPair[0] == agt.id and goalPair[1][0] == enemy.id:
                    valid = False

        self.logger.info('{} is a valid target: {}'.format(enemy, valid))
        return valid

    def get_closest_enemy(self, agt, enemies):
        """
        Return the enemy closest to the agent given.

        Distance is calculated using the Pythagorean theorem, meaning it does not
        factor in the actual number of tiles which need to be traversed.

        Arguments:

        ``agt``, *str*:
            The ID string of the ``Agent`` which will receive the goal.

        ``enemeis``, *sequence*:
            A list of ``Npc`` objects which are potential targets.

        ``returns``, *Npc*:
            The closest enemy to the given agent, as the crow flies.
        """
        self.logger.info('Getting closest enemy to {}'.format(agt))
        agentObj = self.client.operator().map.get_user(agt)
        closestVal = float('inf')
        closest = None
        for enemy in enemies:
            if not self.check_enemy_valid(agentObj, enemy):
                continue
            dist = math.sqrt((agentObj.at[0] - enemy.location[0]) ** 2 + (agentObj.at[1] - enemy.location[1]) ** 2)
            if dist < closestVal:
                closestVal = dist
                closest = enemy

        self.logger.info('Closest enemy is {}'.format(closest))
        return closest

    def run(self, cycle, verbose=2):
        """
        Create a goal for each inactive agent and remember the pairings.

        This function looks at each inactive agent, calculates the closest living
        enemy to that agent, and assigns the goal of killing that enemy to the
        agent. It does **not** actually order the agents to complete the goals,
        though.
        """
        self.logger.info('Retrieving available agents, living enemies, and the op')
        availAgents = self.mem.get('AVAIL_AGENTS')
        enemies = self.mem.get('ENEMIES')
        optr = self.client.operator()
        while optr is None:
            optr = self.client.operator()

        goalPairs = []
        for agt in availAgents:
            self.logger.info('Finding goal for {}'.format(agt))
            target = self.get_closest_enemy(agt, enemies)
            if target is None:
                continue
            goal = goals.Goal(target.id, predicate='killed', user=optr.id)
            self.logger.info('Found goal {}'.format(goal))
            goalPairs.append((agt, goal))

        self.mem.set('PLANNED_GOALS', goalPairs)
        self.logger.info('Saved planned goals')
        return


class GenericPyhopPlanner(base.BaseModule):
    """
    Whereas the PyHopPlanner class below is optimized for use with MIDCA's
    built-in world simulator, this planner is more generalized. It assumes that
    the world state stored in MIDCA's memory is also the world state that will
    be expected by the planning methods and operators. Also, it expects to
    receive 'declare_methods' and 'declare_operators' methods as arguments.
    These should initialize pyhop for the desired planning domain. The
    plan_validator arg should be a method which takes a world state and a plan
    as args and returns whether the plan should be used. This will only be
    called on old plans that are retrieved.
    """

    def __init__(self, declare_methods, declare_operators, plan_validator=None, verbose=2):
        declare_methods()
        declare_operators()
        self.working = True
        self.verbose = verbose
        self.validate_plan = plan_validator

    def get_old_plan(self, state, goals, verbose):
        verbose = self.verbose
        try:
            plan = self.mem.get(self.mem.GOAL_GRAPH).getMatchingPlan(goals)
            if not plan:
                return
            try:
                if self.validate_plan:
                    valid = self.validate_plan(state, plan)
                    if valid:
                        if verbose >= 2:
                            print 'Old plan found that tests as valid:', plan
                    else:
                        if verbose >= 2:
                            print 'Old plan found that tests as invalid:', plan, '. removing from stored plans.'
                        self.mem.get(self.mem.GOAL_GRAPH).removePlan(plan)
                else:
                    if verbose >= 2:
                        print 'no validity check specified. assumingeold plan is valid.'
                    valid = True
            except Exception as e:
                if verbose >= 2:
                    print 'Error validating plan:', plan, e
                raise e

        except AttributeError:
            print 'Error checking for old plans'
            plan = None
            valid = False

        if valid:
            return plan
        else:
            return

    def get_new_plan(self, state, goals, verbose):
        """
            Calls the pyhop planner to generate a new plan.
        """
        verbose = self.verbose
        if verbose >= 2:
            print 'Planning...'
        plan = _plan.pyhop.pyhop(state, [('achieve_goals', goals)], verbose=verbose)
        return plan

    def run(self, cycle, verbose=2):
        verbose = self.verbose
        state = self.mem.get(self.mem.STATE)
        if not state:
            states = self.mem.get(self.mem.STATES)
            if states:
                state = states[-1]
            else:
                if verbose >= 1:
                    print 'No world state loaded. Skipping planning.'
                return
        goals = self.mem.get(self.mem.CURRENT_GOALS)
        if not goals:
            if verbose >= 2:
                print 'No goals received by planner. Skipping planning.'
            return
        else:
            plan = self.get_old_plan(state, goals, verbose)
            if verbose >= 2:
                if plan:
                    print 'Will not replan'
                else:
                    print 'Planning from scratch'
            if not plan:
                plan = self.get_new_plan(state, goals, verbose)
                if not plan and plan != []:
                    return
                plan = plans.Plan([plans.Action(action[0], *action[1:]) for action in plan
                                   ], goals)
                if verbose >= 1:
                    print 'Planning complete.'
            if verbose >= 2:
                print 'Plan: ', plan
            if plan is not None:
                self.mem.get(self.mem.GOAL_GRAPH).addPlan(plan)
            return
