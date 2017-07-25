"""
This module contains all socket communication related classes and methods.

In order to allow agents and operators to interact with the world and each other
concurrently, we use socket communications and run each agent and operator, as
well as the world simulation, in a separate process. The classes in this module
facilitate that.
"""

from cPickle import dumps, loads
import SocketServer as SS
import socket
import os
from time import sleep
import sys
import threading

from MIDCA import base
from MIDCA.modules import planning

import world_utils
import world_operators as d_ops
import world_methods as d_mthds
from modules import perceive, interpret, evaluate, intend, act, plan


WORLD_STATE_REQ = 1
ACTION_SEND = 2
UPDATE_SEND = 3
GOAL_SEND = 4
GOAL_REQ = 5
AGENT_REQ = 6
DIALOG_SEND = 7
DIALOG_REQ = 8


def msgSetup(func):
    """Open a connection before the func and close it after."""
    def fullMsgFunc(self, *args, **kwargs):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect(self.conAddr)
        result = func(self, *args, **kwargs)
        self.socket.close()
        return result
    return fullMsgFunc


class WorldServer(SS.TCPServer):
    """
    Special TCP server class which simulates the world.

    Network interactions:
    User asking for world state --> World
        World replying with world state --> User

    Agent asking for world state --> World
        World replying with world state --> Agent

    User sending action --> World
        World simulates action

    Agent sending action --> World
        World simulates action

    User sending MIDCA an update --> World
        World updates specified MIDCA agent's knowledge

    Agent sending update to user --> World
        World updates specified user's knowledge

    User sending MIDCA a command --> World
        World gives the command to the specified MIDCA agent
    """

    class HandlerClass(SS.StreamRequestHandler):
        """Custom handler class for a world server."""

        def setup(self):
            SS.StreamRequestHandler.setup(self)
            os.system('clear')
            print(self.server.world)
            print("Actors:")
            for u in self.server.world.all_users:
                print("{} = {}".format(u.ascii_rep, repr(u)))

        def read_data(self):
            """Read incoming data until we see \254."""
            data = ""
            newChar = self.rfile.read(1)
            while newChar != '\254':
                data += newChar
                newChar = self.rfile.read(1)
                # print(data)
                # time.sleep(0.5)
            return data

        def handle(self):
            """
            Accept incoming messages and respond appropriately.

            The format for incoming messages should be::

                MSGTYPE:USERID:DATA

            The terminating newline is important!
            """
            dng = self.server.world
            qGoals = self.server.queuedGoals
            msgs = self.server.messages

            self.data = self.read_data()
            self.data = self.data.split(':')
            msgType = int(self.data[0])
            userID = self.data[1]
            msgData = self.data[2:] if len(self.data) >= 3 else None

            if msgType == WORLD_STATE_REQ:
                # Request format: WORLD_STATE_REQ:USERID
                user = dng.get_user(userID)
                user.view(dng)
                pickledMap = dumps(user.map)
                self.wfile.write(pickledMap)

            elif msgType == ACTION_SEND:
                # Request format: ACTION_SEND:USERID:ACTIONSTR
                success = dng.apply_action_str(msgData[0], userID)
                if success:
                    if userID in msgs:
                        msgs[userID].append(("Action success", userID))
                    else:
                        msgs[userID] = [("Action success", userID)]

            elif msgType == UPDATE_SEND:
                # Request format: UPDATE_SEND:USERID:COMMAND
                # Commands:
                #   "list"
                #   "send":RECIPIENTID:OBJID
                cmd = msgData[0]

                if cmd == "list":
                    objs = dng.users[userID].known_objects
                    listStr = ""
                    for obj in objs:
                        listStr += "{} = {}\n".format(repr(obj), obj.id)
                    self.wfile.write(listStr)

                elif cmd == "send":
                    recipientID = msgData[1]
                    recipient = dng.get_user(recipientID)
                    objID = ":".join(msgData[2:])
                    obj = dng.get_object(objID)
                    print(recipientID, recipient)
                    print(objID, obj)
                    if obj is None:
                        if userID in msgs:
                            msgs[userID].append("Updating error: {} not found".format(objID))
                        else:
                            msgs[userID] = ["Updating error: {} not found".format(objID)]
                    recipient.update_knowledge(obj)

                else:
                    raise NotImplementedError("UPDATE_SEND prefix {}".format(cmd))

            elif msgType == GOAL_SEND:
                # Request format: GOAL_SEND:USERID:RECIPIENTID:GOALSTR
                recipientID = msgData[0]
                if recipientID not in [a.id for a in dng.agents]:
                    if userID in msgs:
                        msgs[userID].append("Sending error: {} not found".format(recipientID))
                    else:
                        msgs[userID] = ["Sending error: {} not found".format(recipientID)]
                    return
                goalStr = "{};{}".format(msgData[1], userID)
                if recipientID in qGoals:
                    qGoals[recipientID].append(goalStr)
                else:
                    qGoals[recipientID] = [goalStr]

            elif msgType == GOAL_REQ:
                # Request format: GOAL_REQ:USERID
                if userID not in qGoals:
                    self.wfile.write("")
                    return
                goalStrs = qGoals[userID]
                msgStr = ":".join(goalStrs)
                self.wfile.write(msgStr)
                del qGoals[userID]

            elif msgType == AGENT_REQ:
                # Request format: AGENT_REQ:USERID
                agent = dng.get_user(userID)
                pickledAgent = dumps(agent)
                self.wfile.write(pickledAgent)

            elif msgType == DIALOG_SEND:
                recipientID = msgData[0]
                message = ":".join(msgData[1:])
                if recipientID in msgs:
                    msgs[recipientID].append((message, userID))
                else:
                    msgs[recipientID] = [(message, userID)]

            elif msgType == DIALOG_REQ:
                # Request format: GOAL_REQ:USERID[:SENDERID]
                if userID not in msgs:
                    self.wfile.write("")
                    return
                userMsgs = msgs[userID]

                if msgData[0] != "":
                    userMsgs = [msg[0] for msg in userMsgs if msg[1] == msgData[0]]

                pickledDialogs = dumps(userMsgs)
                self.wfile.write(pickledDialogs)
                del msgs[userID]

            else:
                raise NotImplementedError("Message type {}".format(msgType))

            return

    def __init__(self, server_address, world, bind_and_activate=True):
        """Create server class."""
        SS.TCPServer.__init__(self, server_address, WorldServer.HandlerClass, bind_and_activate)
        self.world = world
        self.queuedGoals = {}
        self.messages = {}


