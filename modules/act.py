import copy
import logging

from midca import base


class SimpleAct(base.BaseModule, object):
    """Allows MIDCA to execute actions in a plan by affecting the World."""

    def __init__(self, logger=logging.getLogger("dummy")):
        """Instantiate a ``SimpleAct`` module; with a logger if desired."""
        super(SimpleAct, self).__init__()
        self.logger = logger

    def init(self, world, mem):
        """Give module critical MIDCA data."""
        self.mem = mem
        self.world = world

    def get_best_plan(self, world, goals, verbose):
        """
        Find best plan in MIDCA's memory and return it.

        It finds the plan with the least amount of steps and chooses to pursue
        that plan.
        """
        self.logger.info("Getting best plan")
        goalGraph = self.mem.get(self.mem.GOAL_GRAPH)
        if not goalGraph:
            self.logger.warn("No goal graph")
            return None

        bestPlan = None
        bestLength = float("inf")
        for nextPlan in goalGraph.allMatchingPlans(goals):
            planLen = len(nextPlan.get_remaining_steps())
            if planLen < bestLength and planLen != 0:
                bestPlan = nextPlan
                bestLength = planLen

        self.logger.info("Best plan is {}".format(bestPlan))
        return bestPlan

    def run(self, cycle, verbose=2):
        """Choose an action to take and store it in MIDCA's memory."""
        plan = None
        goalsAchieved = set()

        self.logger.info("Retrieving goals and plan")
        goals = self.mem.get(self.mem.CURRENT_GOALS)
        plan = self.get_best_plan(self.world, goals, verbose)

        trace = self.mem.trace
        if trace:
            trace.add_module(cycle, self.__class__.__name__)
            trace.add_data("WORLD", copy.deepcopy(self.world.agent()))
            trace.add_data("GOALS", copy.deepcopy(goals))
            trace.add_data("PLAN", copy.deepcopy(plan))

        if plan is not None:
            action = plan.get_next_step()

            if not action:
                if verbose >= 1:
                    print "Plan to achieve goals has already been completed. Taking no action."
                self.mem.add(self.mem.ACTIONS, [])
                self.logger.info("Plan to achieve goals has already been completed")

            else:
                if verbose == 1:
                    print "Action selected:", action
                elif verbose >= 2:
                    print("Selected action " + str(action) + " from plan:\n")
                    if verbose >= 3:
                        for a in plan:
                            print "  "+str(a)
                self.logger.info("Next action is: {} from plan:".format(action))
                self.logger.info("\t" + str(plan))

                self.world.send_action(str(action))
                self.mem.add(self.mem.ACTIONS, [action])
                self.logger.info("Executed and memorized action")

                actions = self.mem.get(self.mem.ACTIONS)
                if len(actions) > 400:
                    actions = actions[200:]
                    self.mem.set(self.mem.ACTIONS, actions)
                    self.logger.info("Trimmed 200 old actions")

                plan.advance()

                if trace:
                    trace.add_data("ACTION", action)
        else:
            if verbose >= 1:
                print "MIDCA will not select an action this cycle."
            self.logger.info("There is no plan, MIDCA will not take an action")

            self.mem.add(self.mem.ACTIONS, [])
            for g in goals:
                self.mem.get(self.mem.GOAL_GRAPH).remove(g)
                self.logger.info("Removed goal {}".format(g))

            if trace:
                trace.add_data("ACTION", None)


class OperatorGiveGoals(base.BaseModule, object):
    """
    Allows an automatic operator to impart generated goals on agents.

    This module looks in MIDCA's memory for a planned mapping of goals to available
    agents and the gives each goal to its proper agent.
    """

    def __init__(self, logger=logging.getLogger("dummy")):
        """Instantiate a ``OperatorGiveGoals`` module; with a logger if desired."""
        super(OperatorGiveGoals, self).__init__()
        self.logger = logger

    def init(self, world, mem):
        """Give the module critical MIDCA data about world state and memory."""
        self.mem = mem
        self.client = world

    def run(self, cycle, verbose=2):
        """
        Impart each remembered goal on the appropriate agent.

        In MIDCA's memory, planned goals are stored as a pair where the first
        element is the agent which should carry out the goal and the second is
        the ``Goal`` which should be given to the agent. This function converts
        each ``Goal`` into a string parseable by the agent and then sends any
        pertinent information (e.g. enemy to target) to the agent, before sending
        the goal string.
        """
        self.logger.info("Retrieving planned goal assignments")
        plannedGoals = self.mem.get("PLANNED_GOALS")
        if plannedGoals is None:
            self.logger.info("There are no planned goal assignments")
            return

        for pGoal in plannedGoals:
            self.logger.info("Assigning goal {}".format(pGoal))
            agt = pGoal[0]
            goal = pGoal[1]
            if goal['predicate'] == 'killed':
                target = goal[0]
                goalStr = 'killed({})'.format(target)
                self.client.inform(agt, target)
                if verbose >= 1:
                    print("Informed {} about {}".format(agt, target))
                self.logger.info("Informed {} about {}".format(agt, target))

            self.logger.info("Sending goal string {} to {}".format(agt, goalStr))
            self.client.direct(agt, goalStr)
            if verbose >= 1:
                print("Directed {} to have goal {}".format(agt, goalStr))
