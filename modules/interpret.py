from MIDCA import base, goals


class UserGoalInput(base.BaseModule):
    """Allows MIDCA to create a goal based on user input."""

    def init(self, world, mem):
        self.mem = mem
        self.world = world

    def run(self, cycle, verbose=2):
        while True:
            userInput = raw_input("""Enter a goal or hit RETURN to continue.
Possible goals are moving to a location or opening a door/chest.
Format:
    agent-at x y : Moves the agent to (x, y)
    open x y : Opens the door or chest at (x, y)
>> """)
            goal = self.parse_input(userInput)
            if goal == 'q':
                return goal
            elif goal == '':
                return 'continue'

            if goal and self.world.valid_goal(goal):
                self.mem.get(self.mem.GOAL_GRAPH).insert(goal)

    def parse_input(self, userIn):
        """Turn user input into a goal."""
        if userIn == 'q' or userIn == '':
            return userIn
        goalData = userIn.split()
        if len(goalData) != 3:
            print("Invalid goal. There should only be three parts")
            return False

        if goalData[0] not in ['agent-at', 'open']:
            print("{} is not a valid goal".format(goalData[0]))
        goalAction = goalData[0]

        try:
            x = int(goalData[1])
            y = int(goalData[2])
        except ValueError:
            print("x and y must be integers")
            return False
        goalLoc = (x, y)

        goalDungeon = self.world.create_goal(goalAction, goalLoc)
        goal = goals.Goal(goalLoc, predicate=goalAction, state=goalDungeon)

        return goal
