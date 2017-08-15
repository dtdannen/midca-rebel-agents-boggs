"""FILL THIS IN."""

# PYthon imports
import subprocess
import threading
from multiprocessing import Process
import time
import socket
import os
import logging
from copy import deepcopy
from itertools import product

# Rebel Agent Imports
import world_utils as wu
import world_methods as w_mthds
import world_operators as w_ops
from modules import perceive, interpret, evaluate, intend, plan, act
from MIDCA.modules import planning
import world_communications as wc


SERVER_ADDR = 'localhost'
SERVER_PORTS = range(9990, 10000)
LOG_MSG_FMT = "%(asctime)s:%(module)s:%(lineno)d: %(message)s"
LOG_DATE_FMT = "%M:%S"

DECLARE_METHODS_FUNC = w_mthds.declare_methods
DECLARE_OPERATORS_FUNC = w_ops.declare_operators
PLAN_VALIDATOR = plan.worldPlanValidator
VERBOSITY = 0
PHASES = ["Perceive", "Interpret", "Eval", "Intend", "Plan", "Act"]

AGENT_MODULES = {"Perceive":  [perceive.RemoteObserver],
                 "Interpret": [interpret.RemoteUserGoalInput,
                               interpret.CompletionEvaluator,
                               interpret.StateDiscrepancyDetector,
                               interpret.GoalValidityChecker,
                               interpret.DiscrepancyExplainer,
                               interpret.GoalRecognition],
                 "Eval":      [evaluate.GoalManager,
                               evaluate.HandleRebellion,
                               evaluate.ProactiveRebellion
                               ],
                 "Intend":    [intend.QuickIntend],
                 "Plan":      [plan.GenericPyhopPlanner],
                 "Act":       [act.SimpleAct]
                 }
AUTO_OP_MODULES = {"Perceive": [perceive.OperatorObserver],
                   "Interpret": [interpret.OperatorInterpret],
                   "Eval": [evaluate.OperatorHandleRebelsStochastic],
                   "Intend": [],
                   "Plan": [plan.OperatorPlanGoals],
                   "Act": [act.OperatorGiveGoals]
                   }


def generate_agent_modules(agtID, rebel=True, compliance=1.0):
    """Create a dictionary of MIDCA module objects to use for an agent."""
    modules = dict([(p, []) for p in PHASES])

    logger = logging.getLogger(agtID)
    if not logger.isEnabledFor(logging.DEBUG):
        logger.setLevel(logging.DEBUG)

        logFile = os.getcwd() + "/logs/{}.log".format(agtID)
        handler = logging.FileHandler(logFile, mode='w')
        handler.setLevel(logging.INFO)

        formatter = logging.Formatter(fmt=LOG_MSG_FMT, datefmt=LOG_DATE_FMT)
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    for phase in PHASES:
        for modInit in AGENT_MODULES[phase]:
            if modInit == evaluate.HandleRebellion:
                if not rebel:
                    # Don't add the handle rebellion module if we don't want rebelling
                    continue
                modules[phase].append(modInit(logger=logger, compliance=compliance))
                continue

            if modInit == plan.GenericPyhopPlanner:
                # Have to add special stuff for the pyhop planner
                modules[phase].append(modInit(DECLARE_METHODS_FUNC,
                                              DECLARE_OPERATORS_FUNC,
                                              PLAN_VALIDATOR,
                                              verbose=VERBOSITY)
                                      )
                continue

            modules[phase].append(modInit(logger=logger))
    return modules


