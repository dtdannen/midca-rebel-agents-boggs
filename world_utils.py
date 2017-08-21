"""
Contains the ``World`` class and related classes and functions.

This is the module responsible for anything to do with representing or simulating
a ``World`` and the ``Agents`` and ``Operators`` within it. This module features
three main classes: ``World``, ``WorldObject``, and ``Agent``, as well as
``WorldObject`` subclasses such as ``Npc``. There are also a handful of useful
functions, such as functions which can create worlds or perform helpful conversions.
"""

from copy import deepcopy
from random import randint
import logging
import os
import traceback
import StringIO
from MIDCA import plans, goals

AGENT = "AGENT"  #: Easily check if an Agent object is an agent
OPERATOR = "OPERATOR"  #: Easily check if an Agent object is an operator

CHEST = 'CHEST'  #: Easily check if a WorldObject object is a chest
DOOR = 'DOOR'  #: Easily check if a WorldObject object is a door
WALL = 'WALL'  #: Easily check if a WorldObject object is a wall
KEY = 'KEY'  #: Easily check if a WorldObject object is a key
COIN = 'COIN'  #: Easily check if a WorldObject object is a coin
FIRE = 'FIRE'  #: Easily check if a WorldObject object is a fire
TRAP = 'TRAP'  #: Easily check if a WorldObject object is a trap
NPC = 'NPC'  #: Easily check if a WorldObject object is a NPC

UNARMED = 0  #: Easily check if an agent is unarmed
ARMING = 1  #: Easily check if an agent is arming
ARMED = 2  #: Easily check if an agent is armed

ENEMY_RED = '\033[31m'
CIVI_GREEN = '\033[32m'
AGENT_BLUE = '\033[34m'
END_COLOR = '\033[0m'

#: List of all objects which could be in the World
OBJECT_LIST = [CHEST, DOOR, WALL, KEY, COIN, FIRE, TRAP, NPC, AGENT, OPERATOR]

#: Conversion table from object characters to object strings
OBJECT_ID_CODES = {"C": CHEST,
                   "D": DOOR,
                   "W": WALL,
                   "k": KEY,
                   "$": COIN,
                   "*": FIRE,
                   "^": TRAP,
                   "&": NPC,
                   "A": AGENT,
                   "O": OPERATOR}

#: Conversion table from object strings to object characters
OBJECT_CODE_IDS = {CHEST: "C",
                   DOOR: "D",
                   WALL: "W",
                   KEY: "k",
                   COIN: "$",
                   FIRE: "*",
                   TRAP: "^",
                   NPC: "&",
                   AGENT: "A",
                   OPERATOR: "O"}

#: Conversion table from direction-indicating characters to strings
DIRECTON_EXPANSIONS = {'n': 'north',
                       's': 'south',
                       'w': 'west',
                       'e': 'east'}


class WorldObject(object):
    """
    Superclass for objects and obstacles in the world.

    All objects share several traits, which are handled by this superclass:

    ``objType``:
        This is a string which indicates what type of object the object really is.
        This value should be a member of ``OBJECT_LIST``. This is set automatically
        when a ``WorldObject`` subclass is instantiated, and should **not** be
        altered.

    ``passable``:
        This is a boolean which indicates whether an ``Agent`` can move through
        the tile which the object is on. This is set automatically when a ``WorldObject``
        subclass is instantiated, and may change as a result of actions taken by
        agents or operators.

    ``location``:
        This is a pair of ints which indicates where on the board the object is
        located. This is the only argument which all ``WorldObject`` subclasses
        require for instantiation. Currently this value does not change, but it
        may be altered as a result of agent or operator actions.

    All subclasses also have several properties and magic methods, some of which
    are provides universally by the base class and some of which must be implemented
    in each subclass.
    """

    def __init__(self, location):
        """
        Create object by giving it a location.

        The WorldObject superclass should not be directly instantiated.
        """
        self.objType = None
        self.passable = None
        self.location = location

    @property
    def ascii_rep(self):
        """
        Return the ASCII art version of the object for use in drawing the world.

        This property determines how an object is displayed on the world map, and
        must be overridden by any subclass of ``WorldObject``.

        ``return``:
            This function should return a str of length two or less.
        """
        raise NotImplementedError

    @property
    def id(self):
        """
        Return a unique string ID for the object.

        This function provides each object with a unique string by prepending the
        object code character to the string of ``hash(self)``. This should **not**
        be overridden by subclasses.

        ``return``:
            This function returns a six character string such that the first character
            is a letter in ``OBJECT_ID_CODES.keys()`` and the remaining five are
            the has value of the object.
        """
        return OBJECT_CODE_IDS[self.objType] + str(hash(self))[:5]

    @property
    def predicates(self):
        """
        Return a string of the MIDCA predicates appropriate for the object.

        In order to facilitate conversion to a MIDCA state representation, every
        object should be able to render all the prepositions which are relevant
        to it. The domain file ``world.sim`` lists every potential predicate. This
        function must be overridden by subclasses.

        ``return``:
            A string which features all predicates relevant to the object, each
            separated by a newline.
        """
        raise NotImplementedError

    def __str__(self):
        """
        Return the string representation of the object.

        This function should return an easily-readble verbal representation of the
        object. Concision is important, but human-readability is a larger concern.
        This method must be overridden by subclasses.

        ``return``:
            A human-readable string which describes the object.
        """
        raise NotImplementedError

    def __repr__(self):
        """
        Return a concise representation of the object.

        This function should emphasize concision and completeness, with human-readability
        being a secondary concern. The string which results from this function should
        allow complete reconstruction of the object, i.e. all information about
        the object should be encoded in the string. This method must be overridden
        by subclasses.

        ``return``:
            A concise, complete representation of the object.
        """
        raise NotImplementedError

    def __eq__(self, other):
        """Indicate whether this object is equal to the other object.

        This function is used to compare the equality of two objects in the ``World``.
        Because the string returned by the ``__repr__`` method should encode ALL
        information about the object in a predicatable way, two objects are equal
        iff their representations are equal. That principle underlies this function.
        This function does not need to be overridden by subclasses.

        ``return``:
            A boolean which is true iff the two objects are equivalent.
        """
        return repr(self) == repr(other)

    def __hash__(self):
        """
        Return an integer unique to this object.

        This function should generate an integer such that no other object which
        is not equivalent to this one will have the same value for its ``__hash__``
        function. This is accomplished by calling Python's built-in ``hash`` function
        on the representation of this object. Since the representation encodes ALL
        information about this object in a predictable way, the hash value will
        be unique to objects with exactly the same state as this one.

        ``return``:
            An integer unique to this object.
        """
        return hash(repr(self))


class Wall(WorldObject):
    """
    Represents a wall in the world.

    Walls are obstacles with no special properties. They only block tiles, nothing
    else.

    Instantiation::

        wall = Wall((x, y))
    """

    def __init__(self, location):
        """Instantiate a world at ``location``."""
        super(Wall, self).__init__(location)
        self.passable = False
        self.objType = WALL

    @property
    def ascii_rep(self):
        """
        Return the ASCII art version of the wall for use in drawing the world.

        A wall appears as two "X"s, as such::

            |XX|

        """
        return "XX"

    @property
    def predicates(self):
        """
        Return a string of the MIDCA predicates appropriate for a wall.

        A wall has no unique predicates, and so the return string is empty.
        """
        return ""

    def __str__(self):
        """
        Return the verbal representation of the wall.

        The verbal representation of a wall is not very interesting...
        """
        return "Wall @ {}".format(self.location)

    def __repr__(self):
        """Return a concise representation of the wall."""
        return "W@{}".format(self.location)