class Client(object):
    """Superclass for world clients."""

    def __init__(self, serverAddr, serverPort, userID):
        self.conAddr = (serverAddr, serverPort)
        self.userID = userID

    def send(self, msgType, data=""):
        """Send given data as a message of the given type."""
        # print("sending {}:{}:{}\254".format(str(msgType), self.userID, data))
        self.socket.sendall("{}:{}:{}\254".format(str(msgType), self.userID, data))

    def recv(self, bufSize=2048):
        return self.socket.recv(bufSize)

    @msgSetup
    def inform(self, recipientID, objID):
        self.send(UPDATE_SEND, "send:{}:{}".format(recipientID, objID))

    @msgSetup
    def dialog(self, recipientID, message):
        """Allow a user to send a plain text message to another user."""
        msgData = "{}:{}".format(recipientID, message)
        self.send(DIALOG_SEND, msgData)

    @msgSetup
    def send_action(self, actionStr):
        """Allow the user to act in the world."""
        self.send(ACTION_SEND, actionStr)

    def wait_for_dialogs(self, senderID=""):
        dialogs = self.get_dialogs(senderID)
        while dialogs is None:
            dialogs = self.get_dialogs(senderID)
            sleep(0.25)
        return dialogs

    @msgSetup
    def get_dialogs(self, senderID=""):
        self.send(DIALOG_REQ, senderID)
        pickledDialogs = self.recv(4096)
        if pickledDialogs == "":
            return
        dialogs = loads(pickledDialogs)
        return dialogs


