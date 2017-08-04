"""FILL THIS IN."""

# PYthon imports
import subprocess
import threading
from multiprocessing import Process
import time
import socket
import os
import logging

# Rebel Agent Imports
import world_utils
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
DISPLAY_FUNC = world_utils.draw_World
VERBOSITY = 0
PHASES = ["Perceive", "Interpret", "Eval", "Intend", "Plan", "Act"]

AGENT_MODULES = {"Perceive":  [perceive.RemoteObserver],
                 "Interpret": [interpret.RemoteUserGoalInput,
                               interpret.CompletionEvaluator,
                               interpret.StateDiscrepancyDetector,
                               interpret.GoalValidityChecker,
                               interpret.DiscrepancyExplainer],
                 "Eval":      [evaluate.GoalManager,
                               evaluate.HandleRebellion],
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


def generate_agent_modules(agtID, rebel=True):
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
            if modInit == evaluate.HandleRebellion and not rebel:
                # Don't add the handle rebellion module if we don't want rebelling
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


def run_visible_test(world, moveLimit=500):
    """
    Run a test using the given world for the given time, then record the results.
    """
    score = [0, 0]
    serverExists = False
    for port in SERVER_PORTS:
        try:
            server = wc.WorldServer((SERVER_ADDR, port), world, score, limit=moveLimit)
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


def run_test(world, moveLimit=500, rebel=True, rejectionProb=0.0):
    """
    Run a test using the given world, agent, and operator, then record the results.
    """
    score = [0, 0]
    serverExists = False
    for port in SERVER_PORTS:
        try:
            server = wc.WorldServer((SERVER_ADDR, port), world, score, limit=moveLimit)
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
        agentModules = generate_agent_modules(agt.id, rebel)
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