def generate_optr_modules(opID, rejectionProb=0.0):
    """Create a dictionary of MIDCA module objects to use for an agent."""
    modules = dict([(p, []) for p in PHASES])

    logger = logging.getLogger(opID)

    if not logger.isEnabledFor(logging.DEBUG):
        logger.setLevel(logging.DEBUG)

        logFile = os.getcwd() + "/logs/{}.log".format(opID)
        handler = logging.FileHandler(logFile, mode='w')
        handler.setLevel(logging.INFO)

        formatter = logging.Formatter(fmt=LOG_MSG_FMT, datefmt=LOG_DATE_FMT)
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    for phase in PHASES:
        for modInit in AUTO_OP_MODULES[phase]:
            if modInit == evaluate.OperatorHandleRebelsStochastic:
                modules[phase].append(modInit(rejectionProb=rejectionProb,
                                              logger=logger))
                continue

            modules[phase].append(modInit(logger=logger))
    return modules


def run_visible_test(world, limit=500):
    """
    Run a test using the given world for the given time, then record the results.
    """
    score = [0, 0]
    serverExists = False
    for port in SERVER_PORTS:
        try:
            server = wc.WorldServer((SERVER_ADDR, port), world, score, limit=limit)
            serverThread = threading.Thread(target=server.serve_forever)
            serverThread.start()
            time.sleep(1)
            serverExists = True
            break
        except socket.error:
            continue
    if not serverExists:
        raise Exception("Server wasn't open, code failing")

    operators = world.operators
    agents = world.agents

    opProcesses = []
    for op in operators:
        outFileName = "logs/{}-Log.txt".format(op.id)
        client_args = ["python", "./world_communications.py",
                       "operator", str(port), op.id,
                       ">", outFileName, "; sleep 5"]
        op_call = ["xterm", "-e", " ".join(client_args)]
        opProcesses.append(subprocess.Popen(op_call))

    agtProcesses = []
    for agt in agents:
        outFileName = "logs/{}-Log.txt".format(agt.id)
        client_args = ["python", "./world_communications.py",
                       "agent", str(port), agt.id,
                       "> ", outFileName, "; sleep 5"]
        agt_call = ["xterm", "-e", " ".join(client_args)]
        agtProcesses.append(subprocess.Popen(agt_call))

    serverThread.join()

    for op in opProcesses:
        op.terminate()
    for agt in agtProcesses:
        agt.terminate()

    return score


def run_test(world, limit=60, rebel=True, rejectionProb=0.0, compliance=1.0):
    """
    Run a test using the given world, agent, and operator, then record the results.
    """
    score = [0, 0]
    serverExists = False
    for port in SERVER_PORTS:
        try:
            server = wc.WorldServer((SERVER_ADDR, port), world, score, limit=limit)
            serverThread = threading.Thread(target=server.serve_forever)
            serverThread.start()
            time.sleep(1)
            serverExists = True
            break
        except socket.error:
            continue
    if not serverExists:
        raise Exception("Server wasn't open, code failing")

    operators = world.operators
    agents = world.agents

    optrThreads = []
    for op in operators:
        opModules = generate_optr_modules(op.id, rejectionProb)
        optr = wc.AutoOperator(SERVER_ADDR, port, op.id, opModules)
        optrThread = Process(target=optr.run)
        optrThreads.append(optrThread)

    agtThreads = []
    for agt in agents:
        agentModules = generate_agent_modules(agt.id, rebel, compliance)
        newAgt = wc.RemoteAgent(SERVER_ADDR, port, agt.id, agentModules)
        agtThread = Process(target=newAgt.run)
        agtThreads.append(agtThread)

    for optrThread in optrThreads:
        optrThread.start()
    for agtThread in agtThreads:
        agtThread.start()

    serverThread.join()

    for op in optrThreads:
        op.terminate()
    for agt in agtThreads:
        agt.terminate()

    return score


