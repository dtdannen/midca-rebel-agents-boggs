"""
MIDCA demo using a dungeon-ish environment.

Agent explores a dungeon with a limited view.
"""
import subprocess
import time

# import MIDCA
from MIDCA import base
from MIDCA.modules import planning

# Domain Specific Imports
import dungeon_utils
import dungeon_server as ds
import dungeon_client as dc
import dungeon_operators as d_ops
import dungeon_methods as d_mthds
from modules import perceive, interpret, evaluate, intend, act, plan


DUNGEON_FILE = './dng_files/drone_demo.dng'
dng = dungeon_utils.build_Dungeon_from_file(DUNGEON_FILE)

DECLARE_METHODS_FUNC = d_mthds.declare_methods
DECLARE_OPERATORS_FUNC = d_ops.declare_operators
PLAN_VALIDATOR = plan.dungeonPlanValidator
DISPLAY_FUNC = dungeon_utils.draw_Dungeon
VERBOSITY = 2

operators = dng.operators
agents = dng.agents

SERVER_ADDR = 'localhost'
SERVER_PORT = 9990
SERVER_ARGS = ["python", "./dungeon_server.py", str(SERVER_PORT), DUNGEON_FILE, " 2> serverError.log; sleep 5"]
server_call = ["xterm", "-e", " ".join(SERVER_ARGS)]
server = subprocess.Popen(server_call)
time.sleep(1)


opProcesses = []
for op in operators:
    client_args = ["python", "./dungeon_client.py", "operator", str(SERVER_PORT), op.id, "; sleep 5"]
    op_call = ["xterm", "-e", " ".join(client_args)]
    opProcesses.append(subprocess.Popen(op_call))


# for agt in agents:
# TODO: Modify this bit so that many agents can run simultaneously
agent = dc.MIDCAClient(SERVER_ADDR, SERVER_PORT, agents[0].__name__)
MIDCAObj = base.PhaseManager(agent, display=DISPLAY_FUNC, verbose=VERBOSITY)


for phase in ["Perceive", "Interpret", "Eval", "Intend", "Plan", "Act"]:
    MIDCAObj.append_phase(phase)

MIDCAObj.append_module("Perceive", perceive.RemoteObserver())
MIDCAObj.append_module("Perceive", perceive.ShowMap())
MIDCAObj.append_module("Interpret", interpret.CompletionEvaluator())
MIDCAObj.append_module("Interpret", interpret.StateDiscrepancyDetector())
MIDCAObj.append_module("Interpret", interpret.GoalValidityChecker())
MIDCAObj.append_module("Interpret", interpret.DiscrepancyExplainer())
MIDCAObj.append_module("Interpret", interpret.RemoteUserGoalInput())
MIDCAObj.append_module("Eval", evaluate.GoalManager())
MIDCAObj.append_module("Eval", evaluate.HandleRebellion())
MIDCAObj.append_module("Intend", intend.QuickIntend())
MIDCAObj.append_module("Plan", planning.GenericPyhopPlanner(DECLARE_METHODS_FUNC,
                                                            DECLARE_OPERATORS_FUNC,
                                                            PLAN_VALIDATOR,
                                                            verbose=VERBOSITY))
MIDCAObj.append_module("Act", act.SimpleAct())


MIDCAObj.set_display_function(DISPLAY_FUNC)

MIDCAObj.storeHistory = False
MIDCAObj.mem.logEachAccess = False

# Initialize and start running!
MIDCAObj.init()
MIDCAObj.initGoalGraph(cmpFunc=plan.dungeonGoalComparator)
MIDCAObj.run(phaseDelay=1, verbose=VERBOSITY)
