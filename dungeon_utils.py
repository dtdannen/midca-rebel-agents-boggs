"""Contains the Dungeon class and related classes."""

from copy import deepcopy
from random import randint
import os

CHEST = 'CHEST'
DOOR = 'DOOR'
WALL = 'WALL'
KEY = 'KEY'
COIN = 'COIN'
FIRE = 'FIRE'
TRAP = 'TRAP'
OBJECT_LIST = [CHEST, DOOR, WALL, KEY, COIN, FIRE, TRAP]
OBJECT_ID_CODES = {"C": CHEST,
                   "D": DOOR,
                   "W": WALL,
                   "K": KEY,
                   "$": COIN,
                   "*": FIRE,
                   "^": TRAP}


class DungeonObject(object):
    """
    Superclass for objects and obstacles in the dungeon.

    All objects share several traits, which are handled by this superclass. They
    also all have ascii_rep methods, magic string methods, and equality methods
    which must override the superclass'.
    """

    def __init__(self, location):
        """
        Create object by setting attributes.

        The attributes an Dungeon Object has are:
        `objType`: The kind of dungeon object it is (e.g. 'CHEST')
        `location`: Where the object is as (x,y)
        `passable`: Whether the object is passable (can be moved over)
        """
        self.objType = None
        self.passable = None
        self.location = location

    @property
    def ascii_rep(self):
        """
        Return the ascii represntation of the object.

        This is how the object will appear on the board display.
        """
        raise NotImplementedError

    def __str__(self):
        raise NotImplementedError

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        return repr(self) == repr(other)


class Wall(DungeonObject):
    """Represents a wall in the dungeon."""

    def __init__(self, location):
        super(Wall, self).__init__(location)
        self.passable = False
        self.objType = WALL

    @property
    def ascii_rep(self):
        return "XX"

    def __str__(self):
        return "Wall @ {}".format(self.location)

    def __repr__(self):
        return "W@{}".format(self.location)


class Chest(DungeonObject):
    """Represents a chest in the dungeon, and can hold things."""

    def __init__(self, location, contains=None):
        super(Chest, self).__init__(location)
        self.passable = False
        self.objType = CHEST
        self.contains = contains
        self.locked = True

    def insert_object(self, obj):
        self.contain = obj

    @property
    def ascii_rep(self):
        if self.locked:
            return 'CC'
        elif self.contains:
            return 'c' + self.contains.ascii_rep
        else:
            return 'cc'

    def __str__(self):
        locked = "Locked" if self.locked else "Unlocked"
        return "{} chest @ {} containing {}".format(locked, self.location,
                                                    str(self.contains))

    def __repr__(self):
        char = "C" if self.locked else "c"
        return "{}@{}:{}".format(char, self.location, repr(self.contains))


class Door(DungeonObject):
    """Represents a door in the dungeon, which can be unlocked and opened."""

    def __init__(self, location, locked=True):
        super(Door, self).__init__(location)
        self.passable = False
        self.objType = DOOR
        self.locked = locked

    @property
    def ascii_rep(self):
        if self.locked:
            return 'DD'
        else:
            return 'd'

    def __str__(self):
        locked = "Locked" if self.locked else "Unlocked"
        return "{} door @ {}".format(locked, self.location)

    def __repr__(self):
        char = "D" if self.locked else "d"
        return "{}@{}".format(char, self.location)


class Key(DungeonObject):
    """Represents a key in the dungeon. Can unlock a locked item."""

    def __init__(self, location, unlocks):
        super(Key, self).__init__(location)
        self.passable = True
        self.objType = KEY
        self.unlocks = unlocks
        self.taken = False

    @property
    def ascii_rep(self):
        return 'k'

    def __str__(self):
        if self.taken:
            return "Owned key which unlocks {}".format(repr(self.unlocks))
        else:
            return "Key at {} which unlocks {}".format(self.location, repr(self.unlocks))

    def __repr__(self):
        if self.taken:
            return "k@tkn:{}".format(repr(self.unlocks))
        else:
            return "k@{}:{}".format(self.location, repr(self.unlocks))


class Coin(DungeonObject):
    """Represents a coin of some value in the dungeon."""

    def __init__(self, location, value):
        super(Coin, self).__init__(location)
        self.passable = True
        self.objType = COIN
        self.value = value

    @property
    def ascii_rep(self):
        return "$"

    def __str__(self):
        return "Coin @ {} worth {}".format(self.location, self.value)

    def __repr__(self):
        return "$@{}:{}".format(self.location, self.value)


