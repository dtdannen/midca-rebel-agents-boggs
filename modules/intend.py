"""Contains the modules which allow MIDCA to choose a goal."""

import copy
import logging
from MIDCA import base


class QuickIntend(base.BaseModule):
    """Chooses a goal to pursue based on how fast it can be completed."""

    def __init__(self, logger=logging.getLogger("dummy")):
        """Instantiate a ``QuickIntend`` module; with a logger if desired."""
        super(QuickIntend, self).__init__()
        self.logger = logger

    def init(self, world, mem):
        """Give the module critical MIDCA data."""
        self.mem = mem
        self.world = world

    def select_goal(self, goalList):
        """
        Find the goal with the shortest estimated plan.

        This doesn't actually form a plan for each possible goal, but uses a
        heuristic to estimate how long the plan will be.
        """
        self.logger.info("Considering potential goals")
        state = self.mem.get(self.mem.STATE)
        if not state:
            raise Exception("No previous state")

        bestScore = float("inf")  # lower scores are preferable
        bestGoal = []
        for goal in goalList:
            self.logger.info("\tAssessing goal {}".format(goal))

            if goal.kwargs['predicate'] == 'agent-at':
                dest = goal.args[0]
                linPath = state.map.get_path_to(state.at, dest)
                obstacles = state.map.obstacles_in(linPath)
                goalScore = len(linPath) + 3 * obstacles
            else:
                goalScore = 5
                # TODO: Make heuristic function for open goal and killed goal.
            self.logger.info("\tGoal score = {}".format(goalScore))

            if goalScore < bestScore:
                bestGoal = [goal]
                bestScore = goalScore
                self.logger.info("\tCurrently, best goal is {}".format(bestGoal))

        return bestGoal, bestScore

    def run(self, cycle, verbose=2):
        """Choose a goal from the goal graph and set it as MIDCA's goal."""
        goalGraph = self.mem.get(self.mem.GOAL_GRAPH)
        trace = self.mem.trace
        if trace:
            trace.add_module(cycle, self.__class__.__name__)
            trace.add_data("GOALGRAPH", copy.deepcopy(goalGraph))

        if not goalGraph:
            if verbose >= 1:
                print "Goal graph not initialized. Intend will do nothing."
            self.logger.warn("Goal graph not initialized, continuing")
            return

        self.logger.info("Retrieving valid goals")
        goals = goalGraph.getUnrestrictedGoals()
        goal_selected, goalScore = self.select_goal(goals)
        self.mem.set(self.mem.CURRENT_GOALS, goal_selected)
        self.logger.info("Selected and memorized goal {}".format(goal_selected))

        if trace:
            trace.add_data("GOALS", goals)

        if not goals:
            if verbose >= 2:
                print "No goals selected."
            self.logger.info("No goals selected")
        else:
            if verbose >= 2:
                print("Goal {} selected because it had the lowest heuristic score: {}".format(goal_selected[0], goalScore))
