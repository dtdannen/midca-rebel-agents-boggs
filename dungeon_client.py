"""
Holds the various server objects and functions for allowing two users.

This code is meant to allow to users to work with MIDCA simulataneously, without
needing to hot-seat a single terminal. It is fairly simple, with the server
sending out the world state, the client displaying that and then transmitting
user orders back to MIDCA.
"""
import SocketServer
import sys
import os


class DungeonClient(SocketServer.BaseRequestHandler):
    """
    Handles the clinet side of the Dungeon interaction.

    Listens for world-state updates, then prompts the user to give MIDCA a new
    goal. If the user gives a goal, it replies to the server with that goal.
    """
    def setup(self):
        """Set up the Dungeon client by getting the users position and view."""

    def handle(self):
        self.data = self.request.recv(4096)
        if self.data == "input":
            userInput = raw_input("Enter a goal or hit RETURN to continue.  ")
            self.request.sendall(userInput)
            if userInput == 'q':
                raise KeyboardInterrupt
        else:
            os.system('clear')
            world, goals, currGoals = self.data.split("~")
            print("World state:")
            print(world)
            print("All Goals:")
            print(goals)
            print("Current Goals:")
            print(currGoals)


if __name__ == '__main__':
    port = int(sys.argv[1])
    HOST, PORT = "localhost", port
    server = SocketServer.TCPServer((HOST, PORT), DungeonClient)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Shutting down client")
    finally:
        server.shutdown()
        server.close()
