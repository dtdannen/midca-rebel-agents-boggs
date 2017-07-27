import copy

from MIDCA import base, goals


class Rebellion(object):
    """Holds information pertaining to an agent's rebellion against a specific goal."""

    def __init__(self, goal, **kwargs):
        assert isinstance(goal, goals.Goal), "A rebellion must be against a goal"
        self.goal = goal
        self.kwargs = kwargs

    def __contains__(self, item):
        return item in self.kwargs or item == 'goal'

    def __getitem__(self, item):
        if item not in self:
            raise KeyError("{} is not a valid key for {}".format(item, repr(self)))
        if item == 'goal':
            return self.goal
        else:
            return self.kwargs[item]

    def __setitem__(self, item, val):
        if item not in self:
            raise KeyError("{} is not a valid key for {}".format(item, repr(self)))
        if item == 'goal':
            raise ValueError("You can't change a rebellion's rejected goal")
        self.kwargs[item] = val
        return True

    def __str__(self):
        retStr = "rebellion(goal={}\n".format(self.goal)
        for kw in self.kwargs:
            retStr += "          {}={}\n".format(kw, self.kwargs[kw])
        retStr += "         )"
        return retStr

    def __repr__(self):
        return "rebellion(goal={})".format(self.goal)


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

    @property
    def agent(self):
        return self.world.agent()

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
                    self.world.dialog(goal.kwargs['user'], "removing invalid goal {}".format(goal))
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
                            self.world.dialog(goal['user'], "added a new goal {}".format(newGoal))
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
                    self.world.dialog(goal.kwargs['user'], "removing invalid goal {}".format(goal))
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
                    self.world.dialog(goal.kwargs['user'], "removing invalid goal {}".format(goal))
                    if verbose >= 1:
                        print("removing invalid goal {}".format(goal))
                    if self.mem.trace:
                        self.mem.trace.add_data("REMOVED GOAL", goal)

                # NOTE: This is where the rebellion happens!!
                elif reason == 'civi-in-AOE':
                    civilians = self.agent.get_civs_in_blast()
                    rebellion = Rebellion(goal, reason=reason, civilians=civilians)
                    if verbose >= 1:
                        print("rejecting goal {}".format(goal))
                        print(str(rebellion))
                    if self.mem.trace:
                        self.mem.trace.add_data("REBELLION", rebellion)
                    if not self.mem.get("REBELLION"):
                        self.mem.set("REBELLION", [rebellion])
                    else:
                        self.mem.add("REBELLION", rebellion)

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

    @property
    def agent(self):
        return self.world.agent()

    def run(self, cycle, verbose=0):
        """Check if there should be a rebellion, and then follow through if so."""
        if self.mem.trace:
            self.mem.trace.add_module(cycle, self.__class__.__name__)

        rebellions = self.mem.get("REBELLION")
        if not rebellions:
            return

        for rebellion in rebellions:
            goal = rebellion.goal
            reason = rebellion['reason']
            print("Rebelling because {}".format(reason))
            self.remove_goal(goal)

            if reason == 'civi-in-AOE':
                for civi in rebellion['civilians']:
                    self.world.inform(goal['user'], civi.id)

            altGoals = self.gen_alt_goals(goal, reason)
            if self.mem.trace:
                self.mem.trace.add_data("ALTERNATE GOALS", altGoals)

            selectedGoal = self.get_response(altGoals, goal['user'], rebellion)
            if selectedGoal is not None:
                self.add_goal(selectedGoal)

            if self.mem.trace:
                self.mem.trace.add_data("USER CHOICE", selectedGoal)

        self.mem.set("REBELLION", None)
        return

    def get_response(self, altGoals, user, rebellion):
        goalKey = self.relate_rebellion(altGoals, user, rebellion)
        response = self.world.wait_for_dialogs(user)
        try:
            response = response[0]
        except IndexError:
            print("ill-formed dialog response: {}".format(response))
        try:
            response = int(response)
        except ValueError:
            pass

        while response not in goalKey:
            self.relate_alt_goals(altGoals, user)
            response = self.world.wait_for_dialogs(user)[0]
            try:
                response = int(response)
            except ValueError:
                pass

        selectedGoal = goalKey[response]
        return selectedGoal

    def relate_rebellion(self, altGoals, senderID, rebellion):
        """Relate possible alt goals to user and create lookup dict for response."""
        goalKey = {}
        dialogStr = "Rebellion:\n{}\nPossible alternate goals:\n".format(str(rebellion))
        goalNum = 1
        for goal in altGoals:
            dialogStr += "\t{}) {}\n".format(goalNum, goal)
            goalKey[goalNum] = goal
            goalNum += 1
        dialogStr += "\t{}) Reject Rebellion\n".format(goalNum)
        goalNum += 1
        dialogStr += "\t{}) None".format(goalNum)
        goalKey[goalNum] = None

        self.world.dialog(senderID, dialogStr)
        return goalKey

    def gen_alt_goals(self, oldGoal, reason):
        """Create and return possible alternate goals to a rejected goal."""
        altGoals = []
        if reason == 'civi-in-AOE':
            for enemy in self.agent.filter_objects(objType="NPC", civi=False, alive=True):
                altGoal = goals.Goal(enemy.id, predicate='killed', user=oldGoal['user'])
                if self.agent.valid_goal(altGoal)[0]:
                    altGoals.append(altGoal)

        return altGoals

    def remove_goal(self, goal):
        goalGraph = self.mem.get(self.mem.GOAL_GRAPH)
        goalGraph.remove(goal)
        if self.mem.trace:
            self.mem.trace.add_data("REJECTED GOAL", goal)

    def add_goal(self, goal):
        goalGraph = self.mem.get(self.mem.GOAL_GRAPH)
        goalGraph.add(goal)


