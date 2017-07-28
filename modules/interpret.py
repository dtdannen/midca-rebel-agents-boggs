from MIDCA import base, goals
import re
import socket
import world_utils as wu


class StateDiscrepancyDetector(base.BaseModule):
    """
    Allows MIDCA to identify discrepancies between expected and actual state.

    This is a simplistic version, but it compares what it expects the world to
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
            self.mem.set(self.mem.DISCREPANCY, diffs)
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

        for goal in currGoals:
            goalValid = state.valid_goal(goal)
            if not goalValid[0]:
                discrepancies[goal] = goalValid[1]
                if verbose >= 2:
                    print("Found goal discrepancy: {}={}".format(goal, goalValid[1]))

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
        goalPred = goal.kwargs['predicate']

        if goalPred == 'agent-at':
            dest = goal.args[0]
            if disc == 'unpassable':
                return 'unpassable'
            if disc == 'no-access':
                trialPath = state.navigate_to(dest, doorsOpen=True)
                if trialPath:
                    return 'door-blocking'
                return 'no-access'

        if goalPred == 'open':
            if disc == 'no-object':
                return 'no-object'

        if goalPred == 'killed':
            if disc == 'no-target':
                return 'target-not-found'
            elif disc == 'civi-killed':
                return 'civi-in-AOE'

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

        self.mem.set(self.mem.DISCREPANCY, None)
        self.mem.set(self.mem.EXPLANATION, True)
        self.mem.set(self.mem.EXPLANATION_VAL, explanations)
        if self.mem.trace:
            self.mem.trace.add_data("EXPLANATIONS", explanations)


class UserGoalInput(base.BaseModule):
    """
    Allows MIDCA to create a goal based on user input.

    DEPRECATED
    """

    def init(self, world, mem):
        self.mem = mem
        self.world = world

    def run(self, cycle, verbose=0):
        """
        Allow user to give MIDCA agent a goal.

        Currently, the user can tell the agent to move to a certain location or
        to open whatever is locked at the given objective point.

        Goals are given as `goal-type args`, and currently valid goals are
            agent-at (x,y)
            open (x,y)
        """
        if self.mem.trace:
            self.mem.trace.add_module(cycle, self.__class__.__name__)

        self.state = self.mem.get(self.mem.STATES)[-1]

        while True:
            if verbose >= 2:
                print("""You may enter a goal as listed below:
                \r\r\ragent-at (x,y) : Moves the agent to (x, y)""")
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
        acceptable_goals = ['agent-at', 'open']

        if userIn == 'q' or userIn == '':
            return userIn

        goalData = userIn.split()

        if goalData[0] not in acceptable_goals:
            print("{} is not a valid goal command".format(goalData[0]))
            return False
        goalPred = goalData[0]

        if goalPred in ['agent-at', 'open']:
            # goalData [1] should be of form (x,y)
            x, y = goalData[1].strip('()').split(',')
            try:
                x = int(x)
                y = int(y)
            except ValueError:
                print("x and y must be integers")
                return False
            goalLoc = (x, y)

            goal = goals.Goal(goalLoc, predicate=goalPred)

        return goal


class PrimitiveRemoteUserGoalInput(base.BaseModule):
    """
    Allows MIDCA to create a goal based on user input.

    DEPRECATED
    """

    def init(self, world, mem):
        self.mem = mem
        self.world = world
        # Here, as with other Remote modules, world is really the client

    def run(self, cycle, verbose=0):
        """
        Allow a remote user to give MIDCA agent a goal.

        Currently, the user can tell the agent to move to a certain location or
        to open whatever is locked at the given objective point.

        Goals are given as `goal-type args`, and currently valid goals are
            agent-at (x,y)
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
        acceptable_goals = ['agent-at', 'open']

        if userIn == 'q' or userIn == '':
            return userIn

        goalData = userIn.split()

        if goalData[0] not in acceptable_goals:
            print("{} is not a valid goal command".format(goalData[0]))
            return False
        goalPred = goalData[0]

        if goalPred in ['agent-at', 'open']:
            # goalData [1] should be of form (x,y)
            x, y = goalData[1].strip('()').split(',')
            try:
                x = int(x)
                y = int(y)
            except ValueError:
                print("x and y must be integers")
                return False
            goalLoc = (x, y)

            goal = goals.Goal(goalLoc, predicate=goalPred)

        return goal

    def get_user_inputs(self):
        data = None
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.connect(("localhost", self.userPort))
            sock.sendall("input")

            if self.client:
                self.client.stdin.write(self.autoFile.readline())

            data = sock.recv(4096)
        except socket.error:
            pass
        finally:
            sock.close()
        return data


