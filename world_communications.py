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
from time import sleep, time, strftime
import sys
import logging
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
DECLARE_METHODS_FUNC = d_mthds.declare_methods
DECLARE_OPERATORS_FUNC = d_ops.declare_operators
PLAN_VALIDATOR = plan.worldPlanValidator
DISPLAY_FUNC = world_utils.draw_World
VERBOSITY = 0
PHASES = ['Perceive', 'Interpret', 'Eval', 'Intend', 'Plan', 'Act']
AGENT_MODULES = {'Perceive': [perceive.RemoteObserver(),
              perceive.ShowMap()],
   'Interpret': [
               interpret.CompletionEvaluator(),
               interpret.StateDiscrepancyDetector(),
               interpret.GoalValidityChecker(),
               interpret.DiscrepancyExplainer(),
               interpret.RemoteUserGoalInput()],
   'Eval': [
          evaluate.GoalManager(),
          evaluate.HandleRebellion()],
   'Intend': [
            intend.QuickIntend()],
   'Plan': [
          planning.GenericPyhopPlanner(DECLARE_METHODS_FUNC, DECLARE_OPERATORS_FUNC, PLAN_VALIDATOR, verbose=VERBOSITY)],
   'Act': [
         act.SimpleAct()]
   }
AUTO_OP_MODULES = {'Perceive': [perceive.OperatorObserver()],'Interpret': [
               interpret.OperatorInterpret()],
   'Eval': [
          evaluate.OperatorHandleRebelsStochastic()],
   'Intend': [],'Plan': [
          plan.OperatorPlanGoals()],
   'Act': [
         act.OperatorGiveGoals()]
   }

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

    Contains a copy of the world and a handler class which is able to interpret
    and appropriately reply to requests. It also limits the number of times it
    can receive an action before the server quits and the simulation ends, allowing
    us to limit the length of the simulations.
    """

    class HandlerClass(SS.StreamRequestHandler):
        """Custom handler class for a world server."""

        def setup(self):
            SS.StreamRequestHandler.setup(self)

        def display(self):
            os.system('clear')
            worldState = self.server.world.status_display()
            print worldState
            score = self.server.world.score
            print 'Enemies: {} | Civis: {}'.format(score[0], score[1])
            self.server.log.info('Enemies: {} | Civis: {}'.format(score[0], score[1]))

        def read_data(self):
            """Read incoming data until we see \xac."""
            data = ''
            newChar = self.rfile.read(1)
            while newChar != '\xac':
                data += newChar
                newChar = self.rfile.read(1)

            return data

        def send_data(self, data):
            """Write data to the file-like connection, terminating with \xac."""
            if type(data) is not str:
                data = str(data)
            self.wfile.write(data + '\xac')

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
            log = self.server.log
            self.data = self.read_data()
            log.info("Data recv'd: {}".format(self.data))
            self.data = self.data.split(':')
            msgType = int(self.data[0])
            userID = self.data[1]
            msgData = self.data[2:] if len(self.data) >= 3 else None
            if msgType == WORLD_STATE_REQ:
                user = dng.get_user(userID)
                user.view(dng)
                pickledMap = dumps(user.map)
                self.send_data(pickledMap)
                self.display()
                log.info('\tSent world state to {}'.format(user))
                if self.server.timeLeft <= 0:
                    log.info('Shutting down server, time out')
                    self.server.record_results()
                    self.server.server_close()
            elif msgType == ACTION_SEND:
                success = dng.apply_action_str(msgData[0], userID)
                if success:
                    if userID in msgs:
                        log.info('\tSuccessfully applied action')
                        msgs[userID].append(('Action success', userID))
                    else:
                        log.info('\\Failed to applied action')
                        msgs[userID] = [('Action success', userID)]
                if self.server.score[0] == 1.0:
                    log.info('Shutting down server, all enemies dead')
                    self.server.record_results()
                    self.server.server_close()
            elif msgType == UPDATE_SEND:
                cmd = msgData[0]
                if cmd == 'list':
                    objs = dng.users[userID].known_objects
                    listStr = ''
                    for obj in objs:
                        listStr += '{} = {}\n'.format(repr(obj), obj.id)

                    self.send_data(listStr)
                    log.info('\tSent list of objects to {}'.format(userID))
                elif cmd == 'send':
                    recipientID = msgData[1]
                    recipient = dng.get_user(recipientID)
                    objID = ':'.join(msgData[2:])
                    obj = dng.get_object(objID)
                    if obj is None:
                        if userID in msgs:
                            msgs[userID].append('Updating error: {} not found'.format(objID))
                            log.warn('\tObject {} not found for inform command'.format(objID))
                        else:
                            msgs[userID] = [
                             'Updating error: {} not found'.format(objID)]
                            log.warn('\tObject {} not found for inform command'.format(objID))
                    recipient.update_knowledge(obj)
                    log.info('\t{} informed {} of {}'.format(userID, recipientID, obj))
                else:
                    raise NotImplementedError('UPDATE_SEND prefix {}'.format(cmd))
            elif msgType == GOAL_SEND:
                recipientID = msgData[0]
                if recipientID not in [ a.id for a in dng.agents ]:
                    if userID in msgs:
                        msgs[userID].append('Sending error: {} not found'.format(recipientID))
                        log.warn('\tRecipient {} not found to give goal'.format(recipientID))
                    else:
                        msgs[userID] = [
                         'Sending error: {} not found'.format(recipientID)]
                        log.warn('\tRecipient {} not found to give goal'.format(recipientID))
                    return
                goalStr = '{};{}'.format(msgData[1], userID)
                if recipientID in qGoals:
                    qGoals[recipientID].append(goalStr)
                else:
                    qGoals[recipientID] = [
                     goalStr]
                log.info('\t{} gave {} the goal {}'.format(userID, recipientID, goalStr))
            elif msgType == GOAL_REQ:
                if userID not in qGoals:
                    self.send_data('')
                    return
                goalStrs = qGoals[userID]
                msgStr = ':'.join(goalStrs)
                self.send_data(msgStr)
                del qGoals[userID]
                log.info('\t{} received goal {}'.format(userID, goalStrs))
            elif msgType == AGENT_REQ:
                agent = dng.get_user(userID)
                pickledAgent = dumps(agent)
                self.send_data(pickledAgent)
            elif msgType == DIALOG_SEND:
                recipientID = msgData[0]
                message = ':'.join(msgData[1:])
                if recipientID in msgs:
                    msgs[recipientID].append((message, userID))
                else:
                    msgs[recipientID] = [
                     (
                      message, userID)]
                log.info('\t{} sent message {} to {}'.format(userID, message, recipientID))
            elif msgType == DIALOG_REQ:
                if userID not in msgs:
                    self.send_data('')
                    return
                userMsgs = msgs[userID]
                if msgData[0] != '':
                    userMsgs = [ msg[0] for msg in userMsgs if msg[1] == msgData[0] ]
                else:
                    del msgs[userID]
                pickledDialogs = dumps(userMsgs)
                self.send_data(pickledDialogs)
                log.info('\t{} got messages {}'.format(userID, userMsgs))
            else:
                raise NotImplementedError('Message type {}'.format(msgType))
            return

    def __init__(self, server_address, world, resultsObj, limit=None, logFile='logs/worldServer.log'):
        """Create server class."""
        SS.TCPServer.__init__(self, server_address, WorldServer.HandlerClass, bind_and_activate=True)
        self.world = world
        self.queuedGoals = {}
        self.messages = {}
        self.timeLimit = limit
        self.startTime = time()
        self.endTime = self.startTime + self.timeLimit
        self.resultsObj = resultsObj
        self.resultsObj['initWorld'] = repr(world)
        self.resultsObj['startTime'] = strftime('%a-%d-%m-%H:%M:%S')
        self.log = logging.getLogger('world_sim')
        self.log.setLevel(logging.INFO)
        handler = logging.FileHandler(logFile, mode='w')
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter(fmt='%(asctime)s: %(message)s', datefmt='%H:%M:%S')
        handler.setFormatter(formatter)
        self.log.addHandler(handler)

    @property
    def score(self):
        return self.world.score

    @property
    def timeLeft(self):
        """Indicate how much time is left for the world simulation to run."""
        return self.endTime - time()

    def record_results(self):
        """Record the result information of the run in the results dict."""
        self.resultsObj['score'] = self.score
        self.resultsObj['eventLog'] = self.world.eventLog
        print self.world.eventLog


class Client(object):
    """Superclass for world clients."""

    def __init__(self, serverAddr, serverPort, userID):
        self.conAddr = (
         serverAddr, serverPort)
        self.userID = userID
        self.lastData = ''

    def send(self, msgType, data=''):
        """Send given data as a message of the given type."""
        self.socket.sendall('{}:{}:{}\xac'.format(str(msgType), self.userID, data))

    def recv(self):
        """
        Read incoming data until we see \xac.

        Because some of the incoming messages will be rather large, it's terribly
        inefficient to read data in the way the world server does. Instead, we read
        in 2048 byte chunks and see if the terminal character is in the message.
        If it is, we split the message at it, prepending whatever is currently in
        ``self.lastData`` to the first portion and then storing the latter portion
        in ``self.lastData``. If the terminal character is not found in the chunk,
        the entire chunk is appended to ``self.lastData``.

        This process means that ``self.lastData`` progressively builds up a message,
        so that once the terminal character is read in we can prepend the rest of
        the message.

        Arguments:

        ``returns``, *str*:
            Returns an entire message sent to the socket, **without** the terminal
            character.
        """
        data = ''
        newChunk = self.socket.recv(2048)
        while '\xac' not in newChunk:
            self.lastData += newChunk
            newChunk = self.socket.recv(2048)

        msgEnd, nextMsgStart = newChunk.split('\xac')
        data = self.lastData + msgEnd
        self.lastData = nextMsgStart
        return data

    @msgSetup
    def inform(self, recipientID, objID):
        self.send(UPDATE_SEND, 'send:{}:{}'.format(recipientID, objID))

    @msgSetup
    def dialog(self, recipientID, message):
        """Allow a user to send a plain text message to another user."""
        msgData = '{}:{}'.format(recipientID, message)
        self.send(DIALOG_SEND, msgData)

    @msgSetup
    def send_action(self, actionStr):
        """Allow the user to act in the world."""
        self.send(ACTION_SEND, actionStr)

    def wait_for_dialogs(self, senderID=''):
        dialogs = self.get_dialogs(senderID)
        while dialogs is None:
            dialogs = self.get_dialogs(senderID)
            sleep(0.25)

        return dialogs

    @msgSetup
    def get_dialogs(self, senderID=''):
        self.send(DIALOG_REQ, senderID)
        pickledDialogs = self.recv()
        if pickledDialogs == '':
            return
        dialogs = loads(pickledDialogs)
        if dialogs == []:
            return
        return dialogs


class OperatorClient(Client):
    """
    Client for a single operator.

    Instantiation::

        opClient = OperatorClient(addr, port, userID)

    Arguments:

    ``address``, *str*:
        Indicates the IP address of the world simulation server.

    ``port``, *int*:
        Indicates the port number of the world simulation server.

    ``userID``, *str*:
        The ID of the operator which will be controlled by this object.

    """

    def __init__(self, addr, port, userID):
        super(OperatorClient, self).__init__(addr, port, userID)

    def display(self):
        """
        Print the operator's world knowledge on the screen for the user.

        This is only useful when the operator is a human. It prints out the name
        of the operator, the operator's dungeon map, and lists known objects.
        """
        os.system('clear')
        print 'Operator {}'.format(self.userID)
        print self.map
        print 'Messages:'
        for msg in self.msgs:
            print '{}:\n\t{}'.format(msg[1], msg[0])

        print 'Known Objects'
        for obj in self.map.objects:
            print '{} = {}'.format(obj, obj.id)

    @msgSetup
    def observe(self, display=False):
        """Have the operator observe the world. """
        self.send(WORLD_STATE_REQ)
        pickledWorld = self.recv()
        return loads(pickledWorld)

    @msgSetup
    def operator(self):
        """Return the ``Agent`` object corresponding to the client's userID."""
        self.send(AGENT_REQ)
        pickledOp = self.recv()
        try:
            optr = loads(pickledOp)
        except EOFError as e:
            print pickledOp
            print e

        return optr

    def parse_command(self, cmd):
        """
        Parse an operator command and execute the appropriate action.

        Command formats::

            action op(args)
            inform recipientID objID
            direct recipientID predicate(args)
            say recipientID message
        """
        cmdData = cmd.split(' ')
        if cmdData[0] == 'action':
            self.send_action(cmdData[1])
        if cmdData[0] == 'inform':
            self.inform(cmdData[1], cmdData[2])
        if cmdData[0] == 'direct':
            self.direct(*cmdData[1:])
        if cmdData[0] == 'say':
            self.dialog(cmdData[1], ' '.join(cmdData[2:]))

    @msgSetup
    def direct(self, recipientID, goalStr):
        """
        Give the specified MIDCA agent a goal.

        Arguments:

        ``recipientID``, *str*:
            The ID of the agent which should be given the goal.

        ``goalStr``, *str*:
            A properly formatted goal string.
        """
        self.send(GOAL_SEND, '{}:{}'.format(recipientID, goalStr))


