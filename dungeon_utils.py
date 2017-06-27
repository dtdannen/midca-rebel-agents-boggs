from copy import deepcopy
from random import randint

CHEST = 'CHEST'
DOOR = 'DOOR'
WALL = 'WALL'
KEY = 'KEY'
OBJECT_LIST = [CHEST, DOOR, WALL, KEY]
OBJECT_ID_CODES = {CHEST: "C",
                   DOOR: "D",
                   WALL: "W",
                   KEY: "K"}


class DungeonObject(object):
    """
    Class for objects in the dungeon.

    Since all objects have the same attributes, we can just use one class.
    """

    def __init__(self, objType, location, unlocks=None):
        """
        Create object by setting attributes.

        The attributes an Dungeon Object has are:
        `objType`: The kind of dungeon object it is (e.g. 'CHEST')
        `location`: Where the object is as (x,y)
        `locked`: Whether the object is locked
        `passable`: Whether the object is passable (can be moved over)
        `unlocks`: If objType=='KEY', then this specifies what the key unlocks
        """
        self.objType = objType
        self.location = location
        self.id = "{}x{}y{}".format(OBJECT_ID_CODES[objType],
                                    location[0], location[1])

        if objType in [CHEST, DOOR]:
            self.locked = True
        else:
            self.locked = False

        if objType == KEY:
            self.passable = True
            self.unlocks = unlocks
        else:
            self.passable = False
            self.unlocks = None

    @property
    def ascii_rep(self):
        """
        Return the ascii represntation of the object.

        This is how the object will appear on the board display.
        """
        if self.objType == CHEST:
            return 'C' if self.locked else 'c'
        if self.objType == DOOR:
            return 'D' if self.locked else 'd'
        if self.objType == WALL: return 'XX'
        return 'k'

    def __str__(self):
        """Return a concise summary of the object's state."""
        retStr = "{}@{} (".format(self.objType, self.location)
        retStr = retStr + "L," if self.locked else retStr + "U,"
        retStr = retStr + "O" if self.passable else retStr + "C"
        retStr = retStr + ",{})".format(str(self.unlocks)) if self.unlocks else retStr + ")"
        return retStr


class Agent(object):
    """
    Represents the agent, and in particular its state and knowledge.

    Used for PyHop planning in conjunction with fog-of-war and limited knowledge
    scenarios.
    """
    # TODO: Create a Map class and move all the goal stuff to it, so we're not
    # checking globally whether a goal can be accomplished

    def __init__(self, name, location, dungeonDim, vision=-1):
        self.name = name
        self.at = location
        self.dim = dungeonDim
        self.vision = vision
        self.map = {}

    @property
    def known_objects(self):
        """Return a list of all dungeon objects."""
        objects = []
        for loc in self.floor:
            objects += self.floor[loc]
        return objects

    def view(self, dungeon):
        viewedObjs = dungeon.get_objects_around(self.at, self.vision)
        for tile in viewedObjs:
            self.map[tile] = viewedObjs[tile]

        return True

    def draw_map(self):
        ascii_board = "  "
        ascii_board += " |".join([str(c) for c in range(self.dim)])
        ascii_board += " |\n"
        for y in range(self.dim):
            ascii_board += str(y) + "|"
            for x in range(self.dim):
                ascii_board += self._draw_ascii_tile((x, y)) + "|"
            ascii_board += "\n"
        print(ascii_board)

    def _draw_ascii_tile(self, loc):
        """Draw a single tile of the board at the given location."""
        tileStr = ''
        # If the agent is there, draw it
        if loc == self.at:
            tileStr += '@'

        # If the tile has contents, draw them
        if loc in self.map.keys():
            for obj in self.map[loc]:
                tileStr += obj.ascii_rep

        # Pad the tile and return
        tileStr = tileStr.rjust(2, '.')
        return tileStr


