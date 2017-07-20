"""This will contain the server and client classes for the Dungeon domain."""

from cPickle import dumps, loads
import SocketServer as SS
import os
import time
import dungeon_utils


WORLD_STATE_REQ = 1
ACTION_SEND = 2
UPDATE_SEND = 3
GOAL_SEND = 4
GOAL_REQ = 5
AGENT_REQ = 6
DIALOG_SEND = 7
DIALOG_REQ = 8


class DungeonServer(SS.TCPServer):
    """
    Special TCP server class which simulates the dungeon.

    Network interactions:
    User asking for world state --> Dungeon
        Dungeon replying with world state --> User

    Agent asking for world state --> Dungeon
        Dungeon replying with world state --> Agent

    User sending action --> Dungeon
        Dungeon simulates action

    Agent sending action --> Dungeon
        Dungeon simulates action

    User sending MIDCA an update --> Dungeon
        Dungeon updates specified MIDCA agent's knowledge

    Agent sending update to user --> Dungeon
        Dungeon updates specified user's knowledge

    User sending MIDCA a command --> Dungeon
        Dungeon gives the command to the specified MIDCA agent
    """

    class HandlerClass(SS.StreamRequestHandler):
        """Custom handler class for a dungeon server."""

        def setup(self):
            SS.StreamRequestHandler.setup(self)
            os.system('clear')
            print(dng)

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
            r"""
            Accept incoming messages and respond appropriately.

            The format for incoming messages should be:
            MSGTYPE:USERID:DATA\n
            The terminating newline is important!
            """
            dng = self.server.dungeon
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
                self.wfile.write(str(user.map))

            elif msgType == ACTION_SEND:
                # Request format: ACTION_SEND:USERID:ACTIONSTR
                success = dng.apply_action_str(msgData[0], userID)

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

    def __init__(self, server_address, dungeon, bind_and_activate=True):
        """Create server class."""
        SS.TCPServer.__init__(self, server_address, DungeonServer.HandlerClass, bind_and_activate)
        self.dungeon = dungeon
        self.queuedGoals = {}
        self.messages = {}


if __name__ == '__main__':
    import sys
    port = int(sys.argv[1])
    dungeonFile = sys.argv[2]
    addr = ('localhost', port)
    dng = dungeon_utils.build_Dungeon_from_file(dungeonFile)
    testServer = DungeonServer(addr, dng)
    try:
        testServer.serve_forever()
    finally:
        testServer.shutdown()
