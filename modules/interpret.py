from MIDCA import base, goals
import re


class StateDiscrepancyDetector(base.BaseModule):
    """
    Allows MIDCA to identify discrepancies between expected and actual state.

    This is a simplistic version, but it compares what it expects the dungeon to
    be with what it really is by copying the Agent from the last state and
    applying the current move to it. The it checks whether there's a difference
    between the simulated map of the old Agent and the real map of the current
    Agent.
    """

    def init(self, world, mem):
        self.mem = mem
        self.world = world

    def get_expected(self, action):
        """Produce the expected Agent given an action."""
        oldStates = self.mem.get(self.mem.STATES)
        if oldStates and len(oldStates) > 1:
            oldAgent = oldStates[-2]
        else:
            # print("Old states not found: {}".format(oldStates))
            return None

        return oldAgent.forecast_action(action)

    def run(self, cycle, verbose=2):
        """
        Check for discrepancies between the actual and expect world state.

        If this finds any discrepancies in state, it stores them in MIDCA's
        memory as a dict.
        """
        discrepancies = self.mem.get(self.mem.DISCREPANCY)
        if discrepancies is None:
            discrepancies = {}

        if self.mem.trace:
            self.mem.trace.add_module(cycle, self.__class__.__name__)

        if verbose >= 1:
            print("\nDiscrepancy Check...")
        currState = self.mem.get(self.mem.STATE)
        if self.mem.get(self.mem.ACTIONS):
            actions = self.mem.get(self.mem.ACTIONS)[-1]
            diffs = {}
            for action in actions:
                expected = self.get_expected(action)
                if not expected:
                    if verbose >= 1:
                        print("No previous state to expect from!")
                        return
                diffs = currState.diff(expected)
            if len(diffs) == 0:
                self.mem.trace.add_data("DISCREPANCY", None)
                return
            if verbose >= 1:
                print("Found {} discrepancies".format(len(diffs.keys())))
            if verbose >= 2:
                print("Discrepancies found are {}".format(diffs))
            self.mem.set(self.mem.DISCREPANCY, (diffs))
            self.mem.trace.add_data("DISCREPANCY", diffs)

        else:
            if verbose >= 1:
                print("No actions to detect discrepancies from")


class GoalValidityChecker(base.BaseModule):
    """
    Allows MIDCA to determine whether all current goals are still valid.

    This module checks each goal in the goal graph for validity against the
    current state, and reports any goals which are not valid.
    """

    def init(self, world, mem):
        self.mem = mem
        self.world = world

    def run(self, cycle, verbose=0):
        if self.mem.trace:
            self.mem.trace.add_module(cycle, self.__class__.__name__)

        discrepancies = self.mem.get(self.mem.DISCREPANCY)
        if discrepancies is None:
            discrepancies = {}

        state = self.mem.get(self.mem.STATE)
        if state is None:
            if verbose >= 1:
                print("No state to check goal validity against, continuing")
            return

        currGoals = self.mem.get(self.mem.CURRENT_GOALS)
        if currGoals is None:
            if verbose >= 1:
                print("No current goals to check validity, continuing")
            return

        for goal in currGoals:
            goalValid = state.valid_goal(goal)
            if not goalValid[0]:
                discrepancies[goal] = goalValid[1]
                if verbose >= 2:
                    print("Found goal discrepancy: {}={}".format(goal, goalValid[1]))

        self.mem.set(self.mem.DISCREPANCY, discrepancies)

        if verbose >= 1:
                    print("End discrepancy check...\n")


