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
        if self.mem.trace:
            self.mem.trace.add_module(cycle, self.__class__.__name__)

        if verbose >= 1:
            print("\nDiscrepancy Check...")
        currState = self.mem.get(self.mem.STATE)
        if self.mem.get(self.mem.ACTIONS):
            actions = self.mem.get(self.mem.ACTIONS)[-1]
            diffs = []
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

        if verbose >= 1:
            print("End discrepancy check...\n")


class DiscrepancyExplainer(base.BaseModule):
    """Allows MIDCA to explain discrepancies in the state."""

    def init(self, world, mem):
        self.mem = mem
        self.world = world
        self.mem.set(self.mem.EXPLANATION, None)
        self.mem.set(self.mem.EXPLANATION_VAL, None)

    def explain(self, discAt, discContent):
        """Try to explain a discrepancy."""
        if re.match('\(\d*, \d*\)', str(discAt)):
            return('agent-move')

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


class UserGoalInput(base.BaseModule):
    """Allows MIDCA to create a goal based on user input."""

    def init(self, world, mem):
        self.mem = mem
        self.world = world

    def run(self, cycle, verbose=0):
        self.state = self.mem.get(self.mem.STATES)[-1]
        while True:
            if verbose >= 5:
                print("""You may enter a goal:
Currently the only possible goal is moving to a location.
Format:
    move-to x y : Moves the agent to (x, y)""")
            userInput = raw_input("Enter a goal or hit RETURN to continue.  ")
            goal = self.parse_input(userInput)
            if goal == 'q':
                return goal
            elif goal == '':
                return 'continue'
            try:
                if goal and self.state.valid_goal(goal):
                    self.mem.get(self.mem.GOAL_GRAPH).insert(goal)
            except Exception as e:
                print(e.args[0])

    def parse_input(self, userIn):
        """Turn user input into a goal."""
        if userIn == 'q' or userIn == '':
            return userIn
        goalData = userIn.split()
        if len(goalData) != 3:
            print("Invalid goal. There should only be three parts")
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
