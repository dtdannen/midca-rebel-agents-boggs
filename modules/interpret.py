from MIDCA import base, goals
import re
import socket


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
        """Give module critical MIDCA data."""
        self.mem = mem
        self.world = world

    def get_expected(self, action):
        """
        Produce the expected state of the world given an action.

        Takes the previous world state (an Agent), and applies the action just
        taken by MIDCA to it. The result is what we'd expect to see if nothing
        has changed.
        """
        oldStates = self.mem.get(self.mem.STATES)
        if oldStates and len(oldStates) > 1:
            oldAgent = oldStates[-2]
        else:
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
                self.mem.trace.add_data("DISCREPANCIES", None)
                return
            if verbose >= 1:
                print("Found {} discrepancies".format(len(diffs.keys())))
            if verbose >= 2:
                print("Discrepancies found are {}".format(diffs))
            self.mem.set(self.mem.DISCREPANCY, (diffs))
            self.mem.trace.add_data("DISCREPANCIES", diffs)

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

        foundDiscs = False
        for goal in currGoals:
            goalValid = state.valid_goal(goal)
            if not goalValid[0]:
                discrepancies[goal] = goalValid[1]
                foundDiscs = True
                if verbose >= 2:
                    print("Found goal discrepancy: {}={}".format(goal, goalValid[1]))
        if not foundDiscs:
            discrepancies = None

        self.mem.set(self.mem.DISCREPANCY, discrepancies)
        if self.mem.trace:
            self.mem.trace.add_data("DISCREPANCIES", discrepancies)

        if verbose >= 1:
                    print("End discrepancy check...\n")


class DiscrepancyExplainer(base.BaseModule):
    """Allows MIDCA to explain discrepancies in the state."""

    def init(self, world, mem):
        """Give module crucial MIDCA data, and clear explanations from mem."""
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
        """
        For every discrepancy MIDCA has encountered try and explain it.

        An individual explanation takes the form of a pair in which the first
        calue is the discrepancy and the second is its explanation. After all
        discrepancies have been explained, it stores the list of explanation
        pairs in MIDCA's memory.
        """
        self.mem.set(self.mem.EXPLANATION, None)
        self.mem.set(self.mem.EXPLANATION_VAL, None)
        if self.mem.trace:
            self.mem.trace.add_module(cycle, self.__class__.__name__)

        discDict = self.mem.get(self.mem.DISCREPANCY)
        if not discDict:
            if verbose >= 1:
                print("No discrepancies to explain.")
            self.mem.set(self.mem.EXPLANATION, None)
            self.mem.set(self.mem.EXPLANATION_VAL, None)
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
        if self.mem.trace:
            self.mem.trace.add_data("EXPLANATIONS", explanations)


class UserGoalInput(base.BaseModule):
    """Allows MIDCA to create a goal based on user input."""

    def init(self, world, mem):
        self.mem = mem
        self.world = world

    def run(self, cycle, verbose=0):
        """
        Allow user to give MIDCA agent a goal.

        Currently, the user can tell the agent to move to a certain location or
        to open whatever is locked at the given objective point.

        Goals are given as `goal-type args`, and currently valid goals are
            move-to (x,y)
            open (x,y)
        """
        if self.mem.trace:
            self.mem.trace.add_module(cycle, self.__class__.__name__)

        self.state = self.mem.get(self.mem.STATES)[-1]

        while True:
            if verbose >= 2:
                print("""You may enter a goal as listed below:
                \r\r\rmove-to (x,y) : Moves the agent to (x, y)""")
            userInput = raw_input("Enter a goal or hit RETURN to continue.  ")
            goal = self.parse_input(userInput)

            if goal == 'q':
                return goal
            elif goal == '':
                return 'continue'

            if goal and self.state.valid_goal(goal)[0]:
                self.mem.get(self.mem.GOAL_GRAPH).insert(goal)
                if self.mem.trace:
                    self.mem.trace.add_data("ADDED GOAL", goal)

    def parse_input(self, userIn):
        """Turn user input into a goal."""
        acceptable_goals = ['move-to', 'open']

        if userIn == 'q' or userIn == '':
            return userIn

        goalData = userIn.split()

        if goalData[0] not in acceptable_goals:
            print("{} is not a valid goal command".format(goalData[0]))
            return False
        goalAction = goalData[0]

        if goalAction in ['move-to', 'open']:
            # goalData [1] should be of form (x,y)
            x, y = goalData[1].strip('()').split(',')
            try:
                x = int(x)
                y = int(y)
            except ValueError:
                print("x and y must be integers")
                return False
            goalLoc = (x, y)

            goal = goals.Goal(goalLoc, predicate=goalAction)

        return goal


class RemoteUserGoalInput(base.BaseModule):
    """Allows MIDCA to create a goal based on user input."""
    def __init__(self, userPort):
        super(RemoteUserGoalInput, self).__init__()
        self.userPort = userPort

    def init(self, world, mem):
        self.mem = mem
        self.world = world

    def run(self, cycle, verbose=0):
        """
        Allow a remote user to give MIDCA agent a goal.

        Currently, the user can tell the agent to move to a certain location or
        to open whatever is locked at the given objective point.

        Goals are given as `goal-type args`, and currently valid goals are
            move-to (x,y)
            open (x,y)
        """
        if self.mem.trace:
            self.mem.trace.add_module(cycle, self.__class__.__name__)

        self.state = self.mem.get(self.mem.STATES)[-1]

        userInput = self.get_user_inputs()
        if not userInput:
            return
        goal = self.parse_input(userInput)

        if goal == 'q':
            return goal
        elif goal == '':
            return 'continue'

        if goal and self.state.valid_goal(goal)[0]:
            self.mem.get(self.mem.GOAL_GRAPH).insert(goal)
            if self.mem.trace:
                self.mem.trace.add_data("ADDED GOAL", goal)

    def parse_input(self, userIn):
        """Turn user input into a goal."""
        acceptable_goals = ['move-to', 'open']

        if userIn == 'q' or userIn == '':
            return userIn

        goalData = userIn.split()

        if goalData[0] not in acceptable_goals:
            print("{} is not a valid goal command".format(goalData[0]))
            return False
        goalAction = goalData[0]

        if goalAction in ['move-to', 'open']:
            # goalData [1] should be of form (x,y)
            x, y = goalData[1].strip('()').split(',')
            try:
                x = int(x)
                y = int(y)
            except ValueError:
                print("x and y must be integers")
                return False
            goalLoc = (x, y)

            goal = goals.Goal(goalLoc, predicate=goalAction)

        return goal

    def get_user_inputs(self):
        data = None
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.connect(("localhost", self.userPort))
            sock.sendall("input")
            data = sock.recv(4096)
        except socket.error:
            pass
        finally:
            sock.close()
        return data
