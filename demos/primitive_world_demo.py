#!/usr/bin/env python
"""
MIDCA demo using a world-ish environment.

Agent explores a world with a limited view.
"""
import subprocess

# import MIDCA
from MIDCA import base
from MIDCA.modules import planning

# Domain Specific Imports
import world_utils
import world_operators as d_ops
import world_methods as d_mthds
from modules import simulate, perceive, interpret, evaluate, intend, act, plan


DIMENSION = 10
CHESTS = 3
DOORS = 3
WALLS = 7

# Setup
# dng = world_utils.World(dim=DIMENSION, agent_vision=2)
# dng.generate(chests=CHESTS, doors=DOORS, walls=WALLS)
dng = world_utils.build_World_from_file('../dng_files/test.dng')

DECLARE_METHODS_FUNC = d_mthds.declare_methods
DECLARE_OPERATORS_FUNC = d_ops.declare_operators
PLAN_VALIDATOR = plan.worldPlanValidator
DISPLAY_FUNC = world_utils.draw_World
VERBOSITY = 2

# Set up remote user variables
USR1_POS = (8, 8)
USR1_VIEW = 3
USR1_PORT = 9990

USR2_POS = (1, 1)
USR2_VIEW = 3
USR2_PORT = 9995

# Open clients for users
USR1_args = ["xterm", "-e", "python", "../world_client_old.py", str(USR1_PORT)]
USR2_args = ["xterm", "-e", "python", "../world_client_old.py", str(USR2_PORT)]
client1 = subprocess.Popen(USR1_args)
client2 = subprocess.Popen(USR2_args)

# Creates a PhaseManager object, which wraps a MIDCA object
myMidca = base.PhaseManager(dng, display=DISPLAY_FUNC, verbose=VERBOSITY)
#
# # Add phases by name
for phase in ["Simulate", "Perceive", "Interpret", "Eval", "Intend", "Plan", "Act"]:
    myMidca.append_phase(phase)

# Add the modules which instantiate basic operation
# Simulate phase modules
myMidca.append_module("Simulate", simulate.SimulateActions())
# myMidca.append_module("Simulate", simulate.ASCIIWorldViewer())
# myMidca.append_module("Simulate", simulate.WorldChanger())
myMidca.append_module("Simulate", simulate.UpdateRemoteUser(userPos=USR1_POS,
                                                            userView=USR1_VIEW,
                                                            userPort=USR1_PORT))
myMidca.append_module("Simulate", simulate.UpdateRemoteUser(userPos=USR2_POS,
                                                            userView=USR2_VIEW,
                                                            userPort=USR2_PORT))
# TODO: Add some events

# Perceive phase modules
myMidca.append_module("Perceive", perceive.Observer())
myMidca.append_module("Perceive", perceive.ShowMap())

# Interpret phase modules
myMidca.append_module("Interpret", interpret.CompletionEvaluator())
myMidca.append_module("Interpret", interpret.StateDiscrepancyDetector())
myMidca.append_module("Interpret", interpret.GoalValidityChecker())
myMidca.append_module("Interpret", interpret.DiscrepancyExplainer())
# myMidca.append_module("Interpret", interpret.UserGoalInput())
myMidca.append_module("Interpret", interpret.PrimitiveRemoteUserGoalInput(USR1_PORT))
myMidca.append_module("Interpret", interpret.PrimitiveRemoteUserGoalInput(USR2_PORT))

# Eval phase modules
myMidca.append_module("Eval", evaluate.GoalManager())

# Introspect phase modules (are we even keeping this?)
# myMidca.append_module("Introspect", rebel.Introspection())

# Intend phase modules
myMidca.append_module("Intend", intend.QuickIntend())

# Plan phase modules
myMidca.append_module("Plan", planning.GenericPyhopPlanner(DECLARE_METHODS_FUNC,
                                                           DECLARE_OPERATORS_FUNC,
                                                           PLAN_VALIDATOR,
                                                           verbose=VERBOSITY))

# Act phase modules
myMidca.append_module("Act", act.SimpleAct())

# Set world viewer to output text
myMidca.set_display_function(DISPLAY_FUNC)

# Tells the PhaseManager to copy and store MIDCA states so they can be accessed later.
# Note: Turning this on drastically increases MIDCA's running time.
myMidca.storeHistory = False
myMidca.mem.logEachAccess = False

# Initialize and start running!
myMidca.init()
myMidca.initGoalGraph(cmpFunc=plan.worldGoalComparator)
myMidca.run(usingInterface=True, verbose=VERBOSITY)
