#!/usr/bin/env python
"""
MIDCA demo using a dungeon-ish environment.
Agent explores a dungeon with a limited view.
"""

# import MIDCA
from MIDCA import base

# Domain Specific Imports
import dungeon_utils
import dungeon_operators as d_ops
import dungeon_methods as d_mthds
from modules import simulate, perceive, interpret, evaluate, intend


DIMENSION = 10
CHESTS = 3
DOORS = 3
WALLS = 7

# Setup
dng = dungeon_utils.Dungeon(dim=DIMENSION, agent_vision=3)
dng.generate(chests=CHESTS, doors=DOORS, walls=WALLS)

DECLARE_METHODS_FUNC = d_mthds.declare_methods
DECLARE_OPERATORS_FUNC = d_ops.declare_operators
DISPLAY_FUNC = dungeon_utils.draw_Dungeon

# Creates a PhaseManager object, which wraps a MIDCA object
myMidca = base.PhaseManager(dng, display=DISPLAY_FUNC, verbose=2)
#
# # Add phases by name
for phase in ["Simulate", "Perceive", "Interpret", "Eval", "Intend", "Plan", "Act"]:
    myMidca.append_phase(phase)
# NOTE: WORKS TO HERE...

# Add the modules which instantiate basic operation
# Simulate phase modules
myMidca.append_module("Simulate", simulate.SimulateActions())
myMidca.append_module("Simulate", simulate.ASCIIWorldViewer())
myMidca.append_module("Simulate", simulate.WorldChanger())
# TODO: Add fog-of-war and maybe some events

# Perceive phase modules
myMidca.append_module("Perceive", perceive.Observer())
myMidca.append_module("Perceive", perceive.ShowMap())

# Interpret phase modules
# myMidca.append_module("Interpret", note.StateDiscrepancyDetector())
myMidca.append_module("Interpret", interpret.UserGoalInput())
# TODO: Figure out state discrepancy testing

# Eval phase modules
myMidca.append_module("Eval", evaluate.CompletionEvaluator())
# TODO: Look into this more, need to understand it better

# Introspect phase modules (are we even keeping this?)
# myMidca.append_module("Introspect", rebel.Introspection())

# Intend phase modules
myMidca.append_module("Intend", intend.SimpleIntend())

# Plan phase modules
# myMidca.append_module("Plan", planning.HeuristicSearchPlanner())
# NOTE: FOr now, we're using the built in HeuristicSearchPlanner. We may want
# or need to move to PyHop or jShop though, and I need to learn how to do that.

# Act phase modules
# myMidca.append_module("Act", act.SimpleAct())
# NOTE: Another module which I'm subsituting in for now. Once I understand more
# this one may be the first to go.

# Set world viewer to output text
myMidca.set_display_function(DISPLAY_FUNC)

# Tells the PhaseManager to copy and store MIDCA states so they can be accessed later.
# Note: Turning this on drastically increases MIDCA's running time.
myMidca.storeHistory = False
myMidca.mem.logEachAccess = False

# Initialize and start running!
myMidca.init()
myMidca.initGoalGraph()
myMidca.run()