class OperatorHandleRebelsFlexible(base.BaseModule):
    """
    Interact with agents which are rebelling, always choosing another goal.

    This module checks whether there are any rebelling agents based on what
    is in MIDCA's memory, and then interacts with each agent. This module
    prefers to always choose a goal if given choices. Otherwise, it will
    choose for the agent to have no goal.
    """

    def init(self, world, mem):
        """Give the module criticial MIDCA information about state and memory."""
        self.mem = mem
        self.client = world

    def run(self, cycle, verbose=2):
        """
        Handle any rebellions by choosing a new goal.

        This function looks through MIDCA's memory to see if "REBELLION" has
        any data stored in it, and, if so, handle that data. The function
        identifies why the agent rebelled, examines the alternative goals
        given by the agent, and chooses one to give the agent. The function
        prefers to choose another goal over no goal, and no goal over overriding
        the rebellion.
        """
        if self.mem.trace:
            self.mem.trace.add_module(cycle, self.__class__.__name__)

        invalidTargets = self.mem.get("INVALID_TARGETS")
        if invalidTargets is None:
            invalidTargets = []

        rebellions = self.mem.get("REBELLIONS")
        self.mem.set("REBELLIONS", [])
        if rebellions is None:
            return
        # rebellions will be a list of tuples which include all pertinent
        # data about each the rebellion, including which agent rebelled.
        for rebellion in rebellions:
            rebGoal, rebReason, rebInfo, altGoals, rebAgt = rebellion
            responseOption = 1
            if rebGoal['predicate'] == 'killed' and rebReason == 'civi-in-AOE':
                invalidTargets.append(rebGoal[0])
                # NOTE: Here is where the flexibility happens (i.e. operator personality)
                for potentialGoal in altGoals:
                    if isinstance(potentialGoal, goals.Goal):
                        break
                    elif potentialGoal == "none":
                        break
                    responseOption += 1
            # NOTE: We can add more rebellion types later

            self.client.dialog(rebAgt, str(responseOption))

            if altGoals[responseOption-1] == "none":
                # We need to remove the agent from the active agents list
                activeAgents = self.mem.get("ACTIVE_AGENTS")
                for agt in activeAgents:
                    if agt == rebAgt:
                        activeAgents.remove(agt)
                self.mem.set("ACTIVE_AGENTS", activeAgents)

            self.mem.set("INVALID_TARGETS", invalidTargets)