class Fire(DungeonObject):
    """Represents a fire in the dungeon, which can deal damage to the agent."""

    def __init__(self, location, damage):
        super(Fire, self).__init__(location)
        self.passable = True
        self.objType = FIRE
        self.damage = damage

    @property
    def ascii_rep(self):
        return "**"

    def __str__(self):
        return "Fire @ {} which deals {} damage".format(self.location, self.damage)

    def __repr__(self):
        return "*@{}:{}".format(self.location, self.damage)


class Trap(DungeonObject):
    """Represents a trap in the dungeon, which is hidden until it activates."""

    def __init__(self, location, damage):
        super(Trap, self).__init__(location)
        self.passable = True
        self.objType = TRAP
        self.damage = damage
        self.hidden = True

    @property
    def ascii_rep(self):
        return "" if self.hidden else "^^"

    def __str__(self):
        hidden = "Hidden" if self.hidden else "Sprung"
        return "{} trap @ {} which deals {} damage".format(hidden, self.location,
                                                           self.damage)

    def __repr__(self):
        char = "h" if self.hidden else "s"
        return "^{}@{}:{}".format(char, self.location, self.damage)


class Dungeon(object):
    """
    Class representing an entire dungeon.

    Contains a dungeon map, the state of doors and chests, and changes the
    environment when needed.
    """

    def __init__(self, dim, agent_vision=-1, agentLoc=None):
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
        if agentLoc:
            self.agentLoc = agentLoc
        else:
            self.agentLoc = (dim/2, dim/2)
        self.agent = Agent('Drizzt', self.agentLoc, dim, agent_vision)

    @property
    def all_locations(self):
        """Return a list of all in-bounds locations."""
        tiles = []
        for x in range(self.dim):
            for y in range(self.dim):
                tiles.append((x, y))

        return tiles

    @property
    def objects(self):
        """Return a list of all dungeon objects."""
        objects = []
        for loc in self.floor:
            objects += self.floor[loc]
        return objects

    def place_object(self, objType, location, **kwargs):
        """Place a new object of the given type at the location, if possible."""
        if not self.loc_valid(location):
            raise Exception("{} is not a valid place for {}".format(location, objType))

        if objType in [CHEST, DOOR, WALL, TRAP, FIRE]:
            if not self.loc_is_free(location):
                raise Exception("{} is already occupied by a large object".format(location))

        if objType == WALL:
            obj = Wall(location)
        elif objType == CHEST:
            contains = kwargs['contains']
            obj = Chest(location, contains)
        elif objType == DOOR:
            obj = Door(location)
        elif objType == KEY:
            unlocks = kwargs['unlocks']
            obj = Key(location, unlocks)
        elif objType == COIN:
            value = kwargs['value']
            obj = Coin(location, value)
        elif objType == FIRE:
            damage = kwargs['damage']
            obj = Fire(location, damage)
        elif objType == TRAP:
            damage = kwargs['damage']
            obj = Trap(location, damage)
        else:
            raise NotImplementedError(objType)

        if location in self.floor:
            self.floor[location].append(obj)
        else:
            self.floor[location] = [obj]
        return obj

    def remove_object_at(self, objType, loc):
        """Remove the object at the given location."""
        if not self.loc_valid(loc):
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
        if not self.loc_valid(dest):
            print("{} is not a valid location".format(dest))
            return False
        if not self.check_passable(dest):
            print("Can't move the agent to {}".format(dest))
            return False
        self.agentLoc = dest
        self.agent.at = dest
        return True

    def move_agent(self, moveDir):
        """Legally move the agent in the given direction."""
        if moveDir == 'n':
            dest = (self.agentLoc[0], self.agentLoc[1]-1)
        elif moveDir == 'e':
            dest = (self.agentLoc[0]+1, self.agentLoc[1])
        elif moveDir == 's':
            dest = (self.agentLoc[0], self.agentLoc[1]+1)
        elif moveDir == 'w':
            dest = (self.agentLoc[0]-1, self.agentLoc[1])
        else:
            raise ValueError("{} is not a valid movement direction".format(moveDir))

        if not self.loc_valid(dest) or not self.check_passable(dest):
            return False

        self.agentLoc = dest
        self.agent.move(moveDir)
        return True

    def agent_take_key(self, keyLoc):
        """If possible, have the agent actually take a key."""
        if not self.loc_valid(keyLoc):
            raise ValueError("{} is not a valid location".format(keyLoc))
        if keyLoc not in self.floor.keys():
            print("Key location {} not in floor.keys()".format(keyLoc))
            return False
        if not (self.adjacent(self.agentLoc, keyLoc) or self.agentLoc == keyLoc):
            print("Agent at {} not adjacent or on key location {}".format(self.agentLoc, self.keyLoc))
            return False

        key = self.get_item_at(keyLoc, KEY)
        if key:
            self.remove_object_at(KEY, keyLoc)
            key.taken = True
            key.location = None
            self.agent.take_key(keyLoc)
            return True
        print("There's no key at {}".format(keyLoc))
        return False

    def agent_take_coin(self, coinLoc):
        """If possible, have the agent actually take a coin."""
        if not self.loc_valid(coinLoc):
            raise ValueError("{} is not a valid location".format(coinLoc))
        if coinLoc not in self.floor.keys():
            print("Coin location {} not in floor.keys()".format(coinLoc))
            return False
        if not (self.adjacent(self.agentLoc, coinLoc) or self.agentLoc == coinLoc):
            print("Agent at {} not adjacent or on coin at location {}".format(self.agentLoc, self.coinLoc))
            return False

        coin = self.get_item_at(coinLoc, COIN)
        if coin:
            self.remove_object_at(COIN, coinLoc)
            self.agent.take_coin(coinLoc)
            return True
        print("There's no coin at {}".format(coinLoc))
        return False

    def agent_unlock(self, target):
        """
        Unlock a door or chest at `target`.

        If there is a door at `target`, the door becomes unlocked and passable,
        if there is a chest, it becomes unlocked.
        """
        if not self.loc_valid(target):
            raise ValueError("{} is not a valid location".format(target))
        if target not in self.floor.keys():
            print("Unlock target location {} not in floor.keys()".format(target))
            return False
        if not self.adjacent(self.agentLoc, target):
            print("Agent at {} not adjacent to target location {}".format(self.agentLoc, self.keyLoc))
            return False

        for obj in self.floor[target]:
            if obj.locked and self.agent.can_unlock(obj):
                obj.locked = False
                if obj.objType == DOOR:
                    obj.passable = True
                self.agent.unlock(target)
                return True
        print("There's no locked object at {}".format(target))
        return False

    def unlock(self, target, key=None):
        """Unlock anything locked at the target location."""
        if not self.loc_valid(target):
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
                    objects[vLoc] = deepcopy(self.floor[vLoc])

        return objects

    def get_item_at(self, loc, objType):
        """Return the item of `objType` at `loc`, if there is one."""
        if not self.loc_valid(loc):
            raise ValueError("{} is not a valid location".format(loc))
        if loc not in self.floor.keys():
            return False
        for obj in self.floor[loc]:
            if obj.objType == objType:
                return obj
        return None

    def check_passable(self, loc, doorsOpen=False):
        """Determine whether `loc` has an impassable object in it."""
        if loc == self.agentLoc:
            return False

        if loc not in self.floor.keys():
            return True

        contents = self.floor[loc]
        for obj in contents:
            if not obj.passable:
                if obj.objType == DOOR and doorsOpen:
                    return True
                return False
        return True

    def loc_is_free(self, loc):
        """
        Indicate whether the location can hold non-trivial object.

        Trivial objects as yet are coins and keys
        """
        if loc not in self.floor.keys():
            return True

        for obj in self.floor[loc]:
            if obj.objType not in [KEY, COIN]:
                return False

        return True

    def loc_unlocked(self, loc):
        """Indicate whether there is an unlocked object at the given location."""
        if not self.loc_valid(loc):
            raise Exception("{} is not a valid location".format(loc))
        if loc not in self.floor.keys():
            return True
        unlocked = True
        for obj in self.floor[loc]:
            if obj.locked:
                unlocked = False
        return unlocked

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
        """Indicate whether a goal is valid."""
        # TODO: make this much more robust!
        # In particular, make sure the 'open' goal is checked more thoroughly.
        goalLoc = goal.args[0]
        goalAction = goal.kwargs['predicate']

        if goalAction == 'move-to' and not self.check_passable(goalLoc):
            raise Exception("Invalid goal: agent can't be at {}".format(goalLoc))

        if goalAction == 'open'and self.check_passable(goalLoc):
            raise Exception("Invalid goal: nothing to open at {}".format(goalLoc))
        return True

    def create_goal(self, predicate, *args):
        """
        Given a predicate and args, create a new Dungeon which fits the goal.

        This creates a new Dungeon object which is different from the current
        one such that the given predicate is true in relation to the args. This
        new Dungeon serves as a PyHop goal.
        """
        goalDungeon = deepcopy(self)
        if predicate == "move-to":
            loc = args[0]
            goalDungeon.teleport_agent(loc)

        elif predicate == "open":
            loc = args[0]
            goalDungeon.unlock(loc)

        return goalDungeon

    def apply_action(self, action):
        """Apply a PyHop generated action to the Dungeon."""
        actType = action.op
        args = action.args

        if actType == 'move':
            moveDir = args[0]
            succeeded = self.move_agent(moveDir)

        elif actType == 'takekey':
            keyLoc = args[0]
            succeeded = self.agent_take_key(keyLoc)

        elif actType == 'unlock':
            target = args[0]
            succeeded = self.agent_unlock(target)

        if succeeded:
            return True
        else:
            raise NotImplementedError("Action type {} is not implemented".format(actType))

    def adjacent(self, loc1, loc2):
        """Indicate whether loc1 and loc2 are adjacent."""
        return abs(loc1[0]-loc2[0]) == 1 or abs(loc1[1]-loc2[1]) == 1

    def get_adjacent(self, loc):
        """Return the 2-4 tiles adjacent to the given one and their direction."""
        adjacentTiles = {}
        nNbor = (loc[0], loc[1]-1)
        sNbor = (loc[0], loc[1]+1)
        eNbor = (loc[0]+1, loc[1])
        wNbor = (loc[0]-1, loc[1])
        if self.loc_valid(nNbor):
            adjacentTiles['n'] = nNbor
        if self.loc_valid(sNbor):
            adjacentTiles['s'] = sNbor
        if self.loc_valid(eNbor):
            adjacentTiles['e'] = eNbor
        if self.loc_valid(wNbor):
            adjacentTiles['w'] = wNbor

        return adjacentTiles

    def get_path_to(self, origin, dest):
        """
        Return list of tiles along the linear path between origin and dest.

        Important to note that the list is linear, disregards obstacles, and
        always chooses to go east or west over north or south in a tie.
        """
        if not (self.loc_valid(origin) and self.loc_valid(dest)):
            raise ValueError("Origin {} or dest {} is not valid".format(origin, dest))

        path = []
        while origin != dest:
            orgX, orgY = origin
            destX, destY = dest
            horizDiff = orgX - destX
            vertDiff = orgY - destY

            if abs(horizDiff) >= abs(vertDiff):
                if orgX > destX:
                    nextOrigin = (origin[0] - 1, origin[1])
                else:
                    nextOrigin = (origin[0] + 1, origin[1])
            else:
                if orgY > destY:
                    nextOrigin = (origin[0], origin[1] - 1)
                else:
                    nextOrigin = (origin[0], origin[1] + 1)
            path.append(nextOrigin)
            origin = nextOrigin

        return path

    def obstacles_in(self, path, doorsOpen=False):
        """Calculate and return number of obstacles in a given path."""
        obstacles = 0
        for tile in path:
            if not self.check_passable(tile, doorsOpen):
                obstacles += 1
        return obstacles

    def diff(self, other):
        """Return a dict of tiles which have changed."""
        if self == other:
            return None

        diffs = {}

        for tile in self.all_locations:
            if tile in self.floor.keys():
                if tile in other.floor.keys():
                    if self.floor[tile] != other.floor[tile]:
                        diffs[tile] = (self.floor[tile], other.floor[tile])
                else:
                    diffs[tile] = (self.floor[tile], None)
            else:
                if tile in other.floor.keys():
                    diffs[tile] = (None, other.floor[tile])

        return diffs

    def draw_view(self, center, vRange):
        """Return a string which shows a limited view of the board."""
        ascii_board = "  "
        ascii_board += " |".join([str(c) for c in range(self.dim)])
        ascii_board += " |\n"

        northBound = max(center[1] - vRange, 0)
        southBound = min(center[1] + vRange, self.dim)
        westBound = max(center[0] - vRange, 0)
        eastBound = min(center[0] + vRange, self.dim)

        for y in range(self.dim):
            ascii_board += str(y) + "|"
            for x in range(self.dim):
                if (northBound <= y <= southBound) and (westBound <= x <= eastBound):
                    ascii_board += self.draw_ascii_tile((x, y)) + "|"
                else:
                    ascii_board += "..|"
            ascii_board += "\n"
        return ascii_board

    def loc_valid(self, loc):
        x = loc[0]
        y = loc[1]
        if not 0 <= x < self.dim: return False
        if not 0 <= y < self.dim: return False
        return True

    def __random_loc(self):
        x = randint(0, self.dim-1)
        y = randint(0, self.dim-1)
        return (x, y)

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

    def __repr__(self):
        """Return a string which allows for reconstructing the Dungeon."""
        retStr = "dim:{}\n".format(self.dim)
        retStr += "aLoc:{}\n".format(self.agentLoc)
        retStr += "aVis:{}\n".format(self.agent_vision)
        for obj in self.objects:
            retStr += repr(obj) + '\n'


