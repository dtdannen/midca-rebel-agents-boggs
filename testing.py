#/usr/bin/python
"""
This module contains all of the code used easy testing, including the
:py:class:`~testing.Testbed` class, which serves as the primary vehicle for
performing batches of tests.

The ultimate goal of this module is to provide easy and modular testing for our
rebel agent code. The :py:class:`~testing.Testbed` class is the solution we
developed, and allows the user to set the values of several different parameters
for testing. As explained in the :ref:`user-guide-results` section of the
:ref:`user-guide`, we can build batches of tests by creating a :py:class:`~testing.Testbed`
class with the values of the parameters we want. The parameters and their meanings
are listed both in the documentation of the :py:class:`~testing.Testbed` class
and in the :ref:`user-guide-demo-params` subsection of the :ref:`user-guide`.
"""
import subprocess
import threading
from multiprocessing import Process
import time
import socket
import os
import logging
from json import dumps
from itertools import product
from collections import namedtuple
import csv
import cPickle
import world_utils as wu
import world_methods as w_mthds
import world_operators as w_ops
from modules import perceive, interpret, evaluate, intend, plan, act
import world_communications as wc
SERVER_ADDR = 'localhost'
SERVER_PORTS = range(9990, 10000)
LOG_MSG_FMT = '%(asctime)s:%(module)s:%(lineno)d: %(message)s'
LOG_DATE_FMT = '%M:%S'
DECLARE_METHODS_FUNC = w_mthds.declare_methods
DECLARE_OPERATORS_FUNC = w_ops.declare_operators
PLAN_VALIDATOR = plan.worldPlanValidator
VERBOSITY = 0
PHASES = ['Perceive', 'Interpret', 'Eval', 'Intend', 'Plan', 'Act']
AGENT_MODULES = {'Perceive': [perceive.RemoteObserver],'Interpret': [
               interpret.RemoteUserGoalInput,
               interpret.CompletionEvaluator,
               interpret.StateDiscrepancyDetector,
               interpret.GoalValidityChecker,
               interpret.DiscrepancyExplainer,
               interpret.GoalRecognition],
   'Eval': [
          evaluate.GoalManager,
          evaluate.HandleRebellion,
          evaluate.ProactiveRebellion],
   'Intend': [
            intend.QuickIntend],
   'Plan': [
          plan.GenericPyhopPlanner],
   'Act': [
         act.SimpleAct]
   }
AUTO_OP_MODULES = {'Perceive': [perceive.OperatorObserver],'Interpret': [
               interpret.OperatorInterpret],
   'Eval': [
          evaluate.OperatorHandleRebelsStochastic],
   'Intend': [],'Plan': [
          plan.OperatorPlanGoals],
   'Act': [
         act.OperatorGiveGoals]
   }
PARAM_NAMES = [
 'worldSize', 'civilians', 'enemies', 'agents',
 'operators', 'visionRange', 'bombRange',
 'rebel', 'proacRebel', 'agentsRandomPosition']
Parameters = namedtuple('Parameters', PARAM_NAMES)

def generate_agent_modules(agtID, rebel=True, proacRebel=True, compliance=1.0):
    """Create a dictionary of MIDCA module objects to use for an agent."""
    modules = dict([ (p, []) for p in PHASES ])
    logger = logging.getLogger(agtID)
    if not logger.isEnabledFor(logging.DEBUG):
        logger.setLevel(logging.DEBUG)
        logFile = os.getcwd() + '/logs/{}.log'.format(agtID)
        handler = logging.FileHandler(logFile, mode='w')
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter(fmt=LOG_MSG_FMT, datefmt=LOG_DATE_FMT)
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    for phase in PHASES:
        for modInit in AGENT_MODULES[phase]:
            if modInit == evaluate.HandleRebellion:
                if not rebel:
                    continue
                modules[phase].append(modInit(logger=logger, compliance=compliance))
                continue
            if modInit == evaluate.ProactiveRebellion:
                if not proacRebel:
                    continue
            if modInit == plan.GenericPyhopPlanner:
                modules[phase].append(modInit(DECLARE_METHODS_FUNC, DECLARE_OPERATORS_FUNC, PLAN_VALIDATOR, verbose=VERBOSITY))
                continue
            modules[phase].append(modInit(logger=logger))

    return modules


