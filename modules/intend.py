"""Contains the modules which allow MIDCA to choose a goal."""

import copy
from MIDCA import base


class QuickIntend(base.BaseModule):
    """Chooses a goal to pursue based on how fast it can be completed."""

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
        state = self.mem.get(self.mem.STATE)
        if not state:
            return []
        bestScore = float("inf")  # lower scores are preferable
        bestGoal = []
        for goal in goalList:
            if goal.kwargs['predicate'] == 'agent-at':
                dest = goal.args[0]
                linPath = state.map.get_path_to(state.at, dest)
                obstacles = state.map.obstacles_in(linPath)
                goalScore = len(linPath) + 3 * obstacles
            else:
                goalScore = 5
                # TODO: Make heuristic function for open goal.
            if goalScore < bestScore:
                bestGoal = [goal]
                bestScore = goalScore
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
            return
        goals = goalGraph.getUnrestrictedGoals()
        goal_selected, goalScore = self.select_goal(goals)
        self.mem.set(self.mem.CURRENT_GOALS, goal_selected)

        if trace:
            trace.add_data("GOALS", goals)

        if not goals:
            if verbose >= 2:
                print "No goals selected."
        else:
            if verbose >= 2:
                print("Goal {} selected because it had the lowest heuristic score: {}".format(goal_selected[0], goalScore))
