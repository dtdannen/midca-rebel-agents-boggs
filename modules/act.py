import copy

from MIDCA import base


class SimpleAct(base.BaseModule):
    """Allows MIDCA to execute actions in a plan by affecting the World."""

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
            if planLen < bestLength and planLen != 0:
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
            trace.add_data("WORLD", copy.deepcopy(self.world.agent()))
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

                self.world.send_action(str(action))
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


class OperatorGiveGoals(base.BaseModule):
    """
    Allows an automatic operator to impart generated goals on agents.

    This module looks in MIDCA's memory for a planned mapping of goals to available
    agents and the gives each goal to its proper agent.
    """

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
        plannedGoals = self.mem.get("PLANNED_GOALS")
        if plannedGoals is None:
            return
        for pGoal in plannedGoals:
            agt = pGoal[0]
            goal = pGoal[1]
            if goal['predicate'] == 'killed':
                target = goal[0]
                goalStr = 'killed({})'.format(target)
                if verbose >= 1: print("Informed {} about {}".format(agt, target))
                self.client.inform(agt, target)
            self.client.direct(agt, goalStr)
            if verbose >= 1: print("Directed {} to have goal {}".format(agt, goalStr))