class Chest(WorldObject):
    """
    Represents a chest in the world, and can hold things.

    A chest has two interesting properties: ``contains`` and ``locked``. However
    ``contains`` does not actually do anything at the moment besides store an
    object. Thus, ``locked`` is also not particularly interesting, although it is
    implemented fully. A chest is never passable.

    A chest can be instantiated with just a location or it can be given a list of
    objects to contain.

    Instantiation::

        chest = Chest((x,y)[, WorldObject])
    """

    def __init__(self, location, contains=None):
        """Instantiate a chest at the location, containing the given object."""
        super(Chest, self).__init__(location)
        self.passable = False
        self.objType = CHEST
        self.contains = contains
        self.locked = True

    def insert_object(self, obj):
        """
        Insert an object into the chest.

        This will override the existing object, if there is one.

        ``obj``:
            This must be an instance of a WorldObject.
        """
        assert isinstance(obj, WorldObject), "Cannot insert non-WorldObject into chest"
        self.contains = (obj)

    @property
    def ascii_rep(self):
        """
        Return the ASCII art version of the object for use in drawing the world.

        A chest is represented as an uppercase "C" if it is locked or a lowercase
        "c" if it is not. It is shown twice if it is enpty, and once it it contains
        something, as such::

            |C.| = locked, full
            |c.| = unlocked, full
            |CC| = locked, empty
            |cc| = unlocked, empty
        """
        if self.locked:
            char = 'C'
        else:
            char = 'c'
        if self.contains:
            return char
        else:
            return char * 2

    @property
    def predicates(self):
        """
        Return a string of the MIDCA predicates appropriate for the object.

        Three predicates relate to chests: ``chest-locked``, ``contains-key``, and
        ``contains-coin``.

        ``return``:
            A string which features all predicates relevant to the chest, each
            separated by a newline.
        """
        retStr = ""
        if self.locked:
            retStr += "chest-locked({})\n".format(self.id)
        if self.contains:
            if self.contains.objType == KEY:
                retStr += "contains-key({}, {})\n".format(self.id, self.contains.id)
            elif self.contains.objType == COIN:
                retStr += "contains-coin({}, {})\n".format(self.id, self.contains.id)
        return retStr

    def __str__(self):
        """
        Return the string representation of the object.

        The string for a chest will indicate whether it's unlocked or not, and
        what it contains.
        """
        locked = "Locked" if self.locked else "Unlocked"
        return "{} chest @ {} containing {}".format(locked, self.location,
                                                    str(self.contains))

    def __repr__(self):
        """
        Return a concise representation of the chest.

        The string for a chest will indicate whether it's unlocked or not, and
        what it contains.
        """
        char = "C" if self.locked else "c"
        return "{}@{}:{}".format(char, self.location, repr(self.contains))


class Door(WorldObject):
    """
    Represents a door in the world, which can be unlocked and opened.

    If a door is locked, it is not passable. Once the door is unlocked, it becomes
    passable. A door is by default instantiated as locked, by it can be
    instantiated as unlocked as well.

    Instantiation::

        door = Door((x,y)[, locked=bool])
    """

    def __init__(self, location, locked=True):
        """Instantiate a door at the given location."""
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

    @property
    def predicates(self):
        retStr = ""
        if self.locked:
            retStr += "door-locked({})\n".format(self.id)
        return retStr

    def __str__(self):
        locked = "Locked" if self.locked else "Unlocked"
        return "{} door @ {}".format(locked, self.location)

    def __repr__(self):
        char = "D" if self.locked else "d"
        return "{}@{}".format(char, self.location)


class Key(WorldObject):
    """Represents a key in the world. Can unlock a locked item."""

    def __init__(self, location, unlocks=None, inChest=None):
        super(Key, self).__init__(location)
        self.passable = True
        self.objType = KEY
        self.unlocks = unlocks
        self.taken = False
        self.inChest = inChest

    @property
    def ascii_rep(self):
        return 'k'

    @property
    def predicates(self):
        retStr = ""
        if self.unlocks:
            if self.unlocks.objType == DOOR:
                retStr += "unlocks-door({}, {})\n".format(self.id, self.unlocks.id)
            if self.unlocks.objType == CHEST:
                retStr += "unlocks-chest({}, {})\n".format(self.id, self.unlocks.id)
        if self.taken:
            retStr += "taken({})\n".format(self.id)
        if self.inChest:
            retStr += "key-in-chest({}, {})\n".format(self.id, self.inChest.id)
        return retStr

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


class Coin(WorldObject):
    """Represents a coin of some value in the world."""

    def __init__(self, location, value, inChest=None):
        super(Coin, self).__init__(location)
        self.passable = True
        self.objType = COIN
        self.value = value
        self.inChest = inChest

    @property
    def ascii_rep(self):
        return "$"

    @property
    def predicates(self):
        retStr = ""
        if self.inChest:
            retStr += "coin-in-chest({}, {})\n".format(self.id, self.inChest.id)
        return retStr

    def __str__(self):
        return "Coin @ {} worth {}".format(self.location, self.value)

    def __repr__(self):
        return "$@{}:{}".format(self.location, self.value)


class Fire(WorldObject):
    """Represents a fire in the world, which can deal damage to the agent."""

    def __init__(self, location, damage):
        super(Fire, self).__init__(location)
        self.passable = True
        self.objType = FIRE
        self.damage = 1

    @property
    def ascii_rep(self):
        return "**"

    @property
    def predicates(self):
        retStr = ""
        return retStr

    def __str__(self):
        return "Fire @ {} which deals {} damage".format(self.location, self.damage)

    def __repr__(self):
        return "*@{}:{}".format(self.location, self.damage)


class Trap(WorldObject):
    """Represents a trap in the world, which is hidden until it activates."""

    def __init__(self, location, damage):
        super(Trap, self).__init__(location)
        self.passable = True
        self.objType = TRAP
        self.damage = 1
        self.hidden = True

    @property
    def ascii_rep(self):
        return "" if self.hidden else "^^"

    @property
    def predicates(self):
        retStr = ""
        if self.hidden:
            retStr += "hidden({})\n".format(self.id)
        return retStr

    def __str__(self):
        hidden = "Hidden" if self.hidden else "Sprung"
        return "{} trap @ {} which deals {} damage".format(hidden, self.location,
                                                           self.damage)

    def __repr__(self):
        char = "h" if self.hidden else "s"
        return "^{}@{}:{}".format(char, self.location, self.damage)


class Npc(WorldObject):
    """Used to represent enemies and civilians in the world."""

    def __init__(self, location, civi=False, living=True):
        super(Npc, self).__init__(location)
        self.passable = False
        self.objType = NPC
        self.civi = civi
        self.alive = living

    @property
    def ascii_rep(self):
        if not self.alive:
            return ""
        if self.civi:
            return CIVI_GREEN + "&C" + END_COLOR
        else:
            return ENEMY_RED + "&E" + END_COLOR

    @property
    def predicates(self):
        retStr = ""
        return "is-{}({})\n".format(self.civ_type, self.id)

    @property
    def civ_type(self):
        return "civi" if self.civi else "enemy"

    def __str__(self):
        alive = "alive" if self.alive else "dead"
        return "{} NPC @ {} which is {}".format(self.civ_type.capitalize(),
                                                self.location, alive)

    def __repr__(self):
        char = "C" if self.civi else "E"
        status = "L" if self.alive else "D"
        return "&{}@{}:{}".format(char, self.location, status)


