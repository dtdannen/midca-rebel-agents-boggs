"""
MIDCA demo using a world-ish environment.

Agent explores a world with a limited view.
"""
import subprocess
import time
import threading

# import MIDCA
from MIDCA import base
from MIDCA.modules import planning

# Domain Specific Imports
import world_utils
import world_communications as wc
import world_operators as d_ops
import world_methods as d_mthds
from modules import perceive, interpret, evaluate, intend, act, plan


DUNGEON_FILE = './dng_files/largeMultiAgent.dng'
dng = world_utils.build_World_from_file(DUNGEON_FILE)

SERVER_ADDR = 'localhost'
SERVER_PORT = 9990
# SERVER_ARGS = ["python", "./world_communications.py", "sim", str(SERVER_PORT), DUNGEON_FILE, " 2> serverError.log; sleep 5"]
# server_call = ["xterm", "-e", " ".join(SERVER_ARGS)]
# server = subprocess.Popen(server_call)
server = wc.WorldServer((SERVER_ADDR, SERVER_PORT), dng)
serverThread = threading.Thread(target=server.serve_forever)
serverThread.start()
time.sleep(1)


operators = dng.operators
agents = dng.agents

opProcesses = []
for op in operators:
    outFileName = "logs/{}-Log.txt".format(op.id)
    client_args = ["python", "./world_communications.py",
                   "operator", str(SERVER_PORT), op.id,
                   ">", outFileName, "; sleep 5"]
    op_call = ["xterm", "-e", " ".join(client_args)]
    opProcesses.append(subprocess.Popen(op_call))

agtProcesses = []
for agt in agents:
    outFileName = "logs/{}-Log.txt".format(agt.id)
    client_args = ["python", "./world_communications.py",
                   "agent", str(SERVER_PORT), agt.id,
                   "> ", outFileName, "; sleep 5"]
    agt_call = ["xterm", "-e", " ".join(client_args)]
    agtProcesses.append(subprocess.Popen(agt_call))
