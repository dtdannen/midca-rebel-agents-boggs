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


class Dungeon(object):
    """
    Class representing an entire dungeon.

    Contains a dungeon map, the state of doors and chests, and changes the
    environment when needed.
    """

    def __init__(self, dim):
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

    def place_object(self, obj, location):
        if not self.__loc_valid:
            raise Exception("{} is not a valid place for {}".format(location, obj))
        if obj.objType in [CHEST, DOOR, WALL]:
            if not self.loc_is_tile(location):
                raise Exception("{} is already occupied by a large object".format(location))
        if location in self.floor.keys():
            self.floor[location].append(obj)
        else:
            self.floor[location] = [obj]

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

    def MIDCA_state_str(self):
        """Generate a MIDCA state based on the current state of the dungeon."""
        stateStr = "AGENT(Drizzt)\nDIM({})\n".format(self.dim)

        # Establish objects
        for loc in self.floor:
            contents = self.floor[loc]
            for obj in contents:
                objType = obj.objType
                objID = obj.id
                stateStr += "{}({})\n".format(objType, objID)
        for loc in [(x, y) for x in range(self.dim) for y in range(self.dim)]:
            if loc in self.floor.keys():
                if not self.check_passable(loc) and loc != self.agentLoc:
                    continue
            stateStr += "TILE(Tx{}y{})\n".format(loc[0], loc[1])

        # Generate predicates
        for loc in [(x, y) for x in range(self.dim) for y in range(self.dim)]:
            stateStr += self.generate_loc_adjancencies(loc)
            stateStr += self.generate_loc_misc(loc)

        stateStr += "agent-at(Drizzt, Tx{}y{})".format(str(self.agentLoc[0]), str(self.agentLoc[1]))

        return stateStr

    def generate_loc_misc(self, loc):
        """Generate the object-specific predicates."""
        if loc not in self.floor.keys():
            return ""

        objPreds = ""
        for obj in self.floor[loc]:
            objType = obj.objType
            if objType == KEY:
                if len(self.floor[loc]) > 1:
                    keyTileID = self.floor[loc][0].id
                else:
                    keyTileID = "Tx{}y{}".format(loc[0], loc[1])
                objPreds += "key-at({}, {})\n".format(obj.id, keyTileID)
                objPreds += "opens({}, {})\n".format(obj.id, obj.unlocks.id)
            if objType == CHEST:
                objPreds += "closed({})\n".format(obj.id)

        return objPreds

    def generate_loc_adjancencies(self, loc):
        """Generate MIDCA adjacency predicates for given location."""
        directions = ['north', 'east', 'south', 'west']

        adjStr = ""
        nNbor = (loc[0], loc[1]-1)
        eNbor = (loc[0]+1, loc[1])
        sNbor = (loc[0], loc[1]+1)
        wNbor = (loc[0]-1, loc[1])
        nbors = [nNbor, eNbor, sNbor, wNbor]

        # First, generate directional adjacencies
        for nbor in nbors:
            if not self.__loc_valid(nbor):
                continue
            nDir = directions[nbors.index(nbor)]

            if self.loc_is_tile(loc):
                locID = "Tx{}y{}".format(loc[0], loc[1])
                if self.loc_is_tile(nbor):
                    nborID = "Tx{}y{}".format(nbor[0], nbor[1])
                else:
                    nborID = self.floor[nbor][0].id
            else:
                locID = self.floor[loc][0].id
                if self.loc_is_tile(nbor):
                    nborID = "Tx{}y{}".format(nbor[0], nbor[1])
                else:
                    nborID = self.floor[nbor][0].id
            adjStr += "adjacent-{}({}, {})\n".format(nDir, locID,
                                                     nborID)
        # Now, we create all the generic adjacencies
        existingLines = adjStr.split('\n')
        existingLines.pop()
        for line in existingLines:
            args = "(" + line.split("(")[1]
            adjStr += "adjacent" + args + "\n"

        return adjStr

    def loc_is_tile(self, loc):
        """
        Indicate whether the location is a TILE or not.

        This is similar to check_passable, but more robust because DOORs can
        change in terms of passability (by being unlocked).
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
        if loc == self. agentLoc:
            tileStr += '@'

        # If the tile has contents, draw them
        if loc in self.floor.keys():
            for obj in self.floor[loc]:
                tileStr += obj.ascii_rep

        # Pad the tile and return
        tileStr = tileStr.rjust(2, '.')
        return tileStr

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


def draw_Dungeon_from_MIDCA(midcaworld, rtn_str=False):
    """
    Take in the MIDCA world and return an ASCII board.

    This function accepts the MIDCA world state as a string, and turns that into
    a new Dungeon object. Then it returns the ASCII representation of that
    Dungeon.
    """
    def obj_from_MIDCA(objStr):
        """Return a DungeonObject from a valid MIDCA string."""
        if objStr[0] not in OBJECT_ID_CODES.values():
            return objStr
        try:
            objCode = objStr[0]
            xIndex = objStr.index("x")
            yIndex = objStr.index("y")
            xVal = int(objStr[xIndex+1:yIndex])
            yVal = int(objStr[yIndex+1:])
            objLoc = (xVal, yVal)
            objType = None
            for objTypeLabel in OBJECT_ID_CODES:
                if objCode in OBJECT_ID_CODES[objTypeLabel]:
                    objType = objTypeLabel
            newObj = DungeonObject(objType, objLoc)
            return newObj
        except Exception:
            print(objStr)
            return objStr

    objectStrs = [str(o) for o in midcaworld.objects if 'T' not in str(o)]
    useful_atoms = [str(a) for a in midcaworld.get_atoms() if 'adjacent' not in str(a)]
    obj_atom_dict = {}
    for objStr in objectStrs:
        obj_atom_dict[obj_from_MIDCA(objStr)] = [atom for atom in useful_atoms if objStr in atom]

    for obj in obj_atom_dict:
        atoms = obj_atom_dict[obj]
        for atom in atoms:
            pred, args = atom.split('(')
            args = args.strip(')').split(', ')
        # TODO finish connecting atoms to

    dim = 0
    for obj in objectStrs:
        try:
            dim = int(obj)
            break
        except Exception:
            continue
    newDng = Dungeon(dim=dim)

    print(objectStrs)
    print(useful_atoms)
    print(dim)


def test():
    """Function for easier testing."""
    dng = Dungeon(5)
    dng.generate(3, 3, 5)
    print(dng.MIDCA_state_str())
    print(str(dng))


if __name__ == '__main__':
    test()
