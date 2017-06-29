#!/usr/bin/env python
"""
MIDCA demo using a dungeon-ish environment.

Agent explores a dungeon with a limited view.
"""

# import MIDCA
from MIDCA import base
from MIDCA.modules import planning

# Domain Specific Imports
import dungeon_utils
import dungeon_operators as d_ops
import dungeon_methods as d_mthds
from modules import simulate, perceive, interpret, evaluate, intend, act, plan


DIMENSION = 10
CHESTS = 3
DOORS = 3
WALLS = 7

# Setup
dng = dungeon_utils.Dungeon(dim=DIMENSION, agent_vision=2)
dng.generate(chests=CHESTS, doors=DOORS, walls=WALLS)

DECLARE_METHODS_FUNC = d_mthds.declare_methods
DECLARE_OPERATORS_FUNC = d_ops.declare_operators
PLAN_VALIDATOR = plan.dungeonPlanValidator
DISPLAY_FUNC = dungeon_utils.draw_Dungeon
VERBOSITY = 0

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
myMidca.append_module("Simulate", simulate.WorldChanger())
# TODO: Add some events

# Perceive phase modules
myMidca.append_module("Perceive", perceive.Observer())
myMidca.append_module("Perceive", perceive.ShowMap())

# Interpret phase modules
myMidca.append_module("Interpret", interpret.StateDiscrepancyDetector())
myMidca.append_module("Interpret", interpret.GoalValidityChecker())
myMidca.append_module("Interpret", interpret.DiscrepancyExplainer())
myMidca.append_module("Interpret", interpret.UserGoalInput())

# Eval phase modules
myMidca.append_module("Eval", evaluate.CompletionEvaluator())
# TODO: Implement an evaluation function able to recognize that the agent
# needs to unlock a door, pick up a key, or open a chest.

# Introspect phase modules (are we even keeping this?)
# myMidca.append_module("Introspect", rebel.Introspection())

# Intend phase modules
myMidca.append_module("Intend", intend.SimpleIntend())

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
myMidca.initGoalGraph(goalCompareFunction=plan.dungeonGoalComparator)
myMidca.run()