class DungeonMap(Dungeon):
    """
    Represents and allows manipulation of the Agent's knowledge of the Dungeon.

    Has many of the features of its parent class Dungeon, but is limited to what
    the Agent knows. It also doesn't have its own Agent to prevent recursion.
    """

    def __init__(self, dim, agentLoc):
        assert type(dim) is int, "dim must be an int"

        # Generate self variables
        self.dim = self.hgt = self.wdt = dim
        self.floor = {}
        self.agentLoc = agentLoc

    def teleport_agent(self, dest):
        """Override a method the map shouldn't do."""
        raise NotImplementedError("A DungeonMap can't teleport the agent!")

    def generate(self, chests, doors, walls):
        """Override a method the map shouldn't do."""
        raise NotImplementedError("A DungeonMap can't generate itself!")

    def update_map(self, view, center, vRange):
        """Update the map based on what the Agent sees."""
        northBound = max(center[1] - vRange, 0)
        southBound = min(center[1] + vRange, self.dim)
        westBound = max(center[0] - vRange, 0)
        eastBound = min(center[0] + vRange, self.dim)

        for x in range(westBound, eastBound+1):
            for y in range(northBound, southBound+1):
                vLoc = (x, y)
                if vLoc in view.keys():
                    self.floor[vLoc] = view[vLoc]
                else:
                    if vLoc in self.floor.keys():
                        del self.floor[vLoc]

    def navigate_to(self, origin, dest, doorsOpen=False):
        """
        Return a list of tiles which forms a path.

        The returned path should be a sequence of locations such that each
        location is adjacent to the last and is passable, the first location is
        adjacent to the origin, and the last location is the destination. Uses
        A* search. If doorsBlock is False, then doors are not treated as
        obstacles.
        """
        explored = []
        activeTiles = [('o', origin, 0)]  # priority queue of tiles to explore

        while len(activeTiles) > 0:
            currNode = activeTiles.pop(0)
            currPath = currNode[0]
            currTile = currNode[1]

            if currTile == dest:
                return currPath

            nbors = self.get_adjacent(currTile)
            for nborDir in nbors:
                nbor = nbors[nborDir]
                if not self.check_passable(nbor, doorsOpen):
                    continue
                linPath = self.get_path_to(nbor, dest)
                obstacles = self.obstacles_in(linPath, doorsOpen)
                weight = len(linPath) + 2 * obstacles
                newNode = (currPath+nborDir, nbor, weight)

                exploredYet = False
                for node in explored:
                    if nbor == node[1]:
                        exploredYet = True
                        break
                if not exploredYet:
                    insertIndex = 0
                    for tile in activeTiles:
                        if tile[2] < weight:
                            insertIndex += 1
                        else:
                            break
                    activeTiles.insert(insertIndex, newNode)

            explored.append(currNode)
        return None

    def valid_goal(self, goal):
        """Indicate whether a goal is valid."""
        # TODO: make this much more robust!
        goalAction = goal.kwargs['predicate']

        if goalAction == 'move-to':
            goalLoc = goal.args[0]
            if not self.check_passable(goalLoc):
                return (False, 'unpassable')
            if not self.navigate_to(self.agentLoc, goalLoc):
                return (False, 'no-access')

        if goalAction == 'open':
            goalLoc = goal.args[0]
            if self.check_passable(goalLoc):
                return (False, 'no-object')
        return (True, 'none')


