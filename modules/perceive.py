"""
Contains modules used during the perceive phase of the MIDCA cycle.

The perceive phase is the first phase executed in a MIDCA cycle. It enables the
agent to take in an updated view of the world for its future deliberations. Thus,
its role is fairly limited, being used only to gather the latest raw data from
the world. Within this module are the perceive modules for both agent and
operator MIDCA cycles.
"""

import copy
import os
import logging

from MIDCA import base


class Observer(base.BaseModule):
    """
    Copies the agent state to MIDCA memory, allowing for custom fog-of-war.

    DEPRECATED
    """

    def init(self, world, mem):
        """Give module access to critical MIDCA information."""
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
    """Displays the MIDCA agent's perception of the world map."""

    def __init__(self, logger=logging.getLogger("dummy")):
        """Instantiate a ``ShowMap`` module; with a logger if desired."""
        super(ShowMap, self).__init__()
        self.logger = logger

    def init(self, world, mem):
        self.mem = mem
        self.world = world

    def run(self, cycle, verbose=2):
        if verbose < 1:
            os.system('clear')
        agent = self.mem.get(self.mem.STATE)
        agent.draw_map()
        self.logger.info("\n" + str(agent.map))


class RemoteObserver(base.BaseModule):
    """
    Copies the agent state to MIDCA memory, allowing for custom fog-of-war.

    Unlike the non-remote version, the world given to this module should be
    an instance of MIDCAClient, and is an intermediary. The observer does not
    have direct access to the world.
    """

    def __init__(self, logger=logging.getLogger("dummy")):
        """Instantiate a ``RemoteObserver`` module; with a logger if desired."""
        super(RemoteObserver, self).__init__()
        self.logger = logger

    def init(self, world, mem):
        """Give module access to critical MIDCA information."""
        self.mem = mem
        self.client = world

    def observe(self):
        """Tell the agent to look at its surroundings."""
        return self.client.observe()
        self.logger.info("Observed world")

    def run(self, cycle, verbose=2):
        """Agent gets updated map info and messages."""
        self.logger.info("Started cycle {}".format(cycle))

        self.observe()
        currAgent = self.client.agent()
        agentCopy = copy.deepcopy(currAgent)
        self.mem.add(self.mem.STATES, agentCopy)
        self.mem.set(self.mem.STATE, currAgent)
        self.logger.info("Recorded current state")

        states = self.mem.get(self.mem.STATES)
        if len(states) > 400:
            # print "trimmed off 200 old stale states"
            states = states[200:]
            self.mem.set(self.mem.STATES, states)
            self.logger.info("Trimmed 200 old states")
        # End Memory Usage Optimization

        msgs = self.client.get_dialogs()
        if msgs is None:
            msgs = []
        self.logger.info("Got messages:")

        if verbose >= 1:
            print("Messages:")
        for msg in msgs:
            msgLogStr = "\t{}:\n\t{}".format(msg[1], msg[0])
            if verbose >= 1:
                print(msgLogStr)
            self.logger.info(msgLogStr)

        self.mem.set("MESSAGES", msgs)
        self.logger.info("Remembered messages")

        if verbose >= 1:
            print "World observed."

        trace = self.mem.trace
        if trace:
            trace.add_module(cycle, self.__class__.__name__)
            trace.add_data("WORLD", agentCopy)
            trace.add_data("MESSAGES", msgs)


class OperatorObserver(base.BaseModule):
    """
    Observation and update module for an operator running automatically.

    This module updates MIDCA's memory with knowledge of the operator's current
    state and any new messages the operator received.

    The current operator instance is stored in "STATE", and a copy of the current
    operator is appended to "STATES".
    """

    def __init__(self, logger=logging.getLogger("dummy")):
        """Instantiate an ``OperatorObserver`` module; with a logger if desired."""
        super(OperatorObserver, self).__init__()
        self.logger = logger

    def init(self, world, mem):
        """Give critical information to the module to initialize it."""
        self.mem = mem
        self.client = world

    def run(self, cycle, verbose=2):
        """Update world state information in MIDCA's memory."""
        self.logger.info("Started cycle {}".format(cycle))

        self.client.observe()
        optr = self.client.operator()
        optrCopy = copy.deepcopy(optr)
        self.mem.add(self.mem.STATES, optrCopy)
        self.mem.set(self.mem.STATE, optr)
        self.logger.info("Recorded current state")

        msgs = self.client.get_dialogs()
        if msgs is None:
            msgs = []
        self.logger.info("Got messages:")

        if verbose >= 1:
            print("Messages:")
        for msg in msgs:
            msgLogStr = "\t{}:\n\t{}".format(msg[1], msg[0])
            if verbose >= 1:
                print(msgLogStr)
            self.logger.info(msgLogStr)

        self.mem.set("MESSAGES", msgs)
        self.logger.info("Remembered messages")

        states = self.mem.get(self.mem.STATES)
        if len(states) > 400:
            states = states[200:]
            self.mem.set(self.mem.STATES, states)
            self.logger.debug("Trimmed 200 old states")

        if verbose >= 1:
            print "World observed."

        trace = self.mem.trace
        if trace:
            trace.add_module(cycle, self.__class__.__name__)
            trace.add_data("WORLD", optrCopy)
            trace.add_data("MESSAGES", msgs)