class World(object):
    """
    Class representing an entire world.

    Contains a world map and all objects on it, and handles any changing of or
    accessing data from the world.
    """

    def __init__(self, dim, bombRange=2, log=logging.getLogger("dummy")):
        """Initialize a blank world of size `dim`x`dim`."""
        assert type(dim) is int, "dim must be an int"

        # Generate self variables
        self.dim = self.hgt = self.wdt = dim
        self.bombRange = bombRange
        self.floor = {}
        self.users = {}
        self.log = log
        self.eventLog = ""
        self.log.info("\n\n")
        self.log.info("New world made")
        Agent.agentCount = 0
        Agent.operatorCount = 0

    @property
    def all_users(self):
        """Return a list of all users (agents and operators)."""
        return self.users.values()

    @property
    def agents(self):
        """Return a list of all of the agents in the ``World``."""
        agents = []
        for userID in self.users:
            if self.users[userID].userType == AGENT:
                agents.append(self.users[userID])
        return agents

    @property
    def operators(self):
        """Return a list of all of the operators in the ``World``."""
        operators = []
        for userID in self.users:
            if self.users[userID].userType == OPERATOR:
                operators.append(self.users[userID])
        return operators

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
        """Return a list of all objects in the ``World``."""
        objects = []
        for loc in self.floor:
            objects += self.floor[loc]
        return objects

    @property
    def enemies(self):
        """Return a list of all of the ``Npc`` objects marked as enemies."""
        return self.filter_objects(objType=NPC, civi=False)

    @property
    def civilians(self):
        """Return a list of all of the ``Npc`` objects labeled as civilians."""
        return self.filter_objects(objType=NPC, civi=True)

    @property
    def score(self):
        """
        Return a pair which indicates the current score.

        As implemented currently, the score is a pair of floats where the first
        value is the percentage of enemies which have been killed and the second
        value is the percentage of civilians remaining alive.

        Arguments:
            ``return``, *tuple*:
                A pair of floats reflecting the percentage of enemies killed and
                percentage of civilians still alive.
        """
        enemiesDead = len(self.filter_objects(civi=False, alive=False))
        civisAlive = len(self.filter_objects(civi=True, alive=True))
        enemyKillRatio = float(enemiesDead)/len(self.enemies)
        civiLiveRatio = float(civisAlive)/len(self.civilians)
        return (enemyKillRatio, civiLiveRatio)

    def filter_objects(self, **kwargs):
        """
        Return a list of known objects whose attributes fit the filters.

        This function allows the caller to select a subset of objects from in the
        ``World`` which have attributes matching certain criteria. This makes it
        much easier to find a specific subset, such as all living enemies or all
        unlocked doors. There is no set list of arguments. Instead, the function
        takes any number of keyword arguments and attempts to find objects which
        have as attributes the keywords, and have as values for those attributes
        the values assigned to the keywords. So, for example, if one argument is
        ``alive=True``, the function looks through all of the objects in the
        ``World`` looking for each object ``obj`` such that ``obj.alive == True``.
        It then returns a list of such objects.

        Arguments:
            ``kwargs``:
                Any keyword-value pair can be used as an argument, but if no
                objects exist which both have the keyword as an attribute and the
                appropriate value for it, then the returned list will be empty.

            ``return``, *list*:
                A list of ``WorldObject`` subclasses which match the filter kwargs
                given.
        """
        knownObjs = self.objects
        filteredObjs = []
        for obj in knownObjs:
            for attrib in kwargs:
                try:
                    valid = eval("obj.{}".format(attrib)) == kwargs[attrib]
                except AttributeError:
                    valid = False
                if not valid:
                    break
            if valid:
                filteredObjs.append(obj)
        return filteredObjs

    def add_user(self, name, location, vision, userType):
        """
        Add a user (agent or operator) to the world with the given attributes.

        This function creates a new user (techincally an ``Agent`` object, but
        of either the agent or operator persuasion) and places it on the board
        at the specified location, if this is possible. If the given location is
        either not a valid location in the world or is already occupied, this
        function raises an exception.

        Arguments:
            ``name``, *str*:
                The name of the agent or operator being placed. This doesn't bear
                much on the actual simulation, but all log files use this name.

            ``location``, *tuple*:
                The location in the ``World`` where the agent or operator should
                be placed. Must be unoccupied.

            ``vision``, *int*:
                The distance which the agent or operator can "see". Currently,
                an agent's vision is a square centered on the agent or operator,
                with a side length equal to twice the ``vision`` argument. Any
                object in that range can be perceived perfectly by the agent.

            ``userType``, *str*:
                This must be either ``"AGENT"`` or ``"OPERATOR"``, and indicates
                which type of user the ``Agent`` object created by this method
                will be.

            ``return``, *Agent*:
                The new ``Agent`` object which was created in the course of
                running this method.
        """
        if not self.loc_valid(location):
            raise Exception("Location {} is not valid".format(location))

        if not self.loc_is_free(location):
            return False

        if name in self.users:
            print("User named {} already exists".format(name))
            return False
        newUser = Agent(name, location, self.dim, vision, userType, self.bombRange)
        self.users[name] = newUser
        return newUser

    def get_user(self, userID):
        """
        Retrieve the ``Agent`` object with the given ID.

        This function looks through all of the agents and operators in the ``World``
        and returns the one which has the proper userID. If such a user doesn't
        exist, this raises a KeyError.

        Arguments:
            ``userID``, *str*:
                The unique ID of the agent or operator, specifically the name
                given to it when it was created.

            ``return``, *Agent*:
                The agent in the ``World`` which has as its ID the given userID
                argument.
        """
        return self.users[userID]

    def user_at(self, loc):
        """Indicate whether there is a user at the location."""
        for user in self.all_users:
            if user.at == loc:
                return True
        return False

    def get_user_at(self, loc):
        """Return the user at the location, of None if there isn't one."""
        if not self.user_at(loc):
            return None

        for user in self.all_users:
            if user.at == loc:
                return user

    def place_object(self, objType, location, **kwargs):
        """Place a new object of the given type at the location, if possible."""
        if not self.loc_valid(location):
            raise Exception("{} is not a valid place for {}".format(location, objType))

        if objType in [CHEST, DOOR, WALL, TRAP, FIRE, NPC]:
            if not self.loc_is_free(location):
                # print("{} is already occupied by a large object".format(location))
                return False

        if objType == WALL:
            obj = Wall(location)
        elif objType == CHEST:
            if 'contains' in kwargs:
                contains = kwargs['contains']
                obj = Chest(location, contains)
            else:
                obj = Chest(location)
        elif objType == DOOR:
            obj = Door(location)
        elif objType == KEY:
            if 'unlocks' in kwargs:
                unlocks = kwargs['unlocks']
                obj = Key(location, unlocks)
            else:
                obj = Key(location)
        elif objType == COIN:
            value = kwargs['value']
            obj = Coin(location, value)
        elif objType == FIRE:
            damage = kwargs['damage']
            obj = Fire(location, damage)
        elif objType == TRAP:
            damage = kwargs['damage']
            obj = Trap(location, damage)
        elif objType == NPC:
            civi = kwargs['civi']
            obj = Npc(location, civi)
        else:
            raise NotImplementedError(objType)

        if location in self.floor:
            self.floor[location].append(obj)
        else:
            self.floor[location] = [obj]

        self.log.info("Placed object {}".format(obj))
        return obj

    def remove_object(self, objID):
        """Remove the given object from the map."""
        for obj in self.objects:
            if repr(obj) == objID:
                break
        self.remove_object_at(obj.objType, obj.location)

    def add_object(self, obj):
        """Add the given object to the map. Does NOT pay attention to spacing rules."""
        if not isinstance(obj, WorldObject):
            raise Exception("obj {} should be a WorldObject, but is {}".format(obj, type(obj)))
        objLoc = obj.location
        if objLoc in self.floor:
            if obj in self.floor[objLoc]:
                return
            self.floor[objLoc].append(obj)
        else:
            self.floor[objLoc] = [obj]
        self.log.info("Added {}".format(obj))

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
                break
        if remove_index == -1:
            print("There's no {} at {}".format(objType, loc))
            return False
        del self.floor[loc][remove_index]
        if len(self.floor[loc]) == 0:
            del self.floor[loc]

        self.log.info("Removed obj {}".format(obj))
        return True

    def teleport_agent(self, dest, userID):
        """Spontaneously move the agent to the dest, if possible."""
        user = self.users[userID]
        if not self.loc_valid(dest):
            print("{} is not a valid location".format(dest))
            return False
        if not self.check_passable(dest):
            print("Can't move the agent to {}".format(dest))
            return False
        user.at = dest

        self.log.info("Teleported agent {} to {}".format(user, dest))
        self.eventLog += "Teleported agent {} to {}".format(user, dest)
        return True

    def move_agent(self, moveDir, userID):
        """Legally move the agent in the given direction."""
        user = self.users[userID]

        if user.damage == 'broken':
            return False

        if moveDir == 'n':
            dest = (user.at[0], user.at[1]-1)
        elif moveDir == 'e':
            dest = (user.at[0]+1, user.at[1])
        elif moveDir == 's':
            dest = (user.at[0], user.at[1]+1)
        elif moveDir == 'w':
            dest = (user.at[0]-1, user.at[1])
        else:
            raise ValueError("{} is not a valid movement direction".format(moveDir))

        if not self.loc_valid(dest) or not self.check_passable(dest):
            return False

        self.take_damage(dest, userID)
        user.move(moveDir)

        self.log.info("Agent {} moved {} to {}".format(user, moveDir, dest))
        self.eventLog += "Agent {} moved {} to {}\n".format(user, moveDir, dest)
        return True

    def take_damage(self, loc, userID):
        damageDealt = 0
        if loc in self.floor:
            for obj in self.floor[loc]:
                try:
                    damageDealt += obj.damage
                except AttributeError:
                    continue

                if obj.objType == TRAP and obj.hidden:
                    obj.hidden = False
        self.users[userID].take_damage(damageDealt)

    def agent_take_key(self, keyLoc, userID):
        """If possible, have the agent actually take a key."""
        if not self.loc_valid(keyLoc):
            raise ValueError("{} is not a valid location".format(keyLoc))

        if keyLoc not in self.floor.keys():
            print("Key location {} not in floor.keys()".format(keyLoc))
            return False

        user = self.users[userID]

        if not (self.adjacent(user.at, keyLoc) or user.at == keyLoc):
            print("Agent at {} not adjacent or on key location {}".format(user.at, keyLoc))
            return False

        key = self.get_item_at(keyLoc, KEY)
        if key:
            self.remove_object_at(KEY, keyLoc)
            key.taken = True
            key.location = None
            user.take_key(keyLoc)
            self.log.info("Agent {} took {}".format(user, key))
            return True
        print("There's no key at {}".format(keyLoc))
        return False

    def agent_take_coin(self, coinLoc, userID):
        """If possible, have the agent actually take a coin."""
        if not self.loc_valid(coinLoc):
            raise ValueError("{} is not a valid location".format(coinLoc))

        if coinLoc not in self.floor.keys():
            print("Coin location {} not in floor.keys()".format(coinLoc))
            return False

        user = self.users[userID]

        if not (self.adjacent(user.at, coinLoc) or user.at == coinLoc):
            print("Agent at {} not adjacent or on coin at location {}".format(user.at, self.coinLoc))
            return False

        coin = self.get_item_at(coinLoc, COIN)
        if coin:
            self.remove_object_at(COIN, coinLoc)
            user.take_coin(coinLoc)
            self.log.info("Agent {} took {}".format(user, coin))
            return True
        print("There's no coin at {}".format(coinLoc))
        return False

    def agent_unlock(self, target, userID):
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

        user = self.users[userID]

        if not self.adjacent(user.at, target):
            print("Agent at {} not adjacent to target location {}".format(user.at, target))
            return False

        for obj in self.floor[target]:
            if obj.locked and user.can_unlock(obj):
                obj.locked = False
                if obj.objType == DOOR:
                    obj.passable = True
                user.unlock(target)
                self.log.info("Agent {} unlocked {}".format(user, obj))
                return True
        print("There's no locked object at {}".format(target))
        return False

    def agent_bomb(self, userID):
        """Have the agent detonate a bomb at its location."""
        user = self.users[userID]
        if not user.armed == ARMED:
            return 0
        target = user.at
        killed = self.bombed_at(target)
        user.bomb()
        self.log.info("Agent {} bombed {}, killing {}".format(user, target, killed))
        self.eventLog += "Agent {} bombed {}, killing {}\n".format(user, target, killed)
        return killed

    def bombed_at(self, target):
        """Detonate a bomb at the target location."""
        killed = 0
        surroundingObjs = self.get_objects_around(target, self.bombRange, makeCopy=False)
        for loc in surroundingObjs:
            for obj in surroundingObjs[loc]:
                if obj.objType == NPC and obj.alive:
                    killed += 1
                    obj.alive = False
                    obj.passable = True
                    self.log.info("Bomb at {} killed {}".format(target, obj))
                    self.eventLog += "\tBomb at {} killed {}\n".format(target, obj)
        return killed

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

    def get_objects_around(self, loc, vRange, includeHidden=False, makeCopy=True):
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
                    viewedObjs = [obj for obj in self.floor[vLoc] if not (obj.objType == TRAP and obj.hidden and not includeHidden)]
                    if makeCopy:
                        objects[vLoc] = deepcopy(viewedObjs)
                    else:
                        objects[vLoc] = viewedObjs
        return objects

    def get_users_around(self, loc, vRange):
        """Return the users around a location."""
        users = {}
        if vRange == -1:
            return self.users
        northBound = max(loc[1] - vRange, 0)
        southBound = min(loc[1] + vRange, self.dim)
        westBound = max(loc[0] - vRange, 0)
        eastBound = min(loc[0] + vRange, self.dim)

        for x in range(westBound, eastBound+1):
            for y in range(northBound, southBound+1):
                vLoc = (x, y)
                if self.user_at(vLoc):
                    user = self.get_user_at(vLoc)
                    users[user.__name__] = user

        return users

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
        if self.user_at(loc):
            return True

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

        if self.user_at(loc):
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
        if self.user_at(loc):
            tileStr += self.get_user_at(loc).ascii_rep

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
        goalPred = goal.kwargs['predicate']

        if goalPred == 'agent-at' and not self.check_passable(goalLoc):
            raise Exception("Invalid goal: agent can't be at {}".format(goalLoc))

        if goalPred == 'open'and self.check_passable(goalLoc):
            raise Exception("Invalid goal: nothing to open at {}".format(goalLoc))
        return True

    def apply_action(self, action, userID):
        """Apply a PyHop generated action to the World."""
        actType = action.op
        args = action.args

        if actType == 'move':
            moveDir = args[0]
            succeeded = self.move_agent(moveDir, userID)

        elif actType == 'takekey':
            keyLoc = args[0]
            succeeded = self.agent_take_key(keyLoc, userID)

        elif actType == 'unlock':
            target = args[0]
            succeeded = self.agent_unlock(target, userID)

        elif actType == 'bomb':
            succeeded = self.agent_bomb(userID)

        elif actType == 'arm':
            agent = self.get_user(userID)
            agent.arm()
            self.log.info("Agent {} armed to {}".format(userID, agent.armed))
            self.eventLog += "Agent {} armed to {}\n".format(userID, agent.armed)
            return True

        else:
            raise NotImplementedError("Action type {} is not implemented".format(actType))

        if succeeded:
            return True

    def apply_action_str(self, actStr, userID):
        """Accept a string version of a pyhop command."""
        actionData = actStr.strip(')').split('(')
        op = actionData[0]
        args = [arg for arg in actionData[1].split(', ')]
        action = plans.Action(op, *args)
        self.apply_action(action, userID)

    def adjacent(self, loc1, loc2):
        """Indicate whether loc1 and loc2 are adjacent."""
        return abs(loc1[0]-loc2[0]) == 1 or abs(loc1[1]-loc2[1]) == 1

    def get_closest_adjacent(self, loc1, loc2):
        """Return the location pair which is adjacent to loc1 and closest to loc2."""
        adjacentTiles = self.get_adjacent(loc1)
        assert adjacentTiles is not None, "WATTTT"
        dist = (loc2[0]-loc1[0], loc2[1]-loc1[1])
        preffedNS = 'n' if dist[0] < 0 else 's'
        preffedWE = 'w' if dist[0] < 0 else 'e'
        if preffedWE in adjacentTiles:
            adjTile = adjacentTiles[preffedWE]
            if self.check_passable(adjTile):
                return adjTile
        elif preffedNS in adjacentTiles:
            adjTile = adjacentTiles[preffedNS]
            if self.check_passable(adjTile):
                return adjTile
        for loc in adjacentTiles:
            adjTile = adjacentTiles[loc]
            if self.check_passable(adjTile):
                return adjTile
        print("No adjacent tile to {}".format(loc1))
        return None

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

    def get_object(self, objID):
        """Return the object with the given ID, if there is one."""
        for obj in self.objects:
            if obj.id == objID:
                return obj

        print("Item with objID {} not found".format(objID))
        return None

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

    def status_display(self):
        """
        Return a useful UI which displays the map, actors, and enemies/civis.

        This function returns a string which can be printed to show critical
        information about the state of the world. It should display the map first,
        then list all actors (agents + operators), then show enemies and civilians,
        as well as their status. All of this should be fairly compact, too.

        Currently, should look like::

            map map map map map map | Agents    | Optrs
            map map map map map map | agt0      | op0
            map map map map map map | agt1      | op1
            map map map map map map | ...       | ...
            map map map map map map | Enemies   | Civis
            map map map map map map | enemy0    | civi0
            map map map map map map | enemy1    | civi1
            map map map map map map | ...       | ...


        Arguments:

        ``return``, *str*:
            A compact and concise but still complete view of the world state.
        """
        mapViewStrs = str(self).split("\n")[:-1]
        enemyStrs = [repr(e) for e in self.enemies]
        civiStrs = [repr(c) for c in self.civilians]
        agentStrs = [repr(a) for a in self.agents]
        optrStrs = [repr(o) for o in self.operators]

        mapHeight = len(mapViewStrs)
        agtEnmHeight = len(agentStrs) + len(enemyStrs)
        optrCiviHeight = len(optrStrs) + len(civiStrs)

        mapWidth = len(mapViewStrs[0])
        agtWidth = max([len(aStr) for aStr in agentStrs])
        optrWidth = max([len(oStr) for oStr in optrStrs])
        enemyWidth = max([len(eStr) for eStr in enemyStrs])
        civiWidth = max([len(cStr) for cStr in civiStrs])

        agtEnmWidth = max(agtWidth, enemyWidth)
        optrCiviWidth = max(optrWidth, civiWidth)

        finalDisplay = "{:^{mW}} | {:<{agW}} | {:<{opW}}\n".format("Map", "Agents", "Optrs",
                                                                   mW=mapWidth,
                                                                   agW=agtEnmWidth,
                                                                   opW=optrCiviWidth)

        totalHgt = max(mapHeight, agtEnmHeight, optrCiviHeight)

        for line in range(totalHgt):
            # Add the next line of the map
            if line < len(mapViewStrs):
                finalDisplay += mapViewStrs[line] + " | "
            else:
                finalDisplay += " " * mapWidth + " | "

            # Add the next agent or enemy string
            if line < len(agentStrs):
                agentOrEnemy = agentStrs[line]
            elif line == len(agentStrs):
                agentOrEnemy = "Enemies"
            elif line < agtEnmHeight:
                enemyIndex = line - len(agentStrs) - 1
                agentOrEnemy = enemyStrs[enemyIndex]
            else:
                agentOrEnemy = " " * agtEnmWidth + " | "

            # Add the next operator or civilian string
            if line < len(optrStrs):
                optrOrCivi = optrStrs[line]
            elif line == len(optrStrs):
                optrOrCivi = "Civilians"
            elif line < optrCiviHeight:
                civiIndex = line - len(optrStrs) - 1
                optrOrCivi = civiStrs[civiIndex]
            else:
                optrOrCivi = " " * optrCiviHeight

            finalDisplay += "{:<{aeWid}} | {:<{ocWid}}\n".format(agentOrEnemy, optrOrCivi,
                                                                 aeWid=agtEnmWidth,
                                                                 ocWid=optrCiviWidth)

        return finalDisplay

    def shuffle_actors(self):
        """Randomly move the agents and operators on the board."""
        for agent in self.agents:
            newLoc = self.random_loc()
            while not self.teleport_agent(newLoc, agent.id):
                newLoc = self.random_loc()

        for oprtr in self.operators:
            newLoc = self.random_loc()
            while not self.teleport_agent(newLoc, oprtr.id):
                newLoc = self.random_loc()

    def loc_valid(self, loc):
        x = loc[0]
        y = loc[1]
        if not 0 <= x < self.dim: return False
        if not 0 <= y < self.dim: return False
        return True

    def midca_state_str(self):
        """Return a string which MIDCA can interpret as a state."""

        def gen_user_decls(self):
            retStr = ""
            for agt in self.agents:
                retStr += "AGENT({}:{})\n".format(agt.id, agt.vision)

            for opr in self.operators:
                retStr += "OPERATOR({}:{})\n".format(opr.id, opr.vision)
            return retStr

        def gen_object_decls(self):
            """Return a string declaring the objects in domain language."""
            retStr = ""
            for obj in self.objects:
                retStr += "{}({})\n".format(obj.objType, obj.id)
            return retStr

        def gen_tile_decls(self):
            """Return a string declaring all tiles."""
            retStr = ""
            for loc in self.all_locations:
                retStr += "TILE(Tx{}y{})\n".format(loc[0], loc[1])
            return retStr

        def gen_tile_adjs(self):
            """Return a string declaring all tile adjacencies."""
            retStr = ""
            for loc in self.all_locations:
                nborDict = self.get_adjacent(loc)
                for nborDir in nborDict:
                    fullDir = DIRECTON_EXPANSIONS[nborDir]
                    nborLoc = nborDict[nborDir]
                    retStr += "adjacent-{}(Tx{}y{}, Tx{}y{})\n".format(fullDir,
                                                                       loc[0], loc[1],
                                                                       nborLoc[0], nborLoc[1])
                    retStr += "adjacent(Tx{}y{}, Tx{}y{})\n".format(loc[0], loc[1],
                                                                    nborLoc[0], nborLoc[1])
            return retStr

        def gen_obj_location_preds(self):
            """Return a string of predicates which indicate where objects are."""
            retStr = ""
            for obj in self.objects:
                retStr += "{}-at({}, Tx{}y{})\n".format(obj.objType.lower(),
                                                        obj.id,
                                                        obj.location[0],
                                                        obj.location[1])
            return retStr

        def gen_tile_preds(self):
            """Return a string with status predicates for each tile."""
            retStr = ""
            for loc in self.all_locations:
                if self.check_passable(loc):
                    retStr += "passable(Tx{}y{})\n".format(loc[0], loc[1])
                # if self.agent.can_see(loc):
                #     retStr += "visible(Tx{}y{})\n".format(loc[0], loc[1])
            return retStr

        def gen_object_preds(self):
            """Return a string with all appropriate predicates relation to objects."""
            retStr = ""
            for obj in self.objects:
                retStr += obj.predicates
            return retStr

        def gen_user_preds(self):
            retStr = ""
            for user in self.all_users:
                usrType = "operator" if user.userType == OPERATOR else "agent"
            retStr += "{}-at({}:{}, Tx{}y{})".format(usrType, user.id, user.vision,
                                                     user.at[0], user.at[1])
            return retStr

        retStr = "DIM({})\n".format(self.dim)

        retStr += "\n# User declarations\n"
        retStr += gen_user_decls(self)

        retStr += "\n# Tile declarations\n"
        retStr += gen_tile_decls(self)

        retStr += "\n# Object declarations\n"
        retStr += gen_object_decls(self)

        retStr += "\n# Tile adjacency predicates\n"
        retStr += gen_tile_adjs(self)

        retStr += "\n# Object location predicates\n"
        retStr += gen_obj_location_preds(self)

        retStr += "\n# Tile status predicates\n"
        retStr += gen_tile_preds(self)

        retStr += "\n# User predicates\n"
        retStr += gen_user_preds(self)

        retStr += "\n# Other object predicates\n"
        retStr += gen_object_preds(self)

        return retStr

    def random_loc(self):
        x = randint(0, self.dim-1)
        y = randint(0, self.dim-1)
        return (x, y)

    def copy(self):
        """Return a new ``World`` object identical to this one."""
        newWorld = build_World_from_str(repr(self))
        newWorld.log = self.log
        return newWorld

    def save(self, filename):
        """
        Save the current world as a file.

        This function writes the result of ``repr(self)`` to the file given in
        ``filename`` suffixed with ``.dng``. It also writes the MIDCA state
        representation of the world to the filename suffixed with ``.state``.

        Note that the MIDCA state converter is not finished and likely will not
        work properly.

        Arguments:

        ``filename``, *str*:
            The name of the file which the dungeon state will be saved to. ``.dng``
            and ``.state`` will be added by the code, and should not be inlcuded
            in the argument.

        """
        filename = "./dng_files/" + filename + ".dng"
        with open(filename, 'w') as saveFile:
            saveFile.write(repr(self))
        with open(filename+".state", 'w') as saveFile:
            saveFile.write(self.MIDCA_state_str())
        return True

    def __str__(self):
        """
        Convert the World to string form.

        This function returns a human-readable form of the ``World`` as a string.
        Specifically, it returns an ASCII grid which shows the current state
        of the ``World`` including the locations of each actor, NPC, and object.

        Arguments:
            ``return``, *str*:
                An ASCII grid with indicators for the location of actors and
                objects.
        """
        ascii_board = "  "
        for cNum in range(self.dim):
            ascii_board += "|{:<2}".format(cNum)
        ascii_board += "|\n"
        for y in range(self.dim):
            ascii_board += "{:<2}|".format(y)
            for x in range(self.dim):
                ascii_board += self.draw_ascii_tile((x, y)) + "|"
            ascii_board += "\n"
        return ascii_board

    def __eq__(self, other):
        """
        Check if two ``World`` objects are the equivalent.

        Since the string representation of a ``World`` encodes all relevant
        information concerning its status, if the representations of two ``World``
        objects are equivalent, then the ``World`` objects are too. Thus, this
        function compares the representations of this and another ``World`` for
        equality and returns the result of that comparison.

        Arguments:
            ``other``, *World*:
                The ``World`` object to check for equivalence with this one.

            ``return``, *bool*:
                A boolean value indicating whether this and the other ``World``
                are equivalent.
        """
        return repr(self) == repr(other)

    def __repr__(self):
        """
        Return a string which clearly encodes all information about the ``World``.

        The string returned by this function will included the size of the world
        as well as the location and attributes of every object and actor on it.
        Since the MIDCA cycle of actors (with the accompanying personality traits)
        are not accesible to the ``World`` object, these are *not* included in
        the string returned. Ultimately, the string returned can be used to
        generate a duplicate ``World`` object.

        The format of the returned string is fairly simple. The first line will
        look like ::

            dim:10

        thereby encoding the size of the ``World``. Each line after that will
        contain the string representation (``repr``) of an object on the board.

        Arguments:
            ``return``, *str*:
                A string representation of the ``World``.
        """
        retStr = "dim:{}\n".format(self.dim)
        for user in self.all_users:
            retStr += repr(user) + '\n'
        for obj in self.objects:
            retStr += repr(obj) + '\n'
        return retStr