class OperatorClient(Client):
    """Client for operators."""

    def run(self):
        """Run both the input and update loops."""
        # inputThread = threading.Thread(target=self.__input_loop)
        updateThread = threading.Thread(target=self.__update_loop)
        updateThread.start()
        # inputThread.start()

    def __input_loop(self):
        """Run a loop which allows the operator interact with the world."""
        while True:
            cmd = raw_input("")
            self.parse_command(cmd)

    def __update_loop(self):
        """Run a loop which constantly feeds the user world state info."""
        while True:
            os.system('clear')
            print("Operator {}".format(self.userID))
            self.draw_perception()
            print("Messages: ")
            self.read_dialogs()
            # sleep(15)
            cmd = raw_input("Command>> ")
            self.parse_command(cmd)

    def parse_command(self, cmd):
        """
        Parse an operator command and execute the appropriate action.

        Command formats:
        action op(args)
        inform
        direct recipientID predicate(args)
        say recipientID message
        """

        cmdData = cmd.split(" ")

        if cmdData[0] == "action":
            self.send_action(cmdData[1])

        if cmdData[0] == "inform":
            self.send_inform()

        if cmdData[0] == "direct":
            self.direct(cmdData[1:])

        if cmdData[0] == "say":
            self.dialog(cmdData[1], " ".join(cmdData[2:]))

    @msgSetup
    def direct(self, goalData):
        """Allow user to give a MIDCA agent a goal."""
        self.send(GOAL_SEND, "{}:{}".format(goalData[0], goalData[1]))

    def draw_perception(self):
        worldView = self.get_perception()
        print(worldView)
        print("Known objects:")
        self.get_object_list()

    def read_dialogs(self):
        dialogs = self.get_dialogs()
        if dialogs is None:
            return
        for dialog in dialogs:
            print("From {}".format(dialog[1]))
            print("\t" + dialog[0])

    def send_inform(self):
        """Allow user to give information to another user."""
        # Indicate to server which information the user is giving, and id of recipient
        objID = raw_input("Input object ID\n>> ")
        recipientID = raw_input("Input recipient ID\n>> ")
        self.inform(recipientID, objID)

    @msgSetup
    def get_perception(self):
        self.send(WORLD_STATE_REQ, "")
        sleep(0.1)
        pickledWorld = self.socket.recv(4096)
        self.map = loads(pickledWorld)
        return self.map

    @msgSetup
    def get_object_list(self):
        """Get and print a list of objects known to the user"""
        # Ask server for all pieces of info operator can give
        self.send(UPDATE_SEND, "list")
        objsList = self.socket.recv(1024)
        # List these for user and ask user to select one
        print(objsList)


class MIDCAClient(Client):
    """Client which serves as a go between for a MIDCA instance and the sim world."""

    @msgSetup
    def agent(self):
        """Return the agent object corresponding to the client's userID."""
        self.send(AGENT_REQ)
        pickledAgent = self.socket.recv(4096)
        try:
            agent = loads(pickledAgent)
        except EOFError as e:
            print(pickledAgent)
            print(e)
        return agent

    @msgSetup
    def observe(self, display=False):
        """Have the agent observe the world. """
        self.send(WORLD_STATE_REQ)
        if display:
            worldView = self.socket.recv(2048)
            os.system('clear')
            print(worldView)

    @msgSetup
    def get_new_goals(self):
        """Retrieve any new goals the server has waiting for the agent."""
        self.send(GOAL_REQ)
        msgStr = self.socket.recv(2048)
        goalStrs = msgStr.split(":")
        return goalStrs


