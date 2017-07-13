"""
Holds the various server objects and functions for allowing two users.

This code is meant to allow to users to work with MIDCA simulataneously, without
needing to hot-seat a single terminal. It is fairly simple, with the server
sending out the world state, the client displaying that and then transmitting
user orders back to MIDCA.
"""
import socket
from time import sleep

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(('localhost', 9990))
s.send('1:1:1:1\n')
print(s.recv(2048))