class WorldMap(World):
    """
    Represents and allows manipulation of the Agent's knowledge of the World.

    Has many of the features of its parent class World, but is limited to what
    the Agent knows. It also doesn't have its own Agent to prevent recursion.
    """

    def __init__(self, dim, bombRange, agent):
        assert type(dim) is int, "dim must be an int"

        # Generate self variables
        self.dim = self.hgt = self.wdt = dim
        self.bombRange = bombRange
        self.floor = {}
        self.users = {agent.id: agent}
        self.agent = agent
        self.eventLog = ""
        self.log = DummyLog()

    def teleport_agent(self, dest):
        """Override a method the map shouldn't do."""
        raise NotImplementedError("A WorldMap can't teleport the agent!")

    def generate(self, chests, doors, walls):
        """Override a method the map shouldn't do."""
        raise NotImplementedError("A WorldMap can't generate itself!")

    def update_map(self, viewedObjs, viewedUsrs, center, vRange, operator=False):
        """Update the map based on what the Agent sees."""
        northBound = max(center[1] - vRange, 0)
        southBound = min(center[1] + vRange, self.dim)
        westBound = max(center[0] - vRange, 0)
        eastBound = min(center[0] + vRange, self.dim)

        for x in range(westBound, eastBound+1):
            for y in range(northBound, southBound+1):
                vLoc = (x, y)
                if vLoc in viewedObjs.keys():
                    self.floor[vLoc] = viewedObjs[vLoc]
                    del viewedObjs[vLoc]
                else:
                    if vLoc in self.floor.keys():
                        del self.floor[vLoc]

        if operator:
            for objLoc in viewedObjs:
                objs = viewedObjs[objLoc]
                for obj in objs:
                    if obj.objType == NPC and not obj.civi:
                        self.floor[objLoc] = viewedObjs[objLoc]

        for user in viewedUsrs:
            self.users[user.id] = user

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
        user = self.all_users[0]
        goalPred = goal.kwargs['predicate']

        if goalPred == 'agent-at':
            goalLoc = goal.args[0]
            if not self.check_passable(goalLoc):
                return (False, 'unpassable')
            if not self.navigate_to(user.at, goalLoc):
                return (False, 'no-access')

        if goalPred == 'open':
            goalLoc = goal.args[0]
            if self.check_passable(goalLoc):
                return (False, 'no-object')

        if goalPred == 'killed':
            targetID = goal.args[0]
            target = self.get_object(targetID)
            if not target:
                return (False, 'no-target')

            bombLoc = self.get_closest_adjacent(target.location, self.agent.at)
            if bombLoc is None:
                return (False, 'no-access')
            objsAroundTarget = self.get_objects_around(bombLoc, self.bombRange)
            for loc in objsAroundTarget:
                for obj in objsAroundTarget[loc]:
                    if obj.objType == NPC and obj.civi:
                        return (False, 'civi-killed')

        return (True, 'none')


