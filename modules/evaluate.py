import copy
from random import random
import logging

from MIDCA import base, goals
import world_utils as wu


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

    def __init__(self, logger=logging.getLogger("dummy")):
        """Instantiate a ``GoalManager`` module; with a logger if desired."""
        super(GoalManager, self).__init__()
        self.logger = logger

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
            self.logger.info("No explanations to manage, continuing")
            return

        goalGraph = self.mem.get(self.mem.GOAL_GRAPH)
        if not goalGraph:
            if verbose >= 1:
                print("There are no goals, continuing")
                self.logger.info("There are no goals, continuing")
            return

        self.logger.info("Getting explanations to handle")
        explans = self.mem.get(self.mem.EXPLANATION_VAL)
        for explan in explans:
            self.logger.info("Handling explanation:\n\t{}".format(explan))

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
                    self.logger.info("\tRemoved invalid goal")

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
                        self.world.dialog(goal['user'], "added a new goal {}".format(newGoal))
                        self.logger.info("\tAdded new goal {}".format(newGoal))

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
                    self.logger.info("\tRemoved invalid goal")

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
                    self.logger.info("\tRemoved invalid goal")

                # NOTE: This is where the rebellion happens!!
                elif reason == 'civi-in-AOE':
                    civilians = self.agent.get_civs_in_blast()
                    rebellion = Rebellion(goal, reason=reason, civilians=civilians)
                    self.logger.info("\tGenerated rebellion:\n\t{}".format(rebellion))
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
        self.logger.info("Done managing goals")
        if self.mem.trace:
            self.mem.trace.add_data("GOALS", goalGraph)


class HandleRebellion(base.BaseModule):
    """Allow MIDCA to rebel against goals it deems unworthy."""

    def __init__(self, logger=logging.getLogger("dummy")):
        """Instantiate a ``HandleRebellion`` module; with a logger if desired."""
        super(HandleRebellion, self).__init__()
        self.logger = logger

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

        self.logger.info("Retrieving rebellions")
        rebellions = self.mem.get("REBELLION")
        if not rebellions:
            self.logger.info("No rebellions to handle, continuing")
            return

        for rebellion in rebellions:
            self.logger.info("Handling rebellion:\n{}".format(rebellion))

            goal = rebellion.goal
            reason = rebellion['reason']
            if verbose >= 1:
                print("Rebelling because {}".format(reason))
            self.remove_goal(goal)
            self.logger.info("\tRemoved goal")

            if reason == 'civi-in-AOE':
                for civi in rebellion['civilians']:
                    self.world.inform(goal['user'], civi.id)
                    if verbose >= 1:
                        print("Informed user of {}".format(civi))
                    self.logger.info("\tInformed user of {}".format(civi))

            altGoals = self.gen_alt_goals(goal, reason)
            if verbose >= 1:
                print("Generated alt goals {}".format(altGoals))
            if self.mem.trace:
                self.mem.trace.add_data("ALTERNATE GOALS", altGoals)
            self.logger.info("\tGenerated alt goals:\n\t{}".format(altGoals))

            selectedGoal = self.get_response(altGoals, goal['user'], rebellion)
            if verbose >= 1:
                print("Operator selected goal {}".format(selectedGoal))
            self.logger.info("\tOperator selected choice {}".format(selectedGoal))

            if selectedGoal is not "None":
                self.add_goal(selectedGoal)
                self.logger.info("\tAdded selected goal")

            if self.mem.trace:
                self.mem.trace.add_data("USER CHOICE", selectedGoal)

        self.mem.set("REBELLION", None)
        self.logger.info("Reset rebellions")
        return

    def get_response(self, altGoals, user, rebellion):
        """Relate rebellion to operator and get their response."""
        goalKey = self.relate_rebellion(altGoals, user, rebellion)
        self.logger.info("Generated goal key:\n{}".format(goalKey))

        response = self.world.wait_for_dialogs(user)
        try:
            response = response[0]
        except IndexError:
            print("ill-formed dialog response: {}".format(response))
            self.logger.warn("Malformed rebellion response: {}".format(response))
        try:
            response = int(response)
        except ValueError:
            self.logger.warn("Response not an int: {}".format(response))
            pass
        self.logger.info("User response: {}".format(response))

        while response not in goalKey:
            self.relate_alt_goals(altGoals, user)
            response = self.world.wait_for_dialogs(user)[0]
            self.logger.info("User response: {}".format(response))
            try:
                response = int(response)
            except ValueError:
                self.logger.warn("Response not an int: {}".format(response))
                pass

        selectedGoal = goalKey[response]
        return selectedGoal

    def relate_rebellion(self, altGoals, senderID, rebellion, informOthers=False):
        """
        Indicate to operator and other agents that agent is rebelling.

        This function generates a string which relates the full details of the
        rebellion and the alternative goals the agent has come up with, then gives
        this to the operator who created the goal. It also tells other agents that
        this agent rebelled and informs them of any relevant civilians.
        """
        # Inform operator
        goalKey = {}
        dialogStr = "Rebellion:\n{}\nPossible alternate goals:\n".format(str(rebellion))
        goalNum = 0
        for goal in altGoals:
            dialogStr += "\t{}) {}\n".format(goalNum, goal)
            goalKey[goalNum] = goal
            goalNum += 1
        self.world.dialog(senderID, dialogStr)
        self.logger.info("Sent rebellion info to operator {}".format(senderID))

        if informOthers:
            # Inform other agents
            state = self.mem.get(self.mem.STATE)
            agents = state.agents
            self.logger.info("Got agents to inform")
            for agent in agents:
                self.world.dialog(agent.id, "I rebelled")
                if rebellion['reason'] == 'civi-in-AOE':
                    for civi in rebellion['civilians']:
                        self.world.inform(agent.id, civi.id)
                self.logger.info("Informed agent {} of rebellion".format(agent))

        return goalKey

    def gen_alt_goals(self, oldGoal, reason):
        """Create and return possible alternate goals to a rejected goal."""
        altGoals = []
        if reason == 'civi-in-AOE':
            for enemy in self.agent.filter_objects(objType="NPC", civi=False, alive=True):
                altGoal = goals.Goal(enemy.id, predicate='killed', user=oldGoal['user'])
                print("Generated single alt goal {} from enemy id {}".format(altGoal, enemy.id))
                if self.agent.valid_goal(altGoal)[0]:
                    altGoals.append(altGoal)
        altGoals.append(oldGoal)
        altGoals.append("None")

        return altGoals

    def remove_goal(self, goal):
        goalGraph = self.mem.get(self.mem.GOAL_GRAPH)
        goalGraph.remove(goal)
        if self.mem.trace:
            self.mem.trace.add_data("REJECTED GOAL", goal)

    def add_goal(self, goal):
        goalGraph = self.mem.get(self.mem.GOAL_GRAPH)
        goalGraph.add(goal)