class Agent(object):
    """
    Represents the agent, and in particular its state and knowledge.

    Used for PyHop planning in conjunction with fog-of-war and limited knowledge
    scenarios.
    """

    def __init__(self, name, location, dungeonDim, vision=-1):
        self.__name__ = name
        self.at = location
        self.vision = vision
        self.map = DungeonMap(dungeonDim, location)
        self.keys = []
        self.coins = 0
        self.health = 10

    @property
    def known_objects(self):
        """Return a list of all dungeon objects."""
        return self.map.objects

    def view(self, dungeon):
        viewedObjs = dungeon.get_objects_around(self.at, self.vision)
        self.map.update_map(viewedObjs, self.at, self.vision)

    def navigate_to(self, dest, doorsOpen=False):
        """Convenient wrapper for navigating."""
        return self.map.navigate_to(self.at, dest, doorsOpen)

    def can_move(self, moveDir):
        """Indicate whether the Agent can move a tile in the given direction."""
        if moveDir == 'n':
            dest = (self.at[0], self.at[1]-1)
        elif moveDir == 'e':
            dest = (self.at[0]+1, self.at[1])
        elif moveDir == 's':
            dest = (self.at[0], self.at[1]+1)
        elif moveDir == 'w':
            dest = (self.at[0]-1, self.at[1])
        else:
            raise ValueError("{} is not a valid movement direction".format(moveDir))

        if not self.map.loc_valid(dest) or not self.map.check_passable(dest):
            return False
        return True

    def move(self, moveDir):
        """
        Move the agent 1 tile in `moveDir` direction, if possible.

        Note that this only affects the Agent and its map, this DOES NOT move
        the Agent in the actual Dungeon.
        """
        if moveDir == 'n':
            dest = (self.at[0], self.at[1]-1)
        elif moveDir == 'e':
            dest = (self.at[0]+1, self.at[1])
        elif moveDir == 's':
            dest = (self.at[0], self.at[1]+1)
        elif moveDir == 'w':
            dest = (self.at[0]-1, self.at[1])
        else:
            raise ValueError("{} is not a valid movement direction".format(moveDir))

        if self.can_move(moveDir):
            self.at = dest
            self.map.agentLoc = dest
            return True
        else:
            print("Can't move {} to {}. Agent at {}".format(moveDir, dest, self.at))
            return False

    def take_key(self, keyLoc):
        """
        Take possession of a key at `keyLoc`.

        Takes a key off the floor and keeps it. This removes it from the dungeon
        permanently, and puts it in the agent's key list. Note that this DOES
        NOT affect the actual Dungeon, only the Agent and its Map.
        """
        if not self.map.loc_valid(keyLoc):
            raise ValueError("{} is not a valid location".format(keyLoc))
        if keyLoc not in self.map.floor.keys():
            return False
        if not (self.map.adjacent(self.at, keyLoc) or self.at == keyLoc):
            return False

        key = self.map.get_item_at(keyLoc, KEY)
        if key:
            self.map.remove_object_at(KEY, keyLoc)
            key.taken = True
            key.location = None
            self.keys.append(key)
            return True
        return False

    def take_coin(self, coinLoc):
        """
        Take possession of a coin at `coinLoc`.

        Takes a coin off the floor and keeps it. This removes it from the dungeon
        permanently, and increments the agent's coin amount by 1. Note that this
        DOES NOT affect the actual Dungeon, only the Agent and its Map.
        """
        if not self.map.loc_valid(coinLoc):
            raise ValueError("{} is not a valid location".format(coinLoc))
        if coinLoc not in self.map.floor.keys():
            return False
        if not (self.map.adjacent(self.at, coinLoc) or self.at == coinLoc):
            return False

        coin = self.map.get_item_at(coinLoc, COIN)
        if coin:
            self.map.remove_object_at(COIN, coinLoc)
            self.coins += coin.value
            return True
        return False

    def unlock(self, target):
        """
        Unlock a door or chest at `target`.

        If there is a door at `target`, the door becomes unlocked and passable,
        if there is a chest, it becomes unlocked. As per usual, this method
        DOES NOT affect the actual Dungeon, merely this Agent and its Map.
        """
        if not self.map.loc_valid(target):
            raise ValueError("{} is not a valid location".format(target))
        if target not in self.map.floor.keys():
            return False
        if not self.map.adjacent(self.at, target):
            return False

        for obj in self.map.floor[target]:
            if obj.locked and self.can_unlock(obj):
                obj.locked = False
                if obj.objType == DOOR:
                    obj.passable = True
                return True
        return False

    def apply_action(self, action):
        actType = action.op
        args = action.args

        if actType == 'move':
            moveDir = args[0]
            succeeded = self.move(moveDir)

        elif actType == 'takekey':
            keyLoc = args[0]
            succeeded = self.take_key(keyLoc)

        elif actType == 'unlock':
            target = args[0]
            succeeded = self.unlock(target)

        else:
            raise NotImplementedError("Action type {} is not implemented".format(actType))

        return succeeded

    def draw_map(self):
        print(str(self.map))

    def valid_goal(self, goal):
        """Wrapper to allow easier access to goal checking."""
        return self.map.valid_goal(goal)

    def create_goal(self, action, *args):
        """Wrapper to allow easier use of goal creation."""
        return self.map.create_goal(action, *args)

    def goal_complete(self, goal):
        """Indicate whether a MIDCA goal has been completed."""
        if goal.kwargs['predicate'] == 'move-to':
            return self.at == goal.args[0]
        elif goal.kwargs['predicate'] == 'open':
            return self.map.loc_unlocked(goal.args[0])
        else:
            raise NotImplementedError("Goal {} is not valid".format(goal))

    def can_unlock(self, obj):
        return any([k.unlocks == obj for k in self.keys])

    def forecast_action(self, action):
        """Return a copy of self with the action applied."""
        futureSelf = deepcopy(self)
        futureSelf.apply_action(action)
        return futureSelf

    def diff(self, other):
        """
        Produce a dict of differences between this Agent and a different one.

        Examines the vital attributes of each Agent and identifies any
        differences between them. Then returns a dict, where each key is an
        attribute and its value is a pair with the value of the attribute in
        question from each Agent. This Agent's value comes first in the pair.
        """
        diffs = {}
        if self.__name__ != other.__name__:
            diffs['__name__': (self.__name, other.__name__)]
        if self.at != other.at:
            diffs['at': (self.at, other.at)]
        if self.vision != other.vision:
            diffs['vision': (self.vision, other.vision)]
        if self.keys != other.keys:
            diffs['keys'] = (self.keys, other.keys)
        if self.coins != other.coins:
            diffs['coins'] = (self.coins, other.coins)
        if self.health != other.health:
            diffs['health'] = (self.health, other.health)

        mapDiffs = self.map.diff(other.map)
        if mapDiffs:
            for tile in mapDiffs.keys():
                diffs[tile] = mapDiffs[tile]

        return diffs

    def get_objects_at(self, loc):
        """Quickly retrieve location information from the Map."""
        return self.map.floor[loc] if loc in self.map.floor.keys() else None

    def can_reach(self, loc):
        """Indicate whether the agent can reach the location."""
        attemptedPath = self.navigate_to(loc)
        if attemptedPath is None or attemptedPath == []:
            return False
        return True