class Agent(object):
    """
    Represents the agent, and in particular its state and knowledge.

    Used for PyHop planning in conjunction with fog-of-war and limited knowledge
    scenarios.
    """
    agentCount = 0
    operatorCount = 0

    def __init__(self, name, location, worldDim, vision=-1, userType=AGENT,
                 bombRange=2):
        self.__name__ = name
        self.id = name
        self.at = location
        self.vision = vision
        self.map = WorldMap(worldDim, bombRange, self)
        self.keys = []
        self.coins = 0
        self.health = 4
        self.userType = userType
        self.armed = UNARMED
        self.bombRange = bombRange
        if userType == AGENT:
            self.number = Agent.agentCount
            Agent.agentCount += 1
        else:
            self.number = Agent.operatorCount
            Agent.operatorCount += 1

    @property
    def damage(self):
        """Indicate the level of damage the bot has taken."""
        return {4: 'undamaged',
                3: 'slightly-damaged',
                2: 'moderately-damaged',
                1: 'heavily-damaged',
                0: 'broken'}[self.health]

    @property
    def known_objects(self):
        """Return a list of all world objects."""
        return self.map.objects

    @property
    def agents(self):
        """Return a list of all agents known to this agent."""
        return [a for a in self.map.agents if a != self]

    @property
    def enemies(self):
        return self.filter_objects(civi=False, alive=True)

    def filter_objects(self, **kwargs):
        """Return a list of known objects whose attributes fit the filters."""
        knownObjs = self.known_objects
        filteredObjs = []
        for obj in knownObjs:
            for attrib in kwargs:
                try:
                    valid = eval("obj.{}".format(attrib)) == kwargs[attrib]
                except AttributeError:
                    valid = False
                if not valid:
                    break
            if valid:
                filteredObjs.append(obj)
        return filteredObjs

    def view(self, world):
        viewedObjs = world.get_objects_around(self.at, self.vision)
        usrs = world.all_users

        if self.userType == OPERATOR:
            enemies = [e for e in world.objects if e.objType == NPC and not e.civi]
            for e in enemies:
                viewedObjs[e.location] = [e]

        self.map.update_map(viewedObjs, usrs, self.at, self.vision, operator=True)

    def update_knowledge(self, objOrAgent):
        """Add the given object or agent to the Agent's knowledge-base."""
        if isinstance(objOrAgent, Agent):
            self.map.users[objOrAgent.__name__] = objOrAgent

        elif isinstance(objOrAgent, WorldObject):
            self.map.add_object(objOrAgent)

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
        the Agent in the actual World.
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
            self.armed = UNARMED
            return True
        else:
            print("Can't move {} to {}. Agent at {}".format(moveDir, dest, self.at))
            return False

    def take_key(self, keyLoc):
        """
        Take possession of a key at `keyLoc`.

        Takes a key off the floor and keeps it. This removes it from the world
        permanently, and puts it in the agent's key list. Note that this DOES
        NOT affect the actual World, only the Agent and its Map.
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

        Takes a coin off the floor and keeps it. This removes it from the world
        permanently, and increments the agent's coin amount by 1. Note that this
        DOES NOT affect the actual World, only the Agent and its Map.
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
        DOES NOT affect the actual World, merely this Agent and its Map.
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

        elif actType == 'bomb':
            succeeded = self.map.bombed_at(self.at)

        elif actType == 'arm':
            succeeded = self.arm()

        else:
            raise NotImplementedError("Action type {} is not implemented".format(actType))

        return succeeded

    def draw_map(self):
        print(str(self.map))

    def valid_goal(self, goal):
        """Wrapper to allow easier access to goal checking."""
        return self.map.valid_goal(goal)

    def goal_complete(self, goal):
        """Indicate whether a MIDCA goal has been completed."""
        if goal.kwargs['predicate'] == 'agent-at':
            return self.at == goal.args[0]
        elif goal.kwargs['predicate'] == 'open':
            return self.map.loc_unlocked(goal.args[0])
        elif goal.kwargs['predicate'] == 'killed':
            target = self.map.get_object(goal.args[0])
            return target.alive is False
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
            diffs['__name__': (self.__name__, other.__name__)]
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

    def can_see(self, loc):
        """Indicate whether the agent can see that location."""
        return abs(loc[0]-self.at[0]) <= self.vision and abs(loc[1]-self.at[1]) <= self.vision

    def take_damage(self, damage):
        """Reduce the agent's health by the given amount."""
        self.health -= damage

    def bomb(self):
        """
        Detonate a bomb under the agent which kills enemies in a 2-block radius.

        An agent is *required* to be armed prior to detonating their bomb.

        Arguments:
            ``return``, *int*:
                The number of NPCs (civilians and enemies) killed in the blast.
        """
        if not self.armed == ARMED:
            return 0
        self.armed = UNARMED
        return self.map.bombed_at(self.at)

    def get_civs_in_blast(self, loc=None):
        """Return a list of civilians in the potential bomb blast."""
        civs = []
        if loc:
            objs = self.map.get_objects_around(loc, self.bombRange)
        else:
            objs = self.map.get_objects_around(self.at, self.bombRange)
        print(objs)
        for objLoc in objs:
            objList = objs[objLoc]
            for obj in objList:
                if obj.objType == NPC and obj.civi:
                    civs.append(obj)

        return civs

    def arm(self):
        """Arm the agent's bomb to be detonated."""
        if self.armed == UNARMED:
            self.armed = ARMING
        elif self.armed == ARMING:
            self.armed = ARMED
        return True

    @property
    def ascii_rep(self):
        if self.userType == AGENT:
            return AGENT_BLUE + "A" + str(self.number) + END_COLOR
        else:
            return "O" + str(self.number)

    def __repr__(self):
        char = "A" if self.userType == AGENT else "O"
        return "{}@{}:{}:{}".format(char, self.at, self.vision, self.__name__)