def generate_optr_modules(opID, rejectionProb=0.0):
    """Create a dictionary of MIDCA module objects to use for an agent."""
    modules = dict([ (p, []) for p in PHASES ])
    logger = logging.getLogger(opID)
    if not logger.isEnabledFor(logging.DEBUG):
        logger.setLevel(logging.DEBUG)
        logFile = os.getcwd() + '/logs/{}.log'.format(opID)
        handler = logging.FileHandler(logFile, mode='w')
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter(fmt=LOG_MSG_FMT, datefmt=LOG_DATE_FMT)
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    for phase in PHASES:
        for modInit in AUTO_OP_MODULES[phase]:
            if modInit == evaluate.OperatorHandleRebelsStochastic:
                modules[phase].append(modInit(rejectionProb=rejectionProb, logger=logger))
                continue
            modules[phase].append(modInit(logger=logger))

    return modules


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

        ``agents = (0.0, 0.0, 0.0, 0.0, 0.0)``, *tuple* or *list*:
            This dictates how many agents will be randomly placed on each new
            world generated for testing, and what their compliance level will be.
            For each value in the tuple, a new agent is created with a compliance
            level of the value.

        ``operators = (1.0)``, *tuple* or *list*:
            This dictates how many operators will be randomly placed on each new
            world generated for testing, and what their flexibility level will be.
            For each value in the tuple a new operator is created with a flexibility
            level of that value.

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
            ``enemies`` must be greater than 0. If the number of NPCs required
            by this parameter is greater than the number of tiles available, it
            will just fill all available tiles.

        ``visionRange = (1, 3)``, *pair* or *list*:
            This dictates the minimum and maximum distance an agent or operator
            can see. When a new agent or operator is placed in the world, its
            vision is randomly chosen between the two numbers in the pair.

        ``bombRange = 2``, *int* or *list*:
            This dictates the blast radius of the bombs in a test.

        ``rebel = (True, True, True, True, True)``, *tuple* or *list*:
            This dictates whether each agent will rebel against goals.

        ``proacRebel = (True, True, True, True, True)``, *tuple8 or *list*:
            This dictates whether agents will initiate proactive rebellions.

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

        ``world = None``, *World* or *list*:
            If the tests should be run on a pre-generated world, pass that world
            through this parameter. If ``world`` is not ``None``, then any parameter
            dealing with the creation of a ``World`` (e.g. ``agents``, ``civilians``,
            etc.) is ignored.

        ``timeLimit = 60``, *int*:
            This dictates how many seconds each run of a test goes.
    """

    def __init__(self, worldSize=10, civilians=10, enemies=10,
                 agents=(0.0, 0.0, 0.0, 0.0, 0.0), operators=(1.0, ),
                 civiEnemyRatio=-1.0, NPCSizeRatio=-1.0, visionRange=(1, 3),
                 bombRange=2, rebel=(True,) * 5, proacRebel=(True,) * 5,
                 agentsRandomPosition=False, mapStatic=False, runsPerTest=3,
                 world=None, timeLimit=60):
        """Instantiate a new Testbed with the given parameters."""
        self.worldSizeList = self.__handle_parameter(worldSize)
        self.NPCSizeRatioList = self.__handle_parameter(NPCSizeRatio)
        self.civiEnemyRatioList = self.__handle_parameter(civiEnemyRatio)
        self.enemiesList = self.__handle_parameter(enemies)
        self.civiliansList = self.__handle_parameter(civilians)
        self.agentsList = self.__handle_parameter(agents)
        self.operatorsList = self.__handle_parameter(operators)
        self.visionRangeList = self.__handle_parameter(visionRange)
        self.bombRangeList = self.__handle_parameter(bombRange)
        self.rebelList = self.__handle_parameter(rebel)
        self.proacRebelList = self.__handle_parameter(proacRebel)
        self.worldList = self.__handle_parameter(world)
        self.world = world
        self.agentsRandomPosition = agentsRandomPosition
        self.mapStatic = mapStatic
        self.runsPerTest = runsPerTest
        self.timeLimit = timeLimit
        self.log = logging.getLogger('testLog')
        hdlr = logging.FileHandler('logs/testLog.log', mode='w')
        fmtr = logging.Formatter(fmt=LOG_MSG_FMT, datefmt=LOG_DATE_FMT)
        hdlr.setLevel(logging.INFO)
        hdlr.setFormatter(fmtr)
        self.log.addHandler(hdlr)
        self.log.setLevel(logging.INFO)
        if self.mapStatic:
            if self.worldList[0]:
                self.worldList = [self.worldList[0]]
            else:
                world = wu.generate_random_drone_demo(dim=self.worldSizeList[0],
                                                      civilians=self.civilians[0],
                                                      enemies=self.enemies[0],
                                                      operators=len(self.operators[0]),
                                                      agents=len(self.agents[0]),
                                                      visionRange=self.visionRange[0],
                                                      bombRange=self.bombRange[0],
                                                      log=self.log)
                self.worldList = [world]
        else:
            self.world = None
        self.testList = self.generate_tests()
        self.testRecords = TestRecords()
        return

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
                               self.bombRangeList, self.rebelList,
                               self.proacRebelList, self.worldList)
        for perm in permutations:
            print 'permutation: {}'.format(perm)
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
        proacRebel = permutation[10]
        if NPCSizeRatio > 0:
            assert NPCSizeRatio <= 1.0, 'NPCSizeRatio must be between 0 and 1'
            NPCNum = int(worldSize ** 2 * NPCSizeRatio)
            if civiEnemyRatio >= 0:
                enemies = int(NPCNum / (1.0 + civiEnemyRatio))
                civilians = NPCNum - enemies
            elif enemies >= 0 and civilians < 0:
                civilians = NPCNum - enemies
            elif civilians >= 0 and enemies < 0:
                enemies = NPCNum - civilians
            elif civilians >= 0 and enemies >= 0:
                assert enemies + civilians == NPCNum, 'enemy and civilian counts must equal NPCNum'
            else:
                raise Exception('Not enough parameters set, NPCSizeRatio is the only one')
        elif civiEnemyRatio > 0:
            assert enemies > 0, 'using civiEnemyRatio requires enemies to be set'
            civilians = int(civiEnemyRatio * enemies)
        newTest = Test(log=self.log, worldSize=worldSize, civilians=civilians, enemies=enemies, agents=agents, operators=operators, visionRange=visionRange, bombRange=bombRange, rebel=rebel, proacRebel=proacRebel, runs=self.runsPerTest, agentsRandomPosition=self.agentsRandomPosition, world=self.world, timeLimit=self.timeLimit)
        return newTest

    def run_tests(self):
        """Run each of the ``Test`` objects in ``self.testList``."""
        results = None
        for test in self.testList:
            results = test.run_tests()
            if test.parameters in self.testRecords:
                self.testRecords[test.parameters].append(results)
            else:
                self.testRecords[test.parameters] = results

        return results

    def __handle_parameter(self, parameter):
        """Turn a parameter into a list if necessary."""
        if not isinstance(parameter, list):
            return [parameter]
        else:
            return parameter


class Test(object):
    """
    Represents a single test with certain parameters and can be run multiple times.

    The ``Test`` object abstracts the idea of a test of rebel agents in the drone
    domain, containing the parameters to be tested and allowing the user to run
    any number of tests with the given parameters. This allows random generation
    of maps fitted to the parameters each time, the generation of a single map
    test many times, or even passing in a map to test with certain agent or
    operator personalities.

    Arguments:
        ``log``, *Logger*:
            A python ``logging.Logger`` object which will be used to record the
            results of running the test.

        ``worldSize = 10``, *int*:
            This dictates the size of the worlds created for testing.

        ``civilians = 10``, *int*:
            This dictates how many civilians will be randomly placed on each new
            world generated for testing.

        ``enemies = 10``, *int*:
            This dictates how many enemies will be randomly placed on each new
            world generated for testing.

        ``agents = [0.0, 0.0, 0.0, 0.0, 0.0]``, *list*:
            This dictates how many agents will be randomly placed on each new
            world generated for testing, and what their compliance level will be.
            For each value in the list, a new agent is created with a compliance
            level of the value.

        ``operators = [1.0]``, *list*:
            This dictates how many operators will be randomly placed on each new
            world generated for testing, and what their flexibility level will be.
            For each value in the list a new operator is created with a flexibility
            level of that value.

        ``visionRange = (1, 3)``, *pair*:
            This dictates the minimum and maximum distance an agent or operator
            can see. When a new agent or operator is placed in the world, its
            vision is randomly chosen between the two numbers in the pair.

        ``bombRange = 2``, *int*:
            This dictates the blast radius of the bombs in a test.

        ``rebel = [True, True, True, True, True]``, *list*:
            This dictates whether each agent will rebel against goals.

        ``proacRebel = [True, True, True, True, True]``, *list*:
            This dictates whether the agent will initiate proactive rebellions.

        ``runs = 3``, *int*:
            The number of times to run simulations with the ``Test``'s parameters.
            This fixes the number of times the ``Test`` object can run simulations,
            because only a number of  ``World`` objects equal to this paramter are
            created for testing.

        ``agentsRandomPosition = False``, *bool*:
            This dictates whether the positions of agents on a board is reset
            every test, even if the map is the same. If this is true, the world
            is altered prior to testing to randomly move the agents on it.

        ``world = None``, *World*:
            If the tests should be run on a pre-generated world, pass that world
            through this parameter. If ``world`` is not ``None``, then any parameter
            dealing with the creation of a ``World`` (e.g. ``agents``, ``civilians``,
            etc.) is ignored.

        ``timeLimit = 60``, *int*:
            This dictates how many seconds each run of a test goes.
    """

    def __init__(self, log, worldSize=10, civilians=10, enemies=10,
                 agents=(0.0, 0.0, 0.0, 0.0, 0.0), operators=1.0,
                 visionRange=(1, 3), bombRange=2, rebel=(True,) * 5,
                 proacRebel=(True,) * 5, runs=3, agentsRandomPosition=False,
                 world=None, timeLimit=60):
        """Instantiate a ``Test`` object with the given paramters."""
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
        self.proacRebel = proacRebel
        self.limit = timeLimit
        self.testWorlds = self.create_test_worlds(runs)

    @property
    def parameters(self):
        """Return a ``dict`` with the ``Test``'s parameters."""
        paramVals = (
         self.worldSize, self.civilians, self.enemies, self.agents,
         self.operators, self.visionRange, self.bombRange,
         self.rebel, self.proacRebel, self.agentsRandomPosition)
        return Parameters(*paramVals)

    def create_test_worlds(self, num):
        """
        Create ``num`` new ``World`` objects to simulate.

        The function creates a list of separate``World`` objects, each of which
        will be simulated once. If a ``World`` was passed in the creation of the
        ``Test``, it will be ``deepcopy``d the appropriate number of times. If
        the agents and operators should be moved, each will do so. If no ``World``
        was passed in, then the appropriate number of ``World`` objects will be
        generated randomly with the parameters passed to the ``Test`` object.

        Arguments:
            ``num``, *int*:
                The number of ``World`` objects to create.

            ``return``, *list*:
                A list of ``num`` ``World`` objects.
        """
        testWorlds = []
        if self.world:
            for i in range(self.runs):
                testWorld = self.world.copy()
                if self.agentsRandomPosition:
                    testWorld.shuffle_actors()
                testWorlds.append(testWorld)

        else:
            for i in range(self.runs):
                testWorld = wu.generate_random_drone_demo(dim=self.worldSize, civilians=self.civilians, enemies=self.enemies, operators=len(self.operators), agents=len(self.agents), visionRange=self.visionRange, bombRange=self.bombRange, log=self.log)
                testWorlds.append(testWorld)

        return testWorlds

    def log_test_info(self, world):
        """Write info about the current test to the log."""
        self.log.info('World:\n{}'.format(world))
        self.log.info('Parameters:')
        self.log.info('World Size: {}'.format(self.worldSize))
        self.log.info('Civilians: {}'.format(self.civilians))
        self.log.info('Enemies: {}'.format(self.enemies))
        self.log.info('Agents: {}'.format(self.agents))
        self.log.info('Operators: {}'.format(self.operators))
        self.log.info('Vision Range: {}'.format(self.visionRange))
        self.log.info('Bomb Range: {}'.format(self.bombRange))
        self.log.info('Rebellion: {}'.format(self.rebel))
        self.log.info('Proactive Rebellion: {}'.format(self.proacRebel))

    def run_tests(self):
        """
        Run the test by simulating each test world for the time limit.

        Prior to each run of the test, information about the test parameters and
        the test world are logged. The runs use the agent and operator personalities
        given to the ``Test`` object to run agent and operator MIDCA cycles.
        """
        results = []
        self.log.info('Starting tests')
        for i in range(self.runs):
            testWorld = self.testWorlds[i]
            self.log.info('Test {}'.format(i + 1))
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
        assert isinstance(world, wu.World), 'run_test input must be World, is {}'.format(world)
        results = {'initWorld': None,
                   'score': None,
                   'eventLog': None,
                   'rebelList': None,
                   'startTime': None
                   }
        serverExists = False
        for port in SERVER_PORTS:
            try:
                server = wc.WorldServer((SERVER_ADDR, port), world, results, limit=self.limit)
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
            raise Exception('Mismatch between map actor count and test actor count')
        optrThreads = []
        optrIndex = 0
        for op in operators:
            opModules = generate_optr_modules(opID=op.id, rejectionProb=self.operators[optrIndex])
            optr = wc.AutoOperator(SERVER_ADDR, port, op.id, opModules)
            optrThread = Process(target=optr.run)
            optrThreads.append(optrThread)
            optrIndex += 1

        agtThreads = []
        agtIndex = 0
        for agt in agents:
            agentModules = generate_agent_modules(agtID=agt.id, rebel=self.rebel[agtIndex], proacRebel=self.proacRebel[agtIndex], compliance=self.agents[agtIndex])
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

        rebList = evaluate.Rebellion.rebellionList
        print rebList
        results['rebelList'] = rebList
        return results