class Testbed(object):
    """
    Allows for the execution of a widely-configurable series of tests.

    The ``Testbed`` class allows a user to pre-configure a series of tests and
    then run them reaptedly and extract results. When a user instantiates a
    ``Testbed``, they can specify parameters which will dictate the way tests
    will be generated and run. Many parameters accept both a single object of
    a certain type or a list of objects of that type. If such a parameter receives
    a list, then it will run a test for each of those parameters. If there are
    multiple such lists, every permutation will be run.

    The number of civilians and enemies can be set in two ways. First, the user
    can directly specify a number or a list of numbers for each parameter, as
    normal. Second, the user can specify the ratio of NPCs to the size of the
    board and the ratio of civilians to enemies, so that the number of civilians
    and enemies changes with the size of the board. If a ratio is set, then the
    ratio will take precedence over the normal paramters.

    Arguments:
        ``worldSize = 10``, *int* or *list*:
            This dictates the size of the worlds created for testing.

        ``civilians = 10``, *int* or *list*:
            This dictates how many civilians will be randomly placed on each new
            world generated for testing. If this number is less than 0, it
            indicates that the number of civilians should be determined by other
            parameters. If that is the case, ``civiEnemyRatio`` *must* be
            greater than 0.

        ``enemies = 10``, *int* or *list*:
            This dictates how many enemies will be randomly placed on each new
            world generated for testing. If this number is less than 0, it
            indicates that the number of enemies should be determined by other
            parameters. If that is the case, ``NPCSizeRatio`` *must* be greater
            than 0.

        ``agents = [0.0, 0.0, 0.0, 0.0, 0.0]``, *list*:
            This dictates how many agents will be randomly placed on each new
            world generated for testing, and what their compliance level will be.
            For each value in the list, a new agent is created with a compliance
            level of the value. This can also be a list of such lists.

        ``operators = [1.0]``, *list*:
            This dictates how many operators will be randomly placed on each new
            world generated for testing, and what their flexibility level will be.
            For each value in the list a new operator is created with a flexibility
            level of that value. This can also be a list of such lists.

        ``civiEnemyRatio = -1.0``, *float* or *list*:
            This dictates the ratio of civilians to enemies, such that a ratio of
            0.5 means 1 civilian per 2 enemies, and a ratio of 0.0 means no
            civilians. If this value is less than 0, the number of civilians and
            enemies placed on the board is based on their respective parameters.
            If that is the case, ``civilians`` *must* be greater than 0.

        ``NPCSizeRatio = -1.0``, *float* or *list*:
            This dictates the ratio between the number of NPCs and the size of
            the board, such that a ratio of 0.5 means that half of all tiles
            contain an NPC. If the value is negative, the number of NPCs is
            determined by their respective parameters. If that is the case,
            ``enemies`` must be greater than 0.

        ``visionRange = (1, 3)``, *pair* or *list*:
            This dictates the minimum and maximum distance an agent or operator
            can see. When a new agent or operator is placed in the world, its
            vision is randomly chosen between the two numbers in the pair.

        ``bombRange = 2``, *int* or *list*:
            This dictates the blast radius of the bombs in a test.

        ``rebel = True``, *bool* or *list*:
            This dictates whether agents will rebel against goals.

        ``agentsRandomPosition = False``, *bool*:
            This dictates whether the positions of agents on a board is reset
            every test, even if the map is the same. If this is true, the world
            is altered prior to testing to randomly move the agents on it.

        ``mapStatic = False``, *bool*:
            This dictates whether a new map is created for every test, or if a
            single world is created at the beginning and used for every subsequent
            test. If the map is static, then the size of the map along with the
            number of NPCs must also be static. If a single value is given for
            those parameters, it will be used. If a list is given, only the first
            element in the list will be used.

        ``runsPerTest = 3``, *int*:
            This dictates how many times each combination of parameters is
            tested.

        ``timeLimit = 60``, *int*:
            This dictates how many seconds each run of a test goes.

    """

    def __init__(self, worldSize=10, civilians=10, enemies=10, agents=[0.0]*5,
                 operators=[1.0], civiEnemyRatio=-1.0, NPCSizeRatio=-1.0,
                 visionRange=(1, 3), bombRange=2, rebel=True,
                 agentsRandomPosition=False, mapStatic=False, runsPerTest=3,
                 world=None, timeLimit=60):
        # Store parameters
        self.worldSizeList = self.__handle_parameter(worldSize)
        self.NPCSizeRatioList = self.__handle_parameter(NPCSizeRatio)
        self.civiEnemyRatioList = self.__handle_parameter(civiEnemyRatio)
        self.enemiesList = self.__handle_parameter(enemies)
        self.civiliansList = self.__handle_parameter(civilians)
        self.agentsList = agents
        self.operatorsList = operators
        self.visionRangeList = self.__handle_parameter(visionRange)
        self.bombRangeList = self.__handle_parameter(bombRange)
        self.rebelList = self.__handle_parameter(rebel)
        self.agentsRandomPosition = agentsRandomPosition
        self.mapStatic = mapStatic
        self.runsPerTest = runsPerTest
        self.timeLimit = timeLimit

        # Set up logger
        self.log = logging.getLogger("testLog")
        hdlr = logging.FileHandler("logs/testLog.log", mode="w")
        fmtr = logging.Formatter(fmt=LOG_MSG_FMT, datefmt=LOG_DATE_FMT)
        hdlr.setLevel(logging.INFO)
        hdlr.setFormatter(fmtr)
        self.log.addHandler(hdlr)
        self.log.setLevel(logging.INFO)

        # Create or store world, if necessary
        if self.mapStatic:
            if world:
                self.world = world
            else:
                self.world = wu.generate_random_drone_demo(dim=self.worldSizeList[0],
                                                           civilians=self.civilians[0],
                                                           enemies=self.enemies[0],
                                                           operators=len(self.operators[0]),
                                                           agents=len(self.agents[0]),
                                                           visionRange=self.visionRange[0],
                                                           bombRange=self.bombRange[0],
                                                           log=self.log)
        else:
            self.world = None

        self.testList = self.generate_tests()

    def generate_tests(self):
        """
        Create all the ``Test`` objects necessary to test the parameters.

        Each possible unique combination of parameters is turned into a ``Test``
        object, which can be run some number of times.

        Arguments:
            ``return``, *list*:
                A list of unique ``Test`` generated from each possible unique
                combination of the paramters given to this object at instantiation.
        """
        tests = []
        permutations = product(self.worldSizeList, self.NPCSizeRatioList,
                               self.civiEnemyRatioList, self.enemiesList,
                               self.civiliansList, self.agentsList,
                               self.operatorsList, self.visionRangeList,
                               self.bombRangeList, self.rebelList
                               )

        for perm in permutations:
            print("permutation: {}".format(perm))
            tests.append(self.generate_test(perm))

        return tests

    def generate_test(self, permutation):
        """
        Generate a single ``Test`` object from a permutation of given parameters.

        This function takes in a permutation of the paramter lists the ``Testbed``
        was initialized with and returns a ``Test`` object corresponding to that
        permutation. That is, the returned ``Test`` object, when run, will simulate
        a world with parameters equal to those of the given permutation. This
        function takes into account the NPCSizeRatio and civiEnemyRatio parameters,
        so that the number of civilians and enemies is set properly.

        Arguments:
            ``permutation``, *list*:
                A list of parameter values, so that each element is the value
                of the corresponding paramter in the list below:

                worldSize = permutation[0]
                NPCSizeRatio = permutation[1]
                civiEnemyRatio = permutation[2]
                enemies = permutation[3]
                civilians = permutation[4]
                agents = permutation[5]
                operators = permutation[6]
                visionRange = permutation[7]
                bombRange = permutation[8]
                rebel = permutation[9]

            ``return``, *Test*:
                A ``Test`` object created with the appropriate parameters.
        """
        worldSize = permutation[0]
        NPCSizeRatio = permutation[1]
        civiEnemyRatio = permutation[2]
        enemies = permutation[3]
        civilians = permutation[4]
        agents = permutation[5]
        operators = permutation[6]
        visionRange = permutation[7]
        bombRange = permutation[8]
        rebel = permutation[9]

        # Determine the number of civilians and enemies if ratios are set
        if NPCSizeRatio > 0:
            assert NPCSizeRatio <= 1.0, "NPCSizeRatio must be between 0 and 1"
            NPCNum = int((worldSize**2) * NPCSizeRatio)
            if civiEnemyRatio >= 0:
                assert civiEnemyRatio <= 1.0, "civiEnemyRatio must be between 0 and 1"
                enemies = int(NPCNum/(1.0 + civiEnemyRatio))
                civilians = NPCNum - enemies
            elif enemies >= 0 and civilians < 0:
                civilians = NPCNum - enemies
            elif civilians >= 0 and enemies < 0:
                enemies = NPCNum - civilians
            elif civilians >= 0 and enemies >= 0:
                assert enemies + civilians == NPCNum, "enemy and civilian counts must equal NPCNum"
            raise Exception("Not enough parameters set, NPCSizeRatio is the only one")
        elif civiEnemyRatio > 0:
            assert civiEnemyRatio <= 1.0, "civiEnemyRatio must be between 0 and 1"
            assert enemies > 0, "using civiEnemyRatio requires enemies to be set"
            civilians = int(civiEnemyRatio * enemies)

        newTest = Test(log=self.log, worldSize=worldSize,
                       civilians=civilians, enemies=enemies,
                       agents=agents, operators=operators,
                       visionRange=visionRange, bombRange=bombRange,
                       rebel=rebel, runs=self.runsPerTest,
                       agentsRandomPosition=self.agentsRandomPosition,
                       world=self.world, timeLimit=self.timeLimit
                       )

        return newTest

    def run_tests(self):
        """Run each of the ``Test`` objects in ``self.testList``."""
        results = {}
        for test in self.testList:
            results[str(test.parameters)] = test.run_tests()

        return results

    def __handle_parameter(self, parameter):
        """Turn a parameter into a list if necessary."""
        if not isinstance(parameter, list):
            return [parameter]
        else:
            return parameter