def draw_Dungeon(dng):
    """Print the Dungeon board."""
    print(str(dng))


def build_Dungeon_from_str(dngStr):
    """Take in a string and create a new Dungeon from it."""
    lines = dngStr.split('\n')
    dim = int(lines[0][4:])
    agentLoc = int(lines[1][5:])
    agentVision = int(lines[2][5:])
    dng = Dungeon(dim=dim, agent_vision=agentVision, agentLoc=agentLoc)
    lines = lines[3:]
    while len(lines) > 0:
        line = lines.pop()
        objCode = line[0]
        locIndex = line.index('@') + 1
        miscIndex = line.index(':') + 1 if ':' in line else len(line)

        objType = OBJECT_ID_CODES[objCode]
        location = get_point_from_str(line[locIndex:miscIndex-1])
        miscData = line[miscIndex:]
        objsMade = []

        if objType == WALL:
            objsMade.append(dng.place_object(WALL, location))
        elif objType == DOOR:
            locked = False if miscData.lower() == 'false' else True
            objsMade.append(dng.place_object(DOOR, location, locked=locked))
        elif objType == CHEST:
            if miscData == '':
                objsMade.append(dng.place_object(CHEST, location))
            else:
                contains = None
                for obj in objsMade:
                    if repr(obj) == miscData:
                        contains = obj
                        break
                if contains:
                    objsMade.append(dng.place_object(CHEST, location,
                                                     contains=contains))
                else:
                    lines.append(line)
        elif objType == KEY:
            unlocks = None
            for obj in objsMade:
                if repr(obj) == miscData:
                    unlocks = obj
                    break
            if unlocks:
                objsMade.append(dng.place_object(KEY, location, unlocks=unlocks))
            else:
                lines.append(line)
        elif objType == COIN:
            value = int(miscData)
            objsMade.append(dng.place_object(COIN, location, value=value))
        elif objType == FIRE:
            dmg = int(miscData)
            objsMade.append(dng.place_object(FIRE, location, damage=dmg))
        elif objType == TRAP:
            dmg = int(miscData)
            objsMade.append(dng.place_object(TRAP, location, damage=dmg))
        else:
            raise NotImplementedError(objType)
    return dng