class Dungeon(object):
    """
    Class representing an entire dungeon.

    Contains a dungeon map, the state of doors and chests, and changes the
    environment when needed.
    """

    def __init__(self, dim, agent_vision=-1):
        """
        Initialize a blank dungeon of size `dim`x`dim`.

        Creates a new Dungeon object which is completely empty. In the dungeon
        environment, any (x,y) pair which isn't occupied by something is
        considered floor and is passable. The objects which can fill a Dungeon
        are:
        Chests: Never passable, initially locked, may have a key in them.
        Doors: Passable when unlocked, initially locked
        Walls: Never passable
        Keys: Always passable, unlock one locked object
        Agent: The agent, can pick up keys, can unlock chests/doors

        The board is stored as a dictionary with (x,y) locations as keys and
        lists of objects as values, so that the value of a location is a list
        of the objects there. The agent is a special case, in that it moves, and
        so the current location of the agent is stored separately. The agent starts
        in the middle of the dungeon.
        """
        assert type(dim) is int, "dim must be an int"

        # Generate self variables
        self.dim = self.hgt = self.wdt = dim
        self.floor = {}
        self.agentLoc = (dim/2, dim/2)
        self.agent = Agent('Drizzt', self.agentLoc, dim, agent_vision)

    @property
    def objects(self):
        """Return a list of all dungeon objects."""
        objects = []
        for loc in self.floor:
            objects += self.floor[loc]
        return objects

    def place_object(self, objType, location):
        if not self.__loc_valid(dest):
            raise Exception("{} is not a valid place for {}".format(location, objType))
        if objType in [CHEST, DOOR, WALL]:
            if not self.loc_is_free(location):
                raise Exception("{} is already occupied by a large object".format(location))
        obj = DungeonObject(objType, location)
        if location in self.floor.keys():
            self.floor[location].append(obj)
        else:
            self.floor[location] = [obj]

    def remove_object_at(self, objType, loc):
        """Remove the object at the given location."""
        if not self.__loc_valid(dest):
            print("{} is not a valid location".format(loc))
            return False
        if loc not in self.floor.keys():
            print("There's no object at {}".format(loc))
            return False
        remove_index = -1
        for obj in self.floor[loc]:
            if obj.objType == objType:
                remove_index = self.floor[loc].index(obj)
        if remove_index == -1:
            print("There's no {} at {}".format(objType, loc))
            return False
        del self.floor[loc][remove_index]
        if len(self.floor[loc]) == 0:
            del self.floor[loc]
        return True

    def teleport_agent(self, dest):
        """Spontaneously move the agent to the dest, if possible."""
        if not self.__loc_valid(dest):
            print("{} is not a valid location".format(dest))
            return False
        if not self.check_passable(dest):
            print("Can't move the agent to {}".format(dest))
            return False
        self.agentLoc = dest
        self.agent.at = dest
        return True

    def unlock(self, target, key=None):
        """Unlock anything locked at the target location."""
        if not self.__loc_valid(target):
            print("{} is not a valid location".format(target))
            return False
        if self.check_passable(target):
            print("Nothing to unlock at {}".format(target))
            return False

        for obj in self.floor[target]:
            if obj.objType in [DOOR, CHEST]:
                if key:
                    obj.passable = key.unlocks == obj
                else:
                    obj.passable = True

    def get_objects_around(self, loc, vRange):
        """Return the objects and their properties around a location."""
        objects = {}
        if vRange == -1:
            return self.floor
        northBound = max(loc[1] - vRange, 0)
        southBound = min(loc[1] + vRange, self.dim)
        westBound = max(loc[0] - vRange, 0)
        eastBound = min(loc[0] + vRange, self.dim)

        for x in range(westBound, eastBound+1):
            for y in range(northBound, southBound+1):
                vLoc = (x, y)
                if vLoc in self.floor.keys():
                    objects[vLoc] = self.floor[vLoc]

        return objects

    def generate(self, chests, doors, walls):
        """
        Generate a random Dungeon.

        Fills the board with chests, doors, and walls, the amount of each
        dictated by `chests`, `doors`, and `walls`. The sum of those should be
        less than half the number of tiles, i.e.
            `chests` + `doors` + `walls` <= `self.dim`**2/2-1

        Note that not all tiles and keys are guaranteeded to be accessible, and
        so not all doors and chests can be reached or unlocked.
        """
        assert chests + doors + walls <= self.dim**2/2 - 1, "too many objects!"

        # Generate chests, walls, and doors
        locks = []
        objTypeIndex = 0
        for objCount in [chests, doors, walls]:
            objType = OBJECT_LIST[objTypeIndex]
            objsPlaced = 0
            while objsPlaced < objCount:
                objLoc = self.__random_loc()
                obj = DungeonObject(objType, objLoc)
                if self.check_passable(objLoc):
                    if objLoc in self.floor.keys():
                        self.floor[objLoc].append(obj)
                    else:
                        self.floor[objLoc] = [obj]
                    print("Placing {}".format(str(obj)))
                    objsPlaced += 1
                    if objType is not WALL:
                        locks.append(obj)
            objTypeIndex += 1

        # Generate and place keys
        keyLock = locks.pop()
        while len(locks) > -1:
            keyLoc = self.__random_loc()
            validLoc = True
            if keyLoc in self.floor.keys():
                for obj in self.floor[keyLoc]:
                    if obj.objType in [DOOR, WALL, KEY]:
                        validLoc = False
                if validLoc:
                    key = DungeonObject(KEY, keyLoc, keyLock)
                    self.floor[keyLoc].append(key)
                    print("Placing {}".format(str(key)))
                    print(len(locks))
                    try:
                        keyLock = locks.pop()
                    except IndexError:
                        break
            else:
                key = DungeonObject(KEY, keyLoc, keyLock)
                self.floor[keyLoc] = [key]
                print("Placing {}".format(str(key)))
                try:
                    keyLock = locks.pop()
                except IndexError:
                    break

    def check_passable(self, loc):
        """Determine whether `loc` has an impassable object in it."""
        if loc == self.agentLoc:
            return False

        if loc not in self.floor.keys():
            return True

        contents = self.floor[loc]
        for obj in contents:
            if not obj.passable:
                return False
        return True

    def loc_is_free(self, loc):
        """
        Indicate whether the location can have a large object.

        Checks whether the tile is already occupied by a large object (chest,
        wall, or door).
        """
        if loc not in self.floor.keys():
            return True

        for objType in [CHEST, DOOR, WALL]:
            if objType in [o.objType for o in self.floor[loc]]:
                return False

        return True

    def draw_ascii_tile(self, loc):
        """Draw a single tile of the board at the given location."""
        tileStr = ''
        # If the agent is there, draw it
        if loc == self.agentLoc:
            tileStr += '@'

        # If the tile has contents, draw them
        if loc in self.floor.keys():
            for obj in self.floor[loc]:
                tileStr += obj.ascii_rep

        # Pad the tile and return
        tileStr = tileStr.rjust(2, '.')
        return tileStr

    def valid_goal(self, goal):
        goalLoc = goal.args[0]
        goalAction = goal.kwargs['predicate']

        if goalAction == 'agent-at':
            return self.check_passable(goalLoc)

        if goalAction == 'open':
            if self.check_passable(goalLoc):
                return False
            return True

    def create_goal(self, predicate, *args):
        """
        Given a predicate and args, create a new Dungeon which fits the goal.

        This creates a new Dungeon object which is different from the current
        one such that the given predicate is true in relation to the args. This
        new Dungeon serves as a PyHop goal.
        """
        goalDungeon = deepcopy(self)
        if predicate == "agent-at":
            loc = args[0]
            goalDungeon.teleport_agent(loc)

        elif predicate == "open":
            loc = args[0]
            goalDungeon.unlock(loc)

        return goalDungeon

    def __random_loc(self):
        x = randint(0, self.dim-1)
        y = randint(0, self.dim-1)
        return (x, y)

    def __loc_valid(self, loc):
        x = loc[0]
        y = loc[1]
        if not 0 <= x < self.dim: return False
        if not 0 <= y < self.dim: return False
        return True

    def __str__(self):
        """
        Convert the Dungeon to a string representation.

        The Dungeon is returned as an ascii representation of the board state.
        This is merely a display, board state cannot be exactly recreated by
        this method. May implement a __rerpr__ later.
        """
        ascii_board = "  "
        ascii_board += " |".join([str(c) for c in range(self.dim)])
        ascii_board += " |\n"
        for y in range(self.dim):
            ascii_board += str(y) + "|"
            for x in range(self.dim):
                ascii_board += self.draw_ascii_tile((x, y)) + "|"
            ascii_board += "\n"
        return ascii_board

    def __eq__(self, other):
        """Check if two Dungeons are the same."""
        return str(self) == str(other)


def draw_Dungeon(dng):
    """Print the Dungeon board."""
    print(str(dng))


def test():
    """Function for easier testing."""
    dng = Dungeon(5)
    dng.generate(3, 3, 5)
    print(dng.MIDCA_state_str())
    print(str(dng))


if __name__ == '__main__':
    test()