class RemoteAgent(object):
    """
    Contains the MIDCA object and the MIDCAClient which together will be an agent.

    A ``RemoteAgent`` class combines a MIDCA cycle with a MIDCA client to fully
    encapsulate the idea of an agent. This also allows us to have many separate
    remote agents.

    The ``RemoteAgent`` class does *not* take a pre-made MIDCA object as an
    instantiaion argument, nor does it accept a list of phases or modules. Instead,
    phases and modules are appended during instantion automatically. As such,
    different agents cannot have different modules, at least at first.

    Instantion::

        remoteAgent = RemoteAgent(address, port, userID)

    Arguments:

    ``address``, *str*:
        Indicates the IP address of the world simulation server.

    ``port``, *int*:
        Indicates the port number of the world simulation server.

    ``userID``, *str*:
        The ID of the agent which will be controlled by this object.
    """

    DECLARE_METHODS_FUNC = d_mthds.declare_methods
    DECLARE_OPERATORS_FUNC = d_ops.declare_operators
    PLAN_VALIDATOR = plan.worldPlanValidator
    DISPLAY_FUNC = world_utils.draw_World
    VERBOSITY = 2
    PHASES = ["Perceive", "Interpret", "Eval", "Intend", "Plan", "Act"]
    MODULES = {"Perceive":  [perceive.RemoteObserver(),
                             perceive.ShowMap()],
               "Interpret": [interpret.CompletionEvaluator(),
                             interpret.StateDiscrepancyDetector(),
                             interpret.GoalValidityChecker(),
                             interpret.DiscrepancyExplainer(),
                             interpret.RemoteUserGoalInput()],
               "Eval":      [evaluate.GoalManager(),
                             evaluate.HandleRebellion()],
               "Intend":    [intend.QuickIntend()],
               "Plan":      [planning.GenericPyhopPlanner(DECLARE_METHODS_FUNC,
                                                          DECLARE_OPERATORS_FUNC,
                                                          PLAN_VALIDATOR,
                                                          verbose=VERBOSITY)],
               "Act":       [act.SimpleAct()]}

    def __init__(self, addr, port, userID):
        """Instantiate ``RemoteAgent`` object by creating appropriate MIDCA cycle."""
        self.conAddr = (addr, int(port))
        self.userID = userID
        self.client = MIDCAClient(addr, int(port), userID)

        self.MIDCACycle = base.PhaseManager(self.client,
                                            display=RemoteAgent.DISPLAY_FUNC,
                                            verbose=RemoteAgent.VERBOSITY)

        for phase in RemoteAgent.PHASES:
            self.MIDCACycle.append_phase(phase)
            for module in RemoteAgent.MODULES[phase]:
                self.MIDCACycle.append_module(phase, module)

        self.MIDCACycle.set_display_function(RemoteAgent.DISPLAY_FUNC)

        self.MIDCACycle.storeHistory = False
        self.MIDCACycle.mem.logEachAccess = False

    def run(self):
        """
        Begin the attached MIDCA cycle.

        Initializes the MIDCA object and runs the cycle.
        """
        self.MIDCACycle.init()
        self.MIDCACycle.initGoalGraph(cmpFunc=plan.worldGoalComparator)
        self.MIDCACycle.run(phaseDelay=1, verbose=RemoteAgent.VERBOSITY)


# class AutoOperator(object):
#     """
#     Represents an automatic operator, which directs agents based on a policy.
#
#     An ``AutoOperator`` object holds an ``OperatorClient`` of its own, and interacts
#     with the world through the client, following a pre-made policy given to the
#     operator at instantiation. The policy determines how, when, and which goals
#     the operator gives an agent, and how the operator responds to rebellion.
#
#     The policy given to the operator should be a function which takes in the world
#     state as the operator sees it and returns a list of strings (which can be emtpy)
#     such that each string is a valid operator command.
#
#     Instantiation::
#
#         autoOperator = AutoOperator(addr, port, userID, policy)
#
#     Arguments:
#
#     ``address``, *str*:
#         Indicates the IP address of the world simulation server.
#
#     ``port``, *int*:
#         Indicates the port number of the world simulation server.
#
#     ``userID``, *str*:
#         The ID of the operator which will be controlled by this object.
#
#     ``policy``, *function*:
#         The policy function for this operator, which is used to generate the next
#         commands issued by the operator. Should have one parameter and returns a
#         list of strings (which may be empty).
#     """
#
#     def __init__(self, addr, port, userID, policy):
#         """Instantiate an automatic operator with the given name and policy."""
#         self.client = OperatorClient(addr, port, userID)
#         self.userID = userID
#         self.policy = policy
# it
#     def



if __name__ == '__main__':
    serveType = sys.argv[1]
    port = int(sys.argv[2])

    if serveType == "sim":
        worldFile = sys.argv[3]
        addr = ('localhost', port)
        dng = world_utils.build_World_from_file(worldFile)
        testServer = WorldServer(addr, dng)
        try:
            testServer.serve_forever()
        finally:
            testServer.shutdown()

    elif serveType == "operator":
        userID = sys.argv[3]
        opClient = OperatorClient('localhost', port, userID)
        opClient.run()

    elif serveType == "agent":
        userID = sys.argv[3]
        agtClient = RemoteAgent('localhost', port, userID)
        agtClient.run()