def draw_World(world):
    """
    Print the world.

    This function is used as the display function for MIDCA. Since the string
    of a ``World`` is a map of it, all that is required for displaying a World
    is to print the string.

    Arguments:
        ``world``, *World*:
            The ``World`` object to be displayed.

        ``return``, *None*
    """
    print(str(dng))


def generate_random_drone_demo(dim, civilians, enemies, operators, agents,
                               visionRange, bombRange, log=logging.getLogger("dummy")):
    """
    Create a blank ``World`` and populate it with appropriate NPCs and actors.

    This function randomly generates a ``World`` with the given number of NPCs
    and actors. The world can be used for testing with the drone strike demos,
    and the worlds created can use logging if a ``Logger`` is passed in.

    The function first creates a world of size ``dim`` with the given ``Logger``,
    then randomly places civilians, enemies, operators, and agents. Agents and
    operators are randomly assigned a vision distance within the range given by
    ``visionRange``, and agent bombs kill all NPCs within ``bombRange`` tiles.

    Arguments:
        ``dim``, *int*:
            The size of the world.

        ``civilians``, *int*:
            The number of civilian NPCs to place randomly in the world.

        ``enemies``, *int*:
            The number of enemies to place randomly in the world.

        ``operators``, *int*:
            The number of operators to place randomly in the world.

        ``agents``, *int*:
            The number of agents to place randomly in the world.

        ``visionRange``, *tuple*:
            A pair of ints, such that the first element indicates the smallest
            possible vision of an agent and the second indicates the largest.

        ``bombRange``, *int*:
            The size of the bomb blast.

        ``log``, *Logger*:
            The ``Logger`` object from Python's built-in ``logging`` library which
            the generated world will use to log events.

        ``return``, *World*:
            A randomly generated world with the appropriate number of NPCs and
            actors.
    """
    dng = World(dim, bombRange, log)
    for _ in range(civilians):
        while not dng.place_object(NPC, dng.random_loc(), civi=True):
            pass

    for _ in range(enemies):
        while not dng.place_object(NPC, dng.random_loc(), civi=False):
            pass

    for opNum in range(operators):
        uName = "Op" + str(opNum)
        vision = randint(*visionRange)
        while not dng.add_user(uName, dng.random_loc(), vision, OPERATOR):
            pass

    for agnNum in range(agents):
        agnName = "Agt" + str(agnNum)
        vision = randint(*visionRange)
        while not dng.add_user(agnName, dng.random_loc(), vision, AGENT):
            pass

    return dng