def build_Dungeon_from_file(filename):
    """
    Take in a text file and create a new Dungeon from it.

    Passes the text of the file into build_Dungeon_from_str.
    """
    with open(filename, 'r') as dngFile:
        dngStr = dngFile.read()

    return build_Dungeon_from_str(dngStr)


def interactive_Dungeon_maker():
    """Allows a user to build a Dungeon from scratch."""
    def parse_command(cmd, dng, objsMade):
        """Parse a command and then execute it."""
        cmdData = cmd.split(' ')
        cmdAction = cmdData[0]

        if cmdAction == 'set':
            attrib = cmdData[1].lower()
            if attrib == 'agent-loc':
                dest = get_point_from_str(cmdData[2])
                success = dng.teleport_agent(dest)
            elif attrib == 'agent-vision':
                vRange = int(cmdData[2])
                dng.agent.vision = vRange
                success = True
            else:
                success = False
                error = "Unknown attribute {} for set command".format(attrib)
        if cmdAction == 'add':
            objType = cmdData[1].upper()
            objLoc = get_point_from_str(cmdData[2])
            miscData = cmdData[3] if len(cmdData) == 4 else None

            if objType not in OBJECT_LIST:
                print("Unknown object type {}".format(objType))
            elif objType == WALL:
                newObj = dng.place_object(WALL, objLoc)
                objsMade[hash(newObj)] = newObj
                return True
            elif objType == DOOR:
                if not miscData:
                    newObj = dng.place_object(DOOR, objLoc)
                    return True
                elif miscData.lower() == 'true':
                    newObj = dng.place_object(DOOR, objLoc, locked=True)
                    return True
                elif miscData.lower() == 'false':
                    newObj = dng.place_object(DOOR, objLoc, locked=False)
                    return True
                else:
                    print("Unkown door lock status {}".format(miscData))
                    return False
            elif objType == CHEST:
                if not miscData:
                    newObj = dng.place_object(CHEST, location)
                    success = ("add", newObj)



    dim = input("First, how big is the dungeon? ")
    dng = Dungeon(dim)
    objsMade = {}
    while True:
        os.system('clear')
        print(str(dng))
        print("""Commands:
        \r\rset agent-loc POINT moves the Agent to (x, y)
        \r\rset agent-vision INT sets how far the Agent can see
        \r\radd OBJTYPE POINT MISCDATA places an object at the given location
        \r\rrem OBJID removes the object with the given id
        \r\rset OBJID ATTRIBUTE VALUE changes the object's attribute
        \r\rsave FILENAME writes the Dungeon to the given file
        \r\rquit

        Object IDs:\n""")
        for objID in objsMade:
            print(objsMade[objID], objID)
        command = raw_input("Command>> ")
        result = parse_command(command, dng)
        print result
        raw_input("ENTER to coninute...")


def get_point_from_str(string):
    """Convert a string of form '(x, y)' into a pair of ints."""
    coords = string.strip('()').split(',')
    point = (int(coords[0]), int(coords[1]))
    return point


def test():
    """Function for easier testing."""
    dng = Dungeon(5)
    dng.generate(3, 3, 5)
    print(dng.MIDCA_state_str())
    print(str(dng))


if __name__ == '__main__':
    test()