class TestRecords(object):
    """
    Holds detailed results and information on tests run in the drone domain.

    A TestsRecords holds detailed information on every test run, including the
    parameters under which the test was run, the initial world state, the resulting
    score, a log of events occuring during the simulation and a log of all
    rebellions. The records of individual runs are organized in lists within a
    dictionary, where the keys are the has values of a dictionary of parameter
    values.
    """

    def __init__(self):
        """Instantiate TestRecords by setting some object attributes."""
        self.testDict = {}

    def save_records(self):
        """
        Save the ``TestRecords`` object to several files.

        The saved files should record, in detail, all of the results of testing
        saved in the in this object. The results of all the tests will be saved
        in a csv file where each paramter is a separate column, and the results
        are split into two columns (percent of enemies killed and percent of
        civilians still alive). Since a unique set of parameters (a row in the
        csv) may have more than one set of results, the results columns are
        filled by the arithmetic mean of the results for that parameter set.
        Additionally, there is a "count" column which indicates how many times
        tests have been run with that set of parameters.

        Each test's event log will be written to a unique text file with a name
        that indicates the time and date of the test. Similarly, the rebellion
        list for each test will be written to a unique file. Finally, the entire
        records collection will be pickled for reuse and saved in a file.

        Arguments:
            ``return``, *None*
        """
        CSVfilename = 'testRecords.csv'
        with open(CSVfilename, 'w') as CSVfile:
            recordWriter = csv.writer(CSVfile)
            recordWriter.writerow(PARAM_NAMES + ['Enemies Killed', 'Civilians Living'])
            for testParams in self.testDict:
                allTestResults = self.testDict[testParams]
                meanScores = self._average_scores(allTestResults)
                recordWriter.writerow(list(testParams) + list(meanScores))
                for testResults in allTestResults:
                    startTime = testResults['startTime']
                    eLogFilename = 'event-log_{}'.format(startTime)
                    with open('log/eventLogs/{}'.format(eLogFilename), 'w') as eLogFile:
                        eLogFile.write(testResults['eventLog'])
                    print testResults['rebelList']

        with open('testRecords.txt', 'w') as recordFile:
            cPickle.dump(self, recordFile)

    def _average_scores(self, resultDicts):
        """Utility method the find the average scores for a series of results."""
        enemiesScore = 0
        civisScore = 0
        for results in resultDicts:
            score = results['score']
            enemiesScore += score[0]
            civisScore += score[1]

        enemiesScoreMean = enemiesScore / len(resultDicts)
        civisScoreMean = civisScore / len(resultDicts)
        return (
         enemiesScoreMean, civisScoreMean)

    def __getitem__(self, item):
        """Return a list of results for the given set of parameters."""
        if item not in self.testDict:
            raise KeyError('{}'.format(item))
        return self.testDict[item]

    def __setitem__(self, item, val):
        """Set the result of the test with parameters given in ``item``."""
        self.testDict[item] = val

    def __contains__(self, item):
        """Indicate whether the set of parameters in ``item`` is in the record."""
        return item in self.testDict

    def __str__(self):
        """Return a string version of this object."""
        return str(self.testDict)
