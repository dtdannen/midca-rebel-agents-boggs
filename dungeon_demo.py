#!/usr/bin/env python
"""MIDCA demo using a dungeon-ish environment."""
import inspect
import os

# import MIDCA
from MIDCA import base
from MIDCA.modules import (act, evaluate, intend, note, perceive, planning,
                           rebel, simulator)
from MIDCA.worldsim import domainread, stateread

# Domain Specific Imports
import dungeon_utils

"""
Agent explores a dungeon with a limited view.
"""

# Setup
thisDir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))

### Domain Specific Variables
DOMAIN_FILE = thisDir + "/dungeon.sim"
DISPLAY_FUNC = dungeon_utils.draw_Dungeon_from_MIDCA
# DECLARE_METHODS_FUNC = methods_nbeacons.declare_methods
# DECLARE_OPERATORS_FUNC = operators_nbeacons.declare_operators
# GOAL_GRAPH_CMP_FUNC = None
DIMENSION = 5

# Load domain
world = domainread.load_domain(DOMAIN_FILE)
# TODO: Make chests hold keys properly

# Create Starting state
state1 = dungeon_utils.Dungeon(dim=DIMENSION)
state1.generate(chests=1, doors=2, walls=3)
state1_str = state1.MIDCA_state_str()
print(state1_str)
print(state1)
# Load state
stateread.apply_state_str(world, state1_str)

# Creates a PhaseManager object, which wraps a MIDCA object
myMidca = base.PhaseManager(world, display=DISPLAY_FUNC, verbose=2)
#
# # Add phases by name
for phase in ["Simulate", "Perceive", "Interpret", "Eval", "Introspect", "Intend", "Plan", "Act"]:
    myMidca.append_phase(phase)
# NOTE: WORKS TO HERE...

# Add the modules which instantiate basic operation
# Simulate phase modules
myMidca.append_module("Simulate", simulator.MidcaActionSimulator())
myMidca.append_module("Simulate", simulator.WorldChanger())
myMidca.append_module("Simulate", simulator.ASCIIWorldViewer(DISPLAY_FUNC))
# NOTE: Currently, there is no need for a new Dungeon simulator module. Once we
# do need it, look at simulator.NBeaconsActionSimulator and
# simulator.NBeaconsSimulator for examples. Eventually we will want one, because
# we'll be adding fog-of-war and maybe other things (sp. events?)

# Perceive phase modules
myMidca.append_module("Perceive", perceive.PerfectObserver())
# TODO: Create a fog-of-war perceiver

# Interpret phase modules
myMidca.append_module("Interpret", note.StateDiscrepancyDetector())
myMidca.append_module("Interpret", rebel.UserGoalInputRebelRand())
# NOTE: Currently we don't have any need for a fancy state discrepancy detector
# because everything is deterministic. Once we add FoW and other things, we'll
# need a good discrepancy detector and an explainer. Look at
# assess.SimpleNBeaconsExplain for an example of an explainer.

# Eval phase modules
myMidca.append_module("Eval", evaluate.SimpleEval2())
# TODO: Look into this more, need to understand it better

# Introspect phase modules (are we even keeping this?)
myMidca.append_module("Introspect", rebel.Introspection())

# Intend phase modules
myMidca.append_module("Intend", intend.SimpleIntend())

# Plan phase modules
myMidca.append_module("Plan", planning.HeuristicSearchPlanner())
# NOTE: FOr now, we're using the built in HeuristicSearchPlanner. We may want
# or need to move to PyHop or jShop though, and I need to learn how to do that.

# Act phase modules
myMidca.append_module("Act", act.SimpleAct())
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
