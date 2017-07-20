import copy, os

from MIDCA import base


class Observer(base.BaseModule):
    """Copies the agent state to MIDCA memory, allowing for custom fog-of-war."""

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


class ShowMap(base.BaseModule):
    """Lets MIDCA show the agent's map of the world."""

    def init(self, world, mem):
        self.mem = mem
        self.client = world

    def run(self, cycle, verbose=2):
        agent = self.mem.get(self.mem.STATE)
        agent.draw_map()
        print("Health: {}".format(agent.damage))
