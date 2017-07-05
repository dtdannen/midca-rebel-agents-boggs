import copy

from MIDCA import base


class SimpleAct(base.BaseModule):
    """Allows MIDCA to execute actions in a plan by affecting the Dungeon."""

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
        goalGraph = self.mem.get(self.mem.GOAL_GRAPH)
        if not goalGraph:
            return None
        bestPlan = None
        bestLength = float("inf")
        for nextPlan in goalGraph.allMatchingPlans(goals):
            planLen = len(nextPlan.get_remaining_steps())
            if planLen < bestLength:
                bestPlan = nextPlan
                bestLength = planLen
        return bestPlan

    def run(self, cycle, verbose=2):
        """Choose an action to take and store it in MIDCA's memory."""
        plan = None
        goalsAchieved = set()
        goals = self.mem.get(self.mem.CURRENT_GOALS)
        plan = self.get_best_plan(self.world, goals, verbose)

        trace = self.mem.trace
        if trace:
            trace.add_module(cycle, self.__class__.__name__)
            trace.add_data("WORLD", copy.deepcopy(self.world))
            trace.add_data("GOALS", copy.deepcopy(goals))
            trace.add_data("PLAN", copy.deepcopy(plan))

        if plan is not None:
            action = plan.get_next_step()
            if not action:
                if verbose >= 1:
                    print "Plan to achieve goals has already been completed. Taking no action."
                self.mem.add(self.mem.ACTIONS, [])

            else:
                if verbose == 1:
                    print "Action selected:", action
                elif verbose >= 2:
                    print("Selected action " + str(action) + " from plan:\n")
                    if verbose >= 3:
                        for a in plan:
                            print "  "+str(a)

                self.mem.add(self.mem.ACTIONS, [action])
                actions = self.mem.get(self.mem.ACTIONS)
                if len(actions) > 400:
                    actions = actions[200:]
                    self.mem.set(self.mem.ACTIONS, actions)
                plan.advance()

                if trace:
                    trace.add_data("ACTION", action)
        else:
            if verbose >= 1:
                print "MIDCA will not select an action this cycle."
            self.mem.add(self.mem.ACTIONS, [])
            for g in goals:
                self.mem.get(self.mem.GOAL_GRAPH).remove(g)

            if trace:
                trace.add_data("ACTION", None)