def build_World_from_str(worldStr):
    """
    Take in a string and create a new ``World`` from it.

    The string should be the output of the built-in ``repr`` function on a
    ``World`` object. As described in the documentation for the ``World`` object,
    each line of the string will be the representation of an individual object,
    NPC, or actor in the world, with the exception of the first line, which will
    indicate the dimensions of the world. This function reads that string line by
    line, adding the object represented on each line to the world. This results
    in a new ``World`` with identical objects and actors. Since the MIDCA cycles
    of the actors are decoupled from the ``World``, this method does *not* restore
    a simulation, just a ``World``.

    Arguments:
        ``worldStr``, *str*:
            The output of calling ``repr`` on a ``World`` object which should be
            recreated.

        ``return``, *World*:
            A ``World`` object such that calling ``repr`` on it would return a
            string equivalent to ``worldStr``.
    """
    lines = worldStr.split('\n')
    dim = int(lines[0][4:])
    dng = World(dim=dim)
    lines = lines[1:]
    objsMade = []
    while len(lines) > 0:
        line = lines.pop(0)
        if len(line) == 0:
            continue
        objCode = line[0]
        locIndex = line.index('@') + 1
        miscIndex = line.index(':') + 1 if ':' in line else len(line)

        objType = OBJECT_ID_CODES[objCode]
        location = get_point_from_str(line[locIndex:miscIndex-1])
        miscData = line[miscIndex:]

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
                # print("Couldn't find object reference {}".format(miscData))
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

        elif objType == NPC:
            living = miscData == "L"
            civi = line[1] == "C"
            objsMade.append(dng.place_object(NPC, location, civi=civi, living=living))

        elif objType in [AGENT, OPERATOR]:
            miscData = miscData.split(":")
            vision = int(miscData[0])
            name = miscData[1]
            objsMade.append(dng.add_user(name, location, vision, objType))
        else:
            raise NotImplementedError(objType)
    return dng


def build_World_from_file(filename, MIDCA=False):
    """
    Take in a text file and create a new World from it.

    Passes the text of the file into build_World_from_str. The file should use
    our own representation of a ``World`` (generated by calling ``repr``), not
    a MIDCA state, unless specified.

    *Note*: MIDCA state strings have not been updated in a while, and cannot
    account for everything now included in a ``World``.

    Arguments:
        ``filename``, *str*:
            The name of the file which contains the world's string.

        ``MIDCA``, *bool*:
            Indicates whether the input file contains a MIDCA state representation.
            Currently, loading a MIDCA state does not fully work, so this should
            always be ``False``.

        ``return``, *World*:
            The ``World`` object whose representation is stored in the file.
    """
    with open(filename, 'r') as dngFile:
        dngStr = dngFile.read()

    return build_World_from_str(dngStr)