class MIDCAClient(Client):
    """Client which serves as a go between for a MIDCA instance and the sim world."""

    @msgSetup
    def agent(self):
        """Return the agent object corresponding to the client's userID."""
        self.send(AGENT_REQ)
        pickledAgent = self.recv()
        try:
            agent = loads(pickledAgent)
        except EOFError as e:
            print pickledAgent
            print e

        return agent

    @msgSetup
    def observe(self, display=False):
        """Have the agent observe the world. """
        self.send(WORLD_STATE_REQ)
        pickledWorld = self.recv()
        self.map = loads(pickledWorld)
        if display:
            print self.map

    @msgSetup
    def get_new_goals(self):
        """Retrieve any new goals the server has waiting for the agent."""
        self.send(GOAL_REQ)
        msgStr = self.recv()
        goalStrs = msgStr.split(':')
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

    ``modules``, *dict*:
        A dictionary assigning MIDCA module objects to a phase.
    """

    def __init__(self, addr, port, userID, modules=AGENT_MODULES):
        """Instantiate ``RemoteAgent`` object by creating appropriate MIDCA cycle."""
        self.conAddr = (
         addr, int(port))
        self.userID = userID
        self.client = MIDCAClient(addr, int(port), userID)
        self.MIDCACycle = base.PhaseManager(self.client, display=DISPLAY_FUNC, verbose=VERBOSITY)
        for phase in PHASES:
            self.MIDCACycle.append_phase(phase)
            for module in modules[phase]:
                self.MIDCACycle.append_module(phase, module)

        self.MIDCACycle.set_display_function(DISPLAY_FUNC)
        self.MIDCACycle.storeHistory = False
        self.MIDCACycle.mem.logEachAccess = False

    def run(self):
        """
        Begin the attached MIDCA cycle.

        Initializes the MIDCA object and runs the cycle.
        """
        self.MIDCACycle.init()
        self.MIDCACycle.initGoalGraph(cmpFunc=plan.worldGoalComparator)
        self.MIDCACycle.run(phaseDelay=0.25, verbose=VERBOSITY)


class AutoOperator(object):
    """
    Contains the MIDCA object and the OperatorClient which together will be an oeprator.

    The ``AutoOperator`` class combines a MIDCA cycle with an operator client so
    that fully automatic operators can be used for testing. The MIDCA cycle is
    created on instantiation using a built-in ``dict`` of phases and accompanying
    modules to use. If in automatic mode, the MIDCA cycle dictates how the operator
    should interact with agents and the world.

    The ``AutoOperator`` class does *not* take a pre-made MIDCA object as an
    instantiaion argument, nor does it accept a list of phases or modules. Instead,
    phases and modules are appended during instantion automatically. As such,
    different agents cannot have different modules, at least at first.

    Instantion::

        autoOperator = AutoOperator(address, port, userID)

    Arguments:

    ``address``, *str*:
        Indicates the IP address of the world simulation server.

    ``port``, *int*:
        Indicates the port number of the world simulation server.

    ``userID``, *str*:
        The ID of the agent which will be controlled by this object.

    ``modules``, *dict*:
        A dictionary assigning MIDCA module objects to a phase.
    """

    def __init__(self, addr, port, userID, modules=AUTO_OP_MODULES):
        """Instantiate ``AutoOperator`` object by creating appropriate MIDCA cycle."""
        self.conAddr = (
         addr, int(port))
        self.userID = userID
        self.client = OperatorClient(addr, int(port), userID)
        self.MIDCACycle = base.PhaseManager(self.client, display=lambda x: str(x), verbose=VERBOSITY)
        for phase in PHASES:
            self.MIDCACycle.append_phase(phase)
            for module in modules[phase]:
                self.MIDCACycle.append_module(phase, module)

        self.MIDCACycle.set_display_function(lambda x: str(x))
        self.MIDCACycle.storeHistory = False
        self.MIDCACycle.mem.logEachAccess = False

    def run(self):
        """
        Begin the attached MIDCA cycle.

        Initializes the MIDCA object and runs the cycle.
        """
        self.MIDCACycle.init()
        self.MIDCACycle.initGoalGraph(cmpFunc=plan.worldGoalComparator)
        self.MIDCACycle.run(phaseDelay=0.25, verbose=VERBOSITY)


if __name__ == '__main__':
    serveType = sys.argv[1]
    port = int(sys.argv[2])
    if serveType == 'sim':
        worldFile = sys.argv[3]
        addr = ('localhost', port)
        dng = world_utils.build_World_from_file(worldFile)
        testServer = WorldServer(addr, dng)
        try:
            testServer.serve_forever()
        finally:
            testServer.shutdown()

    elif serveType == 'operator':
        userID = sys.argv[3]
        opClient = AutoOperator('localhost', port, userID)
        opClient.run()
    elif serveType == 'agent':
        userID = sys.argv[3]
        agtClient = RemoteAgent('localhost', port, userID)
        agtClient.run()