class RemoteUserGoalInput(base.BaseModule):
    """Allows MIDCA to create a goal based on user input."""

    def init(self, world, mem):
        self.mem = mem
        self.world = world
        # Here, as with other Remote modules, world is really the client

    def run(self, cycle, verbose=0):
        """
        Allow a remote user to give MIDCA agent a goal.

        Currently, the user can tell the agent to move to a certain location or
        to open whatever is locked at the given objective point.

        Goals are given as `goal-type args`, and currently valid goals are
            agent-at (x,y)
            open (x,y)
            killed targetID
        """
        if self.mem.trace:
            self.mem.trace.add_module(cycle, self.__class__.__name__)

        self.state = self.mem.get(self.mem.STATES)[-1]

        operatorInputs = self.world.get_new_goals()
        if not operatorInputs:
            return

        for rawGoal in operatorInputs:
            if rawGoal == "":
                continue
            try:
                rawGoalStr, senderID = rawGoal.split(";")
            except ValueError as e:
                print("Invalid goal string {}".format(rawGoal))
                continue
            try:
                argsIndex = rawGoalStr.index('(')
            except ValueError:
                print("Invalid goal string {}".format(rawGoalStr))
                continue
            goalStr = " ".join((rawGoalStr[:argsIndex], rawGoalStr[argsIndex:]))
            goal, error = self.parse_input(goalStr, senderID)
            if goal:
                print("User added goal; {}".format(goal))
                self.world.dialog(senderID, "Goal added")
            else:
                self.world.dialog(senderID, "Error; {}".format(error))

            if goal:
                self.mem.get(self.mem.GOAL_GRAPH).insert(goal)
                if self.mem.trace:
                    self.mem.trace.add_data("ADDED GOAL", goal)

    def parse_input(self, userIn, senderID):
        """Turn user input into a goal."""
        acceptable_goals = ['agent-at', 'open', 'killed']

        if userIn == 'q' or userIn == '':
            return userIn

        goalData = userIn.split()

        if goalData[0] not in acceptable_goals:
            error = "{} is not a valid goal command".format(goalData[0])
            return False, error
        goalPred = goalData[0]

        if goalPred in ['agent-at', 'open']:
            # goalData [1] should be of form (x,y)
            x, y = goalData[1].strip('()').split(',')
            try:
                x = int(x)
                y = int(y)
            except ValueError:
                error = "x and y must be integers"
                return False, error
            goalLoc = (x, y)

            if not self.state.map.loc_valid(goalLoc) or not self.state.map.loc_is_free(goalLoc):
                error = "Invalid location {} for goal {}".format(goalLoc, goalPred)
                return False, error

            goal = goals.Goal(goalLoc, predicate=goalPred, user=senderID)

        elif goalPred in ['killed']:
            targetID = goalData[1].strip("()")
            target = None
            for obj in self.state.known_objects:
                if obj.id == targetID:
                    target = obj
                    break
            if target is None:
                error = "Don't know of target {}".format(targetID)
                return False, error

            goal = goals.Goal(targetID, predicate=goalPred, user=senderID)

        return goal, ""


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
                    self.world.dialog(goal['user'], "Goal complete")
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