class Test(object):
    """Abstracts a single test, which can be run multiple times."""

    def __init__(self, log, worldSize=10, civilians=10, enemies=10, agents=[0.0]*5,
                 operators=[1.0], visionRange=(1, 3), bombRange=2, rebel=True,
                 runs=3, agentsRandomPosition=False, world=None, timeLimit=60):
        self.log = log
        self.worldSize = worldSize
        self.civilians = civilians
        self.enemies = enemies
        self.agents = agents
        self.operators = operators
        self.visionRange = visionRange
        self.bombRange = bombRange
        self.runs = runs
        self.agentsRandomPosition = agentsRandomPosition
        self.world = world
        self.rebel = rebel
        self.limit = timeLimit

        self.testWorlds = self.create_test_worlds(runs)

    @property
    def parameters(self):
        return {'worldSize': self.worldSize,
                'civilians': self.civilians,
                'enemies': self.enemies,
                'agents': self.agents,
                'operators': self.operators,
                'visionRange': self.visionRange,
                'bombRange': self.bombRange,
                'rebel': self.rebel,
                'agentsRandomPosition': self.agentsRandomPosition,
                }

    def create_test_worlds(self, num):
        """
        Create ``num`` new ``World``s to simulate.

        The function creates a list of separate``World`` objects, each of which
        will be simulated once. If a ``World`` was passed in the creation of the
        ``Test``, it will be ``deepcopy``d the appropriate number of times. If
        the agents and operators should be moved, each will do so. If no ``World``
        was passed in, then the appropriate number of ``World``s will be generated
        randomly with the parameters passed to the ``Test`` object.

        Arguments:
            ``num``, *int*:
                The number of ``World``s to create.

            ``return``, *list*:
                A list of ``num`` ``World``s.
        """
        # Create a list of worlds to run a simulation on, equal in number to
        # the number of runs given.
        testWorlds = []
        # If a world is given, duplicate it ``run`` times, shuffling actors if
        # needed.
        if self.world:
            for i in range(self.runs):
                testWorld = deepcopy(self.world)
                if self.agentsRandomPosition:
                    testWorld = testWorld.shuffle_actors()
                testWorlds.append(testWorld)
        # Otherwise, randomly generate ``runs`` new worlds with the appropriate
        # number of NPCs and actors.
        else:
            for i in range(self.runs):
                testWorld = wu.generate_random_drone_demo(dim=self.worldSize,
                                                          civilians=self.civilians,
                                                          enemies=self.enemies,
                                                          operators=len(self.operators),
                                                          agents=len(self.agents),
                                                          visionRange=self.visionRange,
                                                          bombRange=self.bombRange,
                                                          log=self.log)
                testWorlds.append(testWorld)
        return testWorlds

    def log_test_info(self, world):
        """Write info about the current test to the log."""
        self.log.info("World:\n{}".format(world))
        self.log.info("Parameters:")
        self.log.info("World Size: {}".format(self.worldSize))
        self.log.info("Civilians: {}".format(self.civilians))
        self.log.info("Enemies: {}".format(self.enemies))
        self.log.info("Agents: {}".format(self.agents))
        self.log.info("Operators: {}".format(self.operators))
        self.log.info("Vision Range: {}".format(self.visionRange))
        self.log.info("Bomb Range: {}".format(self.bombRange))

    def run_tests(self):
        """
        Run the test by simulating each test world for the time limit.

        Prior to each run of the test, information about the test parameters and
        the test world are logged. The runs use the agent and operator personalities
        given to the ``Test`` object to run agent and operator MIDCA cycles.
        """
        results = []
        self.log.info("Starting tests")
        for i in range(self.runs):
            testWorld = self.testWorlds[i]
            self.log.info("Test {}".format(i+1))
            self.log_test_info(testWorld)
            results.append(self.run_test(testWorld))
        return results

    def run_test(self, world):
        """
        Run a test using the given world then return the results.

        This function runs an individual test on a specified world, using the
        agent and operator personalities given to the ``Test`` object. It uses
        threading to run every aspect of the test simultaneous, and *should*
        return a score value.
        """
        score = [0, 0]
        serverExists = False
        for port in SERVER_PORTS:
            try:
                server = wc.WorldServer((SERVER_ADDR, port),
                                        world, score, limit=self.limit)
                serverThread = threading.Thread(target=server.serve_forever)
                serverThread.start()
                time.sleep(1)
                serverExists = True
                break
            except socket.error:
                continue
        if not serverExists:
            raise Exception("Server wasn't open, code failing")

        operators = world.operators
        agents = world.agents

        if len(operators) != len(self.operators) or len(agents) != len(self.agents):
            raise Exception("Mismatch between map actor count and test actor count")

        optrThreads = []
        optrIndex = 0
        for op in operators:
            opModules = generate_optr_modules(op.id, self.operators[optrIndex])
            optr = wc.AutoOperator(SERVER_ADDR, port, op.id, opModules)
            optrThread = Process(target=optr.run)
            optrThreads.append(optrThread)
            optrIndex += 1

        agtThreads = []
        agtIndex = 0
        for agt in agents:
            agentModules = generate_agent_modules(agt.id, self.rebel, self.agents[agtIndex])
            newAgt = wc.RemoteAgent(SERVER_ADDR, port, agt.id, agentModules)
            agtThread = Process(target=newAgt.run)
            agtThreads.append(agtThread)
            agtIndex += 1

        for optrThread in optrThreads:
            optrThread.start()
        for agtThread in agtThreads:
            agtThread.start()

        serverThread.join()

        for op in optrThreads:
            op.terminate()
        for agt in agtThreads:
            agt.terminate()

        return score


if __name__ == '__main__':
    tBed = Testbed(agents=[[0.0]*5, [1.0]*5],
                   operators=[[0.0], [1.0]],
                   visionRange=[(2, 4), (1, 3)],
                   worldSize=20,
                   runsPerTest=4)
    result = tBed.run_tests()
    print(result)