class DiscrepancyExplainer(base.BaseModule):
    """Allows MIDCA to explain discrepancies in the state."""

    def init(self, world, mem):
        self.mem = mem
        self.world = world
        self.mem.set(self.mem.EXPLANATION, None)
        self.mem.set(self.mem.EXPLANATION_VAL, None)

    def goal_disc_explain(self, goal, disc):
        """
        Figure out why the given goal is invalid.

        Tries to determine whether a goal is uncompletable or whether there is
        a surmountable obstacle.
        """
        state = self.mem.get(self.mem.STATE)
        goalAction = goal.kwargs['predicate']

        if goalAction == 'move-to':
            dest = goal.args[0]
            if disc == 'unpassable':
                return 'unpassable'
            if disc == 'no-access':
                trialPath = state.navigate_to(dest, doorsOpen=True)
                if trialPath:
                    return 'door-blocking'
                return 'no-access'

        if goalAction == 'open':
            if disc == 'no-object':
                return 'no-object'

    def explain(self, discAt, discContent):
        """Try to explain a discrepancy."""
        # If the discrepancy is at a point on the map, it's probably from moving
        if re.match('\(\d*, \d*\)', str(discAt)):
            return('agent-move')

        elif isinstance(discAt, goals.Goal):
            reason = self.goal_disc_explain(discAt, discContent)
            return reason
        else:
            return('unknown-cause')

    def run(self, cycle, verbose=2):
        discDict = self.mem.get(self.mem.DISCREPANCY)
        if not discDict:
            if verbose >= 1:
                print("No discrepancies to explain.")
            return

        explanations = []
        for disc in discDict:
            explanations.append((disc, self.explain(disc, discDict[disc])))

        if verbose >= 2:
            print("Explanations:")
            for explan in explanations:
                print("  {}: {}".format(explan[0], explan[1]))

        self.mem.set(self.mem.EXPLANATION, True)
        self.mem.set(self.mem.EXPLANATION_VAL, explanations)


class GoalManager(base.BaseModule):
    """
    Allows MIDCA to manage goals given its percepts.

    This module checks to ensure all goals are still valid, and whether we need
    new goals in order to accomplish a goal we already have.
    """

    def init(self, world, mem):
        self.mem = mem
        self.world = world

    def findDoorsFor(self, goal):
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
            if not isinstance(explan[0], goals.Goal):
                continue
            goal = explan[0]
            reason = explan[1]
            if goal.kwargs['predicate'] == 'move-to':
                if reason == 'unpassable':
                    goalGraph.remove(goal)
                    if verbose >= 1:
                        print("removing invalid goal {}".format(goal))
                if reason == 'door-blocking':
                    doors = self.findDoorsFor(goal)
                    for door in doors:
                        newGoal = goals.Goal(door.location, predicate='open', parent=goal)
                        goalGraph.add(newGoal)
                        if verbose >= 1:
                            print("added a new goal {}".format(newGoal))
                else:
                    raise Exception("Discrepancy reason {} shouldn't exist".format(reason))
            elif goal.kwargs['predicate'] == 'open':
                if reason == 'no-object':
                    goalGraph.remove(goal)
                    if verbose >= 1:
                        print("removing invalid goal {}".format(goal))
                else:
                    raise Exception("Discrepancy reason {} shouldn't exist".format(reason))
            else:
                raise NotImplementedError("Goal {} is not there yet".format(goal))

        if verbose >= 1:
            print("Done managing goals \n")


class UserGoalInput(base.BaseModule):
    """Allows MIDCA to create a goal based on user input."""

    def init(self, world, mem):
        self.mem = mem
        self.world = world

    def run(self, cycle, verbose=0):
        self.state = self.mem.get(self.mem.STATES)[-1]
        while True:
            if verbose >= 2:
                print("""You may enter a goal as listed below:
                \r\r\rmove-to x y : Moves the agent to (x, y)""")
            userInput = raw_input("Enter a goal or hit RETURN to continue.  ")
            goal = self.parse_input(userInput)
            if goal == 'q':
                return goal
            elif goal == '':
                return 'continue'
            try:
                if goal and self.state.valid_goal(goal)[0]:
                    self.mem.get(self.mem.GOAL_GRAPH).insert(goal)
            except Exception as e:
                print(e.args[0])

    def parse_input(self, userIn):
        """Turn user input into a goal."""
        if userIn == 'q' or userIn == '':
            return userIn
        goalData = userIn.split()
        if len(goalData) != 3:
            print("Invalid goal. There should be three parts")
            return False

        if goalData[0] not in ['move-to', 'open']:
            print("{} is not a valid goal command".format(goalData[0]))
            return False
        goalAction = goalData[0]

        try:
            x = int(goalData[1])
            y = int(goalData[2])
        except ValueError:
            print("x and y must be integers")
            return False
        goalLoc = (x, y)

        goal = goals.Goal(goalLoc, predicate=goalAction)

        return goal