def interactive_World_maker():
    """
    Allow a user to build a World from scratch.

    This function begins a loop which displays the current state of the new map,
    then asks the user for input. The user can add, remove, or modify objects and
    actors on the map or save the map. This function does not accept arguments,
    and only returns a boolean indicating execution success. In order to preserve
    the new world, the user must utilize the `save` command.

    Commands:
        ``set``:
            The ``set`` command allows the user to set object and actor attributes,
            and the general format looks like::

                set objID attrib newValue

            ``objID``:
                A valid ID code foran already-existing object or actor.

            ``attrib``:
                A valid attribute for the type of object or actor to which the ``objID``
                refers. Although this is somewhat sketchy, a valid attribute is anything
                in ``dir(targetObject)``.

            ``newValue``:
                The new value of the attribute, in a format which can be cast to the
                proper type for the attribute. If the attribute is a ``bool``, 'None',
                'f', 'F', 'false', 'False', and '0' all get cast to False.

        ``add``:
            The ``add`` command allows the user to add a new object or actor in the
            world. The general format looks like::

                add objType, location, miscData

            ``objType``:
                The object type string which corresponds to the desired object. The
                string for an object type is given by the object's eponymous constant.

            ``location``:
                The location to add the new object at, given as ``'(x, y)'`` such that
                the string can be converted to a point by :py:func:``~modules.world_utils.get_point_from_str``.

            ``miscData``:
                Any extra data needed to create the object. This is object-type specific.

        ``rem``:
            The ``rem`` command removes a specified object from the board completely.
            Note that this is irreversible. The general format looks like::

                rem objID

            ``objID``:
                A valid ID for the existing object which is to be removed.

        ``save``:
            The ``save`` command saves the current world to a file specified by the
            user in two different formats: a format unique to this domain, and a less
            powerful but more generalizable MIDCA state. The files will be saved in
            ``dng_files/``. The general format looks like::

                save filename

            ``filename``:
                The name of the file which the world should be saved to, **without**
                a file type extension at the end.

    Arguments:
        ``return``, *bool*:
            Indicates whether the world creation was successful or not.
    """
    def set_obj_attrib(target, attrib, val, objsMade):
        """Set the target attribute of the object to the given value, if possible."""
        if attrib not in dir(target):
            print("Object {} has no attribute {}".format(target, attrib))
            return False

        if attrib == 'location':
            val = get_point_from_str(val)
            target.location = val
            return True
        elif attrib in ['contains', 'unlocks']:
            if val in objsMade.keys():
                val = objsMade[val]
            else:
                print("Object code {} not made yet".format(val))
                return False
            target.__dict__[attrib] = val
            return True
        else:
            attribType = type(target.__dict__[attrib])
            if attribType is bool:
                val = False if val in ['None', 'f', 'F', 'false', 'False', '0'] else True
            target.__dict__[attrib] = attribType(val)
            return True

    def parse_command(cmd, dng, objsMade):
        """Parse a command and then execute it."""
        cmdData = cmd.split(' ')
        cmdAction = cmdData[0]

        if cmdAction == 'set':
            data = cmdData[1].lower()
            if data in objsMade.keys():
                objTarget = objsMade[data]
                attrib = cmdData[2].lower()
                value = cmdData[3]
                return set_obj_attrib(objTarget, attrib, value, objsMade)
            else:
                print("Unknown data {} for set command".format(data))
                return False

        elif cmdAction == 'add':
            objType = cmdData[1].upper()
            try:
                objLoc = get_point_from_str(cmdData[2])
            except ValueError:
                print("Problem converting location to point: not an int")
                return False
            if len(cmdData) == 4:
                miscData = cmdData[3]
            elif len(cmdData) >= 4:
                miscData = cmdData[3:]
            else:
                miscData = None

            if objType not in OBJECT_LIST:
                print("Unknown object type {}".format(objType))
            elif objType == WALL:
                newObj = dng.place_object(WALL, objLoc)
                objsMade[repr(newObj)] = newObj
                return True
            elif objType == DOOR:
                if not miscData:
                    newObj = dng.place_object(DOOR, objLoc)
                    objsMade[repr(newObj)] = newObj
                    return True
                elif miscData.lower() == 'true':
                    newObj = dng.place_object(DOOR, objLoc, locked=True)
                    objsMade[repr(newObj)] = newObj
                    return True
                elif miscData.lower() == 'false':
                    newObj = dng.place_object(DOOR, objLoc, locked=False)
                    objsMade[repr(newObj)] = newObj
                    return True
                else:
                    print("Unkown door lock status {}".format(miscData))
                    return False
            elif objType == CHEST:
                if not miscData:
                    newObj = dng.place_object(CHEST, objLoc)
                    objsMade[repr(newObj)] = newObj
                    return True
                miscData = " ".join(miscData)
                if miscData in objsMade.keys():
                    contains = objsMade[miscData]
                    if contains.objType not in [KEY, COIN]:
                        print("A chest can't hold a {}".format(contains.objType))
                        return False
                    newObj = dng.place_object(CHEST, objLoc, contains=contains)
                    objsMade[repr(newObj)] = newObj
                    return True
                else:
                    print("Object code {} is not made yet".format(miscData))
                    return False
            elif objType == KEY:
                if not miscData:
                    newObj = dng.place_object(KEY, objLoc)
                    objsMade[repr(newObj)] = newObj
                    return True
                miscData = " ".join(miscData)
                if miscData in objsMade.keys():
                    unlocks = objsMade[miscData]
                    if unlocks.objType not in [CHEST, DOOR]:
                        print("Object type {} can't be unlocked".format(unlocks.objType))
                        return False
                    newObj = dng.place_object(KEY, objLoc, unlocks=unlocks)
                    objsMade[repr(newObj)] = newObj
                    return True
                else:
                    print("Object code {} is not made yet".format(miscData))
                    return False
            elif objType == COIN:
                if not miscData:
                    print("Coin assigned value of 1")
                    value = 1
                else:
                    try:
                        value = int(miscData)
                    except ValueError:
                        print("Coin value must be an int, {} isn't".format(miscData))
                        return False

                newObj = dng.place_object(COIN, objLoc, value=value)
                objsMade[repr(newObj)] = newObj
                return True
            elif objType == FIRE:
                if not miscData:
                    print("Fire assigned damage of 3")
                    damage = 3
                else:
                    try:
                        damage = int(miscData)
                    except ValueError:
                        print("Damage needs to be an int, {} isn't".format(miscData))
                        return False

                newObj = dng.place_object(FIRE, objLoc, damage=damage)
                objsMade[repr(newObj)] = newObj
                return True
            elif objType == TRAP:
                if not miscData:
                    print("Trap assigned damage of 3")
                    damage = 3
                else:
                    try:
                        damage = int(miscData)
                    except ValueError:
                        print("Damage needs to be an int, {} isn't".format(miscData))
                        return False

                newObj = dng.place_object(TRAP, objLoc, damage=damage)
                objsMade[repr(newObj)] = newObj
                return True
            elif objType == NPC:
                if not miscData:
                    civi = False
                else:
                    civi = True if miscData.lower() in ['c', 'civi', 'civilian'] else False
                newObj = dng.place_object(NPC, objLoc, civi=civi)
                objsMade[repr(newObj)] = newObj
                return True
            elif objType in [AGENT, OPERATOR]:
                name = miscData[0]
                vision = int(miscData[1])
                newAgent = dng.add_user(name, objLoc, vision, objType)
                objsMade[repr(newAgent)] = newAgent
                return True
            else:
                print("Object type {} is not implemented yet".format(objType))
                return False

        elif cmdAction == 'rem':
            targetID = " ".join(cmdData[1:])
            if targetID not in objsMade.keys():
                print("Can't remove object {}, doesn't exist".format(targetID))
                return False
            dng.remove_object(targetID)
            del objsMade[targetID]
            return True

        elif cmdAction == 'save':
            return dng.save(cmdData[1])

        else:
            print("Command {} not implemented yet".format(cmdAction))
            return False

    dim = input("First, how big is the world? ")
    dng = World(dim)
    objsMade = {}
    while True:
        os.system('clear')
        print(str(dng))
        print("""Commands:
        \r\radd OBJTYPE POINT MISCDATA places an object at the given location
        \r\rset OBJID ATTRIBUTE VALUE changes the object's attribute
        \r\rrem OBJID removes the object with the given id
        \r\rsave FILENAME writes the World to the given file
        \r\rquit

        \r\rObject IDs:\n""")
        col = 1
        for objID in objsMade:
            if col % 4 == 0:
                col = 1
                print("{}".format(repr(objsMade[objID])))
            else:
                col += 1
                print "{}\t|\t".format(repr(objsMade[objID])),
        command = raw_input("\nCommand>> ")
        if command.lower() in ['q', 'quit']:
            print("Exiting world maker...")
            return True
        try:
            result = parse_command(command, dng, objsMade)
        except Exception as e:
            print("Couldn't complete command...")
            print(e)
            print(traceback.format_exc())
            result = False
        if not result:
            print("error thrown...")
            raw_input("Hit enter to continue...")


def get_point_from_str(string):
    """
    Convert a string of form '(x, y)' into a pair of ints.

    Arguments:

    ``string``, *str*:
        A string of form `'(x, y)'`, where `x` and `y` are able to be cast as
        ints by the `int` method.

    ``return``, *tuple*:
        A pair of ints which correspond to `x` and `y`.
    """
    coords = string.strip('()').split(',')
    point = (int(coords[0]), int(coords[1]))
    return point


def goal_from_str(string):
    """
    Convert goal string representation to a goal.

    Specifically, this function takes the result of ``str(goal)`` as input and
    returns ``Goal goal``.

    Note that each goal type needs to be custom added, so that the arguments for
    the new goal are converted to their proper types.

    Arguments:

    ``string``, *str*:
        String representation of a goal.

    ``returns``, *Goal*:
        The goal which the string represents.
    """
    args = []
    kwargs = {}
    strippedString = string[string.index("Goal")+4:].strip('()')
    dataStrs = strippedString.split(',')
    for dataStr in dataStrs:
        if ':' in dataStr:
            name, data = dataStr.split(':')
            name = name.strip()
            data = data.strip()
            kwargs[name] = data
        else:
            data = dataStr.strip()
            args.append(data)

    if kwargs['predicate'] == 'killed':
        resGoal = goals.Goal(args[0], predicate='killed', user=kwargs['user'])

    return resGoal


def goals_equal(goal1, goal2):
    """
    Indicate whether two goals are equal.

    Since the string form of a ``Goal`` includes all pertinent information and
    is predictable, this function compares the strings of the two ``Goal``
    objects to check for equivalence.

    Arguments:
        ``goal1``, *Goal*:
            The first of the two goals to check for equivalence.

        ``goal2``, *Goal*:
            The second of the two goals to check for equivalence.

        ``return``, *bool*:
            A boolean value indicating whether the two goals are equal.
    """
    return str(goal1) == str(goal2)


class DummyLog(object):
    """This is my greatest shame. Used to take the place of a log in a world map."""

    def info(self, val):
        pass


if __name__ == '__main__':
    dng = interactive_World_maker()
    # dng = build_World_from_file()
    # dng = generate_random_drone_demo(dim=25, civilians=15, enemies=30,
    #                                  operators=1, agents=5)
    # print(dng.status_display())
    # filename = raw_input("Save this as: ")
    # if filename != "":
    #     dng.save(filename)
