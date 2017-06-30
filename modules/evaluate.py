import copy

from MIDCA import base, goals


class GoalManager(base.BaseModule):
    """
    Allows MIDCA to manage goals given its percepts.

    This module checks to ensure all goals are still valid, and whether we need
    new goals in order to accomplish a goal we already have.
    """

    def init(self, world, mem):
        """Give module crucial MIDCA data."""
        self.mem = mem
        self.world = world

    def findDoorsFor(self, goal):
        """
        Return a list of door objects which need to be opened to reach the goal.

        Navigates to the goal by pretending all doors are open, then looks along
        the generated path for door objects and stores them in a list. Not super
        efficient, but it works and I can't think of a better solution.
        """
        dest = goal.args[0]
        state = self.mem.get(self.mem.STATE)
        path = state.navigate_to(dest, doorsOpen=True)
        currTile = state.at

        doors = []
        for moveDir in path:
            if moveDir == 'n':
                currTile = (currTile[0], currTile[1]-1)
            elif moveDir == 's':
                currTile = (currTile[0], currTile[1]+1)
            elif moveDir == 'w':
                currTile = (currTile[0]-1, currTile[1])
            elif moveDir == 'e':
                currTile = (currTile[0]+1, currTile[1])
            if state.get_objects_at(currTile):
                for obj in state.get_objects_at(currTile):
                    if obj.objType == 'DOOR':
                        doors.append(obj)
        return doors

    def run(self, cycle, verbose=2):
        """Check each explanation and if it's about a goal solve that."""
        if self.mem.trace:
            self.mem.trace.add_module(cycle, self.__class__.__name__)

        if not self.mem.get(self.mem.EXPLANATION):
            if verbose >= 1:
                print("No explanations to manage, continuing")
            return

        goalGraph = self.mem.get(self.mem.GOAL_GRAPH)
        if not goalGraph:
            if verbose >= 1:
                print("There are no goals, continuing")
            return

        explans = self.mem.get(self.mem.EXPLANATION_VAL)
        for explan in explans:

            # Make sure it's an explanation of a goal
            if not isinstance(explan[0], goals.Goal):
                continue

            goal = explan[0]
            reason = explan[1]

            # If the goal is a move-to goal, see if it's impossible to achieve
            if goal.kwargs['predicate'] == 'move-to':
                if reason == 'unpassable':
                    # If the tile is unpassable or there is not path to the tile
                    # remove the goal.
                    goalGraph.remove(goal)
                    if verbose >= 1:
                        print("removing invalid goal {}".format(goal))
                    if self.mem.trace:
                        self.mem.trace.add_data("REMOVED GOAL", goal)

                elif reason == 'door-blocking':
                    # If there's a door blocking the goal, find it and add a
                    # sub-goal to open it.
                    doors = self.findDoorsFor(goal)
                    for door in doors:
                        newGoal = goals.Goal(door.location, predicate='open', parent=goal)
                        goalGraph.add(newGoal)
                        if verbose >= 1:
                            print("added a new goal {}".format(newGoal))
                        if self.mem.trace:
                            self.mem.trace.add_data("ADDED GOAL", newGoal)

                else:
                    raise Exception("Discrepancy reason {} shouldn't exist".format(reason))

            # If it's an open goal which is invalid, it's likely because either
            # there is no locked object at the target destination or there is no
            # key to open the object.
            elif goal.kwargs['predicate'] == 'open':
                if reason == 'no-object':
                    goalGraph.remove(goal)
                    if verbose >= 1:
                        print("removing invalid goal {}".format(goal))
                    if self.mem.trace:
                        self.mem.trace.add_data("REMOVED GOAL", goal)

                else:
                    raise Exception("Discrepancy reason {} shouldn't exist".format(reason))

            else:
                raise NotImplementedError("Goal {} is not there yet".format(goal))

        if verbose >= 1:
            print("Done managing goals \n")
        if self.mem.trace:
            self.mem.trace.add_data("GOALS", goalGraph)


class CompletionEvaluator(base.BaseModule):
    """Evaluates whether goals have been completed and new goals are needed."""

    def init(self, world, mem):
        """Give the module critical MIDCA data."""
        self.mem = mem
        self.world = world

    def run(self, cycle, verbose=2):
        """Remove goals which have been completed."""
        self.state = self.mem.get(self.mem.STATE)
        try:
            goals = self.mem.get(self.mem.CURRENT_GOALS)
        except KeyError:
            goals = []

        trace = self.mem.trace
        if trace:
            trace.add_module(cycle, self.__class__.__name__)

        goalGraph = self.mem.get(self.mem.GOAL_GRAPH)

        goals_changed = False
        if goals:
            for goal in goals:
                if self.state.goal_complete(goal):
                    print("Goal {} completed!".format(goal))
                    score = self.mem.get(self.mem.DELIVERED)
                    if score:
                        self.mem.set(self.mem.DELIVERED, score + 1)
                    else:
                        self.mem.set(self.mem.DELIVERED, 1)
                    goalGraph.remove(goal)
                    if trace:
                        trace.add_data("REMOVED GOAL", goal)
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
        if trace and goals_changed:
            trace.add_data("GOALS", goals)
