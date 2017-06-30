"""Collection of dungeon-specific simulator modules for MIDCA."""

from MIDCA import base


class SimulateActions(base.BaseModule):
    """Apply the actions given to the Dungeon."""

    def init(self, world, mem):
        """Initialize the MIDCA module by giving it access to world and memory."""
        self.mem = mem
        self.world = world

    def execute_action(self, action):
        """Try to apply the action to the world."""
        if not self.world.apply_action(action):
            raise Exception("For some reason, action {} did not succeed".format(action))

    def run(self, cycle, verbose=0):
        """
        Run the module in MIDCA's cycle.

        Gets the current actions queued up, if there are any, and then tries to
        execute them in the world.
        """
        self.verbose = verbose
        if self.mem.trace:
            self.mem.trace.add_module(self.__class__.__name__)
        if self.mem.get(self.mem.ACTIONS):
            actions = self.mem.get(self.mem.ACTIONS)[-1]
            if actions == []:
                if verbose >= 2:
                    print("No actions to take, continuing")
                    return
            for action in actions:
                self.execute_action(action)
                if self.mem.trace:
                    self.mem.trace.add_data("ACTION", action)


class WorldChanger(base.BaseModule):
    """Allows the user to change the world state."""

    def init(self, world, mem):
        """Initialize the MIDCA module by giving it access to world and memory."""
        self.mem = mem
        self.world = world

    def parse_response(self, response):
        """
        Transform the given response string into a digestible list.

        The list contains the action type (e.g. 'move-to'), the location
        given, and the kind of object, if there is one. In the future this may
        need to be more robust to allow for different kinds of changes.
        """
        respData = response.split()
        action, locStr = respData[:2]
        objType = None
        if len(respData) == 3:
            objType = respData[2].upper()

        loc = locStr.strip("()").split(',')
        loc = (int(loc[0]), int(loc[1]))

        return [action, loc, objType] if objType else [action, loc]

    def make_change(self, change):
        """
        Apply the change to the world.

        Currently the user can add or remove objects at a location or teleport
        the agent.
        """
        action = change[0]
        loc = change[1]
        if len(change) == 3:
            objType = change[2]

        if action == 'add':
            self.world.place_object(objType, loc)
        elif action == 'rem':
            self.world.remove_object_at(objType, loc)
        elif action == 'tele':
            self.world.teleport_agent(loc)
        else:
            return False
        return True

    def run(self, cycle, verbose=0):
        """Ask user for any changes and apply them if possible."""

        while True:
#             if verbose >= 2:
#                 print("""Change commands:
# `add loc objType` to add an object
# `rem loc objType` to remove an object
# `tele loc` to move the agent to the location
# q to quit MIDCA
# RETURN to continue with the MIDCA cycle
# >> """)
            response = raw_input("What would you like to change?  ")
            if response == '':
                return 'continue'
            elif response == 'q':
                return 'q'
            else:
                try:
                    command = self.parse_response(response)
                except Exception:
                    print("{} is not a valid command".format(response))
                    continue
            if not self.make_change(command):
                print("{} is not a valid command".format(response))
                continue


class ASCIIWorldViewer(base.BaseModule):
    """Displays the Dungeon as an ASCII board."""

    def init(self, world, mem):
        self.mem = mem
        self.world = world

    def run(self, cycle, verbose=0):
        print(str(self.world))
