"""This will contain the server and client classes for the Dungeon domain."""

import SocketServer as SS

import dungeon_utils


WORLD_STATE_REQ = 1
UPDATE_REQ = 2
ACTION_SEND = 3
UPDATE_SEND = 4


class DungeonServer(SS.TCPServer):
    """
    Special TCP server class which simulates the dungeon.

    Network interactions:
    User asking for world state --> Dungeon
        Dungeon replying with world state --> User

    Agent asking for world state --> Dungeon
        Dungeon replying with world state --> Agent

    User asking for MIDCA updates --> Dungeon
        Dungeon replying with stored MIDCA update --> User

    Agent asking for specific user commands/info --> Dungeon
        Dungeon replying with stored user command/info --> Agent

    User sending action --> Dungeon
        Dungeon simulates action

    Agent sending action --> Dungeon
        Dungeon simulates action

    User sending MIDCA command/info --> Dungeon
        Dungeon stores command/info (overwrites previous for this user)

    Agent sending update to user --> Dungeon
        Dungeon stores update (overwrites existing)
    """

    class HandlerClass(SS.StreamRequestHandler):
        """Custom handler class for a dungeon server."""

        # def __init__(self, request, client_address, server, dungeon):
        #     SS.StreamRequestHandler.__init__(self, request, client_address, server)
        #     self.dungeon = dungeon
        #     self.messages = {}
        #     print(dir(self))

        def handle(self):
            r"""
            Accept incoming messages and respond appropriately.

            The format for incoming messages should be:
            MSGTYPE:USERID:DATA\n
            The terminating newline is important!
            """
            dng = self.server.dungeon
            self.data = self.rfile.readline().strip()
            self.data = self.data.split(':')
            msgType = int(self.data[0])
            userID = self.data[1]
            msgData = self.data[2:] if len(self.data) > 2 else None

            if msgType == WORLD_STATE_REQ:
                user = dng.get_user(userID)
                self.wfile.write(user.draw_map)

            elif msgType == UPDATE_REQ:
                requestedID = msgData[0]
                update = self.messages[requestedID]
                self.wfile.write(update)

            elif msgType == ACTION_SEND:
                success = dng.apply_action(msgData[0], userID)
                if success:
                    self.wfile.write("success")
                else:
                    self.wfile.write("failure")

            elif msgType == UPDATE_SEND:
                self.messages[userID] = " ".join(msgData)

            else:
                raise NotImplementedError("Message type {}".format(msgType))

            return

    def __init__(self, server_address, dungeon, bind_and_activate=True):
        """Create server class."""
        SS.TCPServer.__init__(self, server_address, DungeonServer.HandlerClass, bind_and_activate)
        self.dungeon = dungeon


if __name__ == '__main__':
    addr = ('localhost', 9990)
    dng = dungeon_utils.build_Dungeon_from_file('dng_files/test.dng')
    testServer = DungeonServer(addr, dng)
    try:
        testServer.serve_forever()
    finally:
        testServer.shutdown()
