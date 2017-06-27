import copy
from MIDCA import base


class SimpleIntend(base.BaseModule):
    """Chooses a goal to pursue with no thought."""

    def init(self, world, mem):
        self.mem = mem
        self.world = world

    def run(self, cycle, verbose=2):
        trace = self.mem.trace
        if trace:
            trace.add_module(cycle, self.__class__.__name__)
            trace.add_data("GOALGRAPH", copy.deepcopy(self.mem.GOAL_GRAPH))

        goalGraph = self.mem.get(self.mem.GOAL_GRAPH)

        if not goalGraph:
            if verbose >= 1:
                print "Goal graph not initialized. Intend will do nothing."
            return
        goals = goalGraph.getUnrestrictedGoals()
        goals_selected = []

        if len(goals) > 1:
            # just randomly pick the first one
            goals_selected = [goals[0]]
            self.mem.set(self.mem.CURRENT_GOALS, goals_selected)
        else:
            goals_selected = goals
            self.mem.set(self.mem.CURRENT_GOALS, goals_selected)
        if trace:
            trace.add_data("GOALS", goals)

        if not goals:
            if verbose >= 2:
                print "No goals selected."
        else:
            if verbose >= 2:
                print "Selecting goal(s):",
                for goal in goals_selected:
                    print goal,
                print