class OperatorHandleRebelsStochastic(base.BaseModule):
    """
    Interact with agents which are rebelling by delivering a response.

    This module handles any rebellions the operator heard by choosing whether
    to assign a new goal suggested by the agent, reject the agent's rebellion,
    or allow the rebellion but not give the agent an alternative. If the module
    sees a rebellion, it chooses whether to reject the rebellion or accept alternative
    goals randomly, according to the probability given to hte module at instantiation.
    """

    def __init__(self, rejectionProb=0.0, logger=logging.getLogger("dummy")):
        """Instantiate the module, giving it a probability of rejecting a rebellion."""
        super(OperatorHandleRebelsStochastic, self).__init__()
        self.rejectionProb = rejectionProb
        self.logger = logger

    def init(self, world, mem):
        """Give the module criticial MIDCA information about state and memory."""
        self.mem = mem
        self.client = world

    def run(self, cycle, verbose=2):
        """
        Run the handle rebellion module.

        This function looks through MIDCA's memory to see if there are any
        pending rebellions, and handles them individually.
        """
        if self.mem.trace:
            self.mem.trace.add_module(cycle, self.__class__.__name__)

        self.logger.info("Retrieving rebellions")
        rebellions = self.mem.get("REBELLIONS")
        if verbose >= 1:
            print("Rebellions: {}".format(rebellions))
        self.mem.set("REBELLIONS", [])
        self.logger.info("Rebellions:\n{}".format(rebellions))
        if rebellions is None:
            return

        for rebellion in rebellions:
            self.handle_rebellion(rebellion, verbose)

    def handle_rebellion(self, rebellion, verbose=2):
        """
        Handle an individual rebellion from interpreting it to replying.

        This function extracts the core information from the rebellion, then
        decides on an appropriate response to the rebelling agent. For this
        module, the response is determined by whether the operator is willing
        to accept the rebellion or not, which is in turn decided randomly.
        Should the operator accept the rebellion, an alternative goal is chosen
        from those suggested by the agent, should it reject the rebellion, the
        operator will restore the goal to the agent.

        Arguments:

        ``rebellion``, *tuple*:
            A tuple containing for important pieces of rebellion information. The
            first is the rejected goal, the sceond is the reason for rejection,
            the third is miscellaneous information about the rebellion, and the
            fourth is the rebel agent.

        ``return``:, *None*
        """
        self.logger.info("Handling rebellion\n{}".format(rebellion))
        if verbose >= 1:
            print("Handling rebellion {}".format(str(rebellion)))

        rebGoal, rebReason, rebInfo, altGoals, rebAgt = rebellion
        rejection = random() < self.rejectionProb
        self.logger.info("Rejection: {}".format(rejection))

        if rejection:
            responseOption = altGoals.index(rebGoal)
            if verbose >= 1:
                print("Rejected rebellion, responseOption={}".format(responseOption))
            self.logger.info("Rejected rebellion, responseOption={}".format(responseOption))

        else:
            self.logger.info("Choosing alternate option")
            for altGoal in altGoals:
                if not wu.goals_equal(altGoal, rebGoal):
                    responseOption = altGoals.index(altGoal)
                    if verbose >= 1:
                        print("Found alt goal {}, responseOption={}".format(altGoal, responseOption))
                    self.logger.info("Found alt goal {}, responseOption={}".format(altGoal, responseOption))
                    break
            self.mark_as_invalid_goal(rebAgt, rebGoal, verbose)
            self.logger.info("Marked goal {} as invalid for {}".format(rebGoal, rebAgt))

        self.client.dialog(rebAgt, str(responseOption))
        if verbose >= 1:
            print("Sent response {} to {}".format(str(responseOption), rebAgt))
        self.logger.info("Sent response {} to {}".format(responseOption, rebAgt))

        if altGoals[responseOption] == "none":
            # We need to remove the agent from the active agents list
            activeAgents = self.mem.get("ACTIVE_AGENTS")
            for agt in activeAgents:
                if agt == rebAgt:
                    activeAgents.remove(agt)
            self.mem.set("ACTIVE_AGENTS", activeAgents)
            if verbose >= 1:
                print("Removed {} from active agents".format(rebAgt))
            self.logger.info("Removed {} from active agents".format(rebAgt))

    def mark_as_invalid_goal(self, agt, goal, verbose):
        """Mark a goal as invalid for the given agent."""
        if verbose >= 1:
            print("Marked rebellion goal {} as invalid for {}".format(goal, agt))
        self.mem.add("INVALID_GOALS", (agt, goal))
