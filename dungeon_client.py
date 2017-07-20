"""
Holds the various server objects and functions for allowing two users.

This code is meant to allow to users to work with MIDCA simulataneously, without
needing to hot-seat a single terminal. It is fairly simple, with the server
sending out the world state, the client displaying that and then transmitting
user orders back to MIDCA.
"""
import socket
from time import sleep
import os
from cPickle import dumps, loads
import sys
import threading

import dungeon_server as ds


def msgSetup(func):
    """Open a connection before the func and close it after."""
    def fullMsgFunc(self, *args, **kwargs):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect(self.conAddr)
        result = func(self, *args, **kwargs)
        self.socket.close()
        return result
    return fullMsgFunc


class Client(object):
    """Superclass for dungeon clients."""

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
        self.send(ds.UPDATE_SEND, "send:{}:{}".format(recipientID, objID))

    @msgSetup
    def dialog(self, recipientID, message):
        """Allow a user to send a plain text message to another user."""
        msgData = "{}:{}".format(recipientID, message)
        self.send(ds.DIALOG_SEND, msgData)

    @msgSetup
    def send_action(self, actionStr):
        """Allow the user to act in the world."""
        self.send(ds.ACTION_SEND, actionStr)

    def wait_for_dialogs(self, senderID=""):
        dialogs = self.get_dialogs(senderID)
        while dialogs == None:
            dialogs = self.get_dialogs(senderID)
            sleep(0.25)
        return dialogs

    @msgSetup
    def get_dialogs(self, senderID=""):
        self.send(ds.DIALOG_REQ, senderID)
        pickledDialogs = self.recv(4096)
        if pickledDialogs == "":
            return
        dialogs = loads(pickledDialogs)
        return dialogs


class OperatorClient(Client):
    """Client for operators."""

    def run(self):
        """Run both the input and update loops."""
        # inputThread = threading.Thread(target=self.input_loop)
        updateThread = threading.Thread(target=self.update_loop)
        updateThread.start()
        # inputThread.start()

    def input_loop(self):
        """Run a loop which allows the operator interact with the world."""
        while True:
            cmd = raw_input("")
            self.parse_command(cmd)

    def update_loop(self):
        """Run a loop which constantly feeds the user world state info."""
        while True:
            os.system('clear')
            print("Operator {}".format(self.userID))
            self.draw_perception()
            print("Messages: ")
            self.read_dialogs()
            print("Command>> ")
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
        self.send(ds.GOAL_SEND, "{}:{}".format(goalData[0], goalData[1]))

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
        self.send(ds.WORLD_STATE_REQ, "")
        sleep(0.1)
        return self.socket.recv(4096)

    @msgSetup
    def get_object_list(self):
        """Get and print a list of objects known to the user"""
        # Ask server for all pieces of info operator can give
        self.send(ds.UPDATE_SEND, "list")
        objsList = self.socket.recv(1024)
        # List these for user and ask user to select one
        print(objsList)


class MIDCAClient(Client):
    """Client which serves as a go between for a MIDCA instance and the sim world."""

    @msgSetup
    def agent(self):
        """Return the agent object corresponding to the client's userID."""
        self.send(ds.AGENT_REQ)
        pickledAgent = self.socket.recv(2048)
        agent = loads(pickledAgent)
        return agent

    @msgSetup
    def observe(self, display=False):
        """Have the agent observe the world. """
        self.send(ds.WORLD_STATE_REQ)
        if display:
            worldView = self.socket.recv(2048)
            os.system('clear')
            print(worldView)

    @msgSetup
    def get_new_goals(self):
        """Retrieve any new goals the server has waiting for the agent."""
        self.send(ds.GOAL_REQ)
        msgStr = self.socket.recv(2048)
        goalStrs = msgStr.split(":")
        return goalStrs


if __name__ == '__main__':
    userType = sys.argv[1].lower()
    port = int(sys.argv[2])
    name = sys.argv[3]
    if userType == "operator":
        opClient = OperatorClient('localhost', port, name)
        opClient.run()
    # TODO: Add code to allow a MIDCA agent to run here or something
