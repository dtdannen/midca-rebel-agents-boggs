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

            # If the goal is a agent-at goal, see if it's impossible to achieve
            if goal.kwargs['predicate'] == 'agent-at':
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

            # If the goal is for an NPC to be killed and there's a problem, it's
            # either because the target given isn't around anymore or because
            # the attack would kill civilians.
            elif goal.kwargs['predicate'] == 'killed':
                if reason == 'target-not-found':
                    goalGraph.remove(goal)
                    # TODO: Alert user to goal removal and reason why
                    if verbose >= 1:
                        print("removing invalid goal {}".format(goal))
                    if self.mem.trace:
                        self.mem.trace.add_data("REMOVED GOAL", goal)

                # NOTE: This is where the rebellion happens!!
                elif reason == 'civi-in-AOE':
                    if verbose >= 1:
                        print("rejecting goal {}".format(goal))
                    if self.mem.trace:
                        self.mem.trace.add_data("REJECTED GOAL", goal)
                    self.mem.set("REBELLION", goal)
                    self.mem.set("REBEL_EXPLAN", reason)

                else:
                    raise Exception("Discrepancy reason {} shouldn't exist".format(reason))

            else:
                raise NotImplementedError("Goal {} is not there yet".format(goal))

        if verbose >= 1:
            print("Done managing goals \n")
        if self.mem.trace:
            self.mem.trace.add_data("GOALS", goalGraph)


class HandleRebellion(base.BaseModule):
    """Allow MIDCA to rebel against goals it deems unworthy."""

    def init(self, world, mem):
        self.mem = mem
        self.world = world

    def run(self, cycle, verbose=0):
        rebellion = self.mem.get("REBELLION")
        if rebellion:
            # TODO Notify the user through the communications channel
            # TODO Give explanation through notification channel
            # TODO Relate location of civilians through communication channel
            # TODO Ask for new info through notification channel
