import copy

from MIDCA import base


class CompletionEvaluator(base.BaseModule):
    """Evaluates whether goals have been completed and new goals are needed."""

    def init(self, world, mem):
        self.mem = mem
        self.world = world

    def run(self, cycle, verbose=2):
        try:
            goals = self.mem.get(self.mem.CURRENT_GOALS)
        except KeyError:
            goals = []

        trace = self.mem.trace
        if trace:
            trace.add_module(cycle, self.__class__.__name__)
            trace.add_data("WORLD", copy.deepcopy(self.world))
            trace.add_data("GOALS", copy.deepcopy(goals))

        goalGraph = self.mem.get(self.mem.GOAL_GRAPH)

        goals_changed = False
        if goals:
            for goal in goals:
                if self.world == goal.kwargs['state']:
                    print("Goal {} completed!".format(goal))
                    score = self.mem.get(self.mem.DELIVERED)
                    if score:
                        self.mem.set(self.mem.DELIVERED, score + 1)
                    else:
                        self.mem.set(self.mem.DELIVERED, 1)
                    goalGraph.remove(goal)
                    if trace: trace.add_data("REMOVED GOAL", goal)
                    goals_changed = True
                else:
                    print("Goal {} not completed yet".format(goal))

            numPlans = len(goalGraph.plans)
            goalGraph.removeOldPlans()
            newNumPlans = len(goalGraph.plans)
            if numPlans != newNumPlans and verbose >= 1:
                print "Removed {} plans that no longer apply.".format(numPlans - newNumPlans)
                goals_changed = True
        else:
            print("No current goals, skipping eval")
        if trace and goals_changed: trace.add_data("GOALS", goals)