class OperatorInterpret(base.BaseModule):
    """
    A module which allows an automatic operator to interpret world state.

    This module is responsible for all interpretation done by an automatic operator,
    including interpreting incoming messages and identifying enemies and available
    agents.
    """

    def init(self, world, mem):
        """Give the MIDCA module access to important state and memory data."""
        self.mem = mem
        self.client = world

    def interpret_rebellion_msg(self, msgBody):
        """
        Return rebellion information and alternate goals given.

        This function uses a couple of RegEx patterns to scan for information
        pertaining to the rebellion (e.g. the goal, the reason), and for alternate
        goals. It reconstructs the alternate goals from the strings, and then
        returns all of this information as a tuple.

        Arguments:

        ``msgBody``, *str*:
            The message indicating an agent is rebelling.

        ``return``, *tuple*:
            A tuple containing all the information extracted from the message.
            The elements are::

                (Goal rebelGoal, str rebelReason, list rebelInfo, list altGoals)

            such that ``rebelInfo`` is a list of strings which contain miscellaneous
            rebellion info (e.g. civilians) and ``altGoals`` is a list of alternative
            goals where the index of a goal corresponds to the numerical option of
            that goal.
        """
        rebDataPattern = re.compile(r"\w+=.+")
        altGoalsPattern = re.compile(r"\d+\) .*")

        rebDataStrs = re.findall(rebDataPattern, msgBody)
        altGoalsStrs = re.findall(altGoalsPattern, msgBody)

        rebelInfo = []
        for rebDataStr in rebDataStrs:
            name, data = rebDataStr.split('=')
            if name == 'goal':
                rebelGoal = wu.goal_from_str(data)
            elif name == 'reason':
                rebelReason = data
            else:
                rebelInfo.append("=".join([name, data]))

        altGoals = []
        for altGoalStr in altGoalsStrs:
            if "Goal" in altGoalStr:
                altGoals.append(wu.goal_from_str(altGoalStr))
            elif "Reject Rebellion" in altGoalStr:
                altGoals.append("reject")
            else:
                altGoals.append("none")
        return (rebelGoal, rebelReason, rebelInfo, altGoals)

    def run(self, cycle, verbose=2):
        """
        Interpret the world state and remember it.

        This module interprets the world state and new messages received by the
        operator. It flags rebellions, living enemies, and unassigned operators
        for handling later.
        """
        if self.mem.trace:
            self.mem.trace.add_module(cycle, self.__class__.__name__)

        msgs = self.mem.get("MESSAGES")
        currOp = self.client.operator()

        activeAgents = self.mem.get("ACTIVE_AGENTS")
        if activeAgents is None:
            activeAgents = []

        rebellions = {}
        for msg in msgs:
            msgBody = msg[0]
            msgSender = msg[1]
            # TODO: Figure out why new, unified rebel message isn't catching.

            # if a goal was successful added, that agent is now active
            if msgBody == 'Goal added':
                if msgSender not in activeAgents:
                    self.mem.add("ACTIVE_AGENTS", msgSender)
                continue

            # if a goal was cancelled, that agent is now inactive
            elif 'Goal complete' in msgBody or 'invalid goal' in msgBody:
                # removing an agent from memory is a bit tricky
                activeAgents = self.mem.get("ACTIVE_AGENTS")
                for agt in activeAgents:
                    if agt == msgSender:
                        activeAgents.remove(agt)
                self.mem.set("ACTIVE_AGENTS", activeAgents)
                continue

            # if there's a rebellion, we need to flag that
            elif "rebellion" in msgBody:
                rebGoal, rebReason, rebInfo, altGoals = self.interpret_rebellion_msg(msgBody)
                self.mem.add("REBELLIONS", (rebGoal, rebReason, rebInfo, altGoals, msgSender))

        self.mem.set("ENEMIES", currOp.enemies)

        activeAgents = self.mem.get("ACTIVE_AGENTS")
        print("Active agents: {}".format(activeAgents))
        # activeAgents should be a dict with currently active agents as keys and
        # their goals as values.
        if activeAgents is None:
            activeAgents = []
        availAgents = set([agt.id for agt in currOp.map.agents]) - set(activeAgents)
        print("Avail agents: {}".format(availAgents))
        self.mem.set("AVAIL_AGENTS", availAgents)
