import copy
import os

from MIDCA import base


class Observer(base.BaseModule):
    """
    Copies the agent state to MIDCA memory, allowing for custom fog-of-war.

    DEPRECATED
    """

    def init(self, world, mem):
        self.mem = mem
        self.world = world

    def observe(self):
        """Tell the agent to look at its surroundings."""
        return self.world.agent.view(self.world)

    def run(self, cycle, verbose=2):
        self.observe()
        agentCopy = copy.deepcopy(self.world.agent)
        self.mem.add(self.mem.STATES, agentCopy)
        self.mem.set(self.mem.STATE, self.world.agent)
        states = self.mem.get(self.mem.STATES)
        if len(states) > 400:
            # print "trimmed off 200 old stale states"
            states = states[200:]
            self.mem.set(self.mem.STATES, states)
        # End Memory Usage Optimization

        if verbose >= 1:
            print "World observed."

        trace = self.mem.trace
        if trace:
            trace.add_module(cycle, self.__class__.__name__)
            trace.add_data("WORLD", agentCopy)
            trace.add_data("CURR WORLD", agentCopy)


class ShowMap(base.BaseModule):
    """Lets MIDCA show the agent's map of the world."""

    def init(self, world, mem):
        self.mem = mem
        self.world = world

    def run(self, cycle, verbose=2):
        if verbose < 1:
            os.system('clear')
        agent = self.mem.get(self.mem.STATE)
        agent.draw_map()
        print("Health: {}".format(agent.damage))


class RemoteObserver(base.BaseModule):
    """
    Copies the agent state to MIDCA memory, allowing for custom fog-of-war.

    Unlike the non-remote version, the world given to this module should be
    an instance of MIDCAClient, and is an intermediary. The observer does not
    have direct access to the world.
    """

    def init(self, world, mem):
        self.mem = mem
        self.client = world

    def observe(self):
        """Tell the agent to look at its surroundings."""
        return self.client.observe()

    def run(self, cycle, verbose=2):
        self.observe()
        currAgent = self.client.agent()
        agentCopy = copy.deepcopy(currAgent)
        self.mem.add(self.mem.STATES, agentCopy)
        self.mem.set(self.mem.STATE, currAgent)
        states = self.mem.get(self.mem.STATES)
        if len(states) > 400:
            # print "trimmed off 200 old stale states"
            states = states[200:]
            self.mem.set(self.mem.STATES, states)
        # End Memory Usage Optimization

        if verbose >= 1:
            print "World observed."

        trace = self.mem.trace
        if trace:
            trace.add_module(cycle, self.__class__.__name__)
            trace.add_data("WORLD", agentCopy)
            trace.add_data("CURR WORLD", agentCopy)


class OperatorObserver(base.BaseModule):
    """
    Observation and update module for an operator running automatically.

    This module updates MIDCA's memory with knowledge of the operator's current
    state and any new messages the operator received.

    The current operator instance is stored in "STATE", and a copy of the current
    operator is appended to "STATES".
    """

    def init(self, world, mem):
        """Give critical information to the module to initialize it."""
        self.mem = mem
        self.client = world

    def run(self, cycle, verbose=2):
        """Update world state information in MIDCA's memory."""
        self.client.observe()
        optr = self.client.operator()
        optrCopy = copy.deepcopy(optr)
        self.mem.add(self.mem.STATES, optrCopy)
        self.mem.set(self.mem.STATE, optr)

        msgs = self.client.get_dialogs()
        self.mem.set("MESSAGES", msgs)

        states = self.mem.get(self.mem.STATES)
        if len(states) > 400:
            states = states[200:]
            self.mem.set(self.mem.STATES, states)

        if verbose >= 1:
            print "World observed."

        trace = self.mem.trace
        if trace:
            trace.add_module(cycle, self.__class__.__name__)
            trace.add_data("WORLD", optrCopy)
            trace.add_data("MESSAGES", msgs)
