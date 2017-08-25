=================
Simulation Module
=================

The classes and functions in this module deal with running the simulations themselves, from the world to the agents and operators. The :py:class:`~world_communications.WorldServer` class is at the core of these operations, dealing with both simulating the world and facilitating communications between the agents and operators. The :py:class:`~world_communications.RemoteAgent` and :py:class:`~world_communications.AutoOperator` classes are what we use to run agents and operators, respectively. Finally, the :py:class:`~world_communications.Client` class and its subclasses :py:class:`~world_communications.MIDCAClient` and :py:class:`~world_communications.OperatorClient` are the classes which do all of the communication work between the agents and operators and the world server.

Originally, all aspects of the simulations were handled in a single MIDCA instance, with a special *simulation phase* which applied changes made by the MIDCA agent. However, this method allowed for only one agent, and required humans to act as manual operators, giving the agent goals by inputting them into the program. Additionally, the arrangement meant that the objective world state was tied into the agent itself, which made partial observability difficult to implement. As such, we developed a system in which the objective world state was held by a server, and agents and operators were only able to interact with it through socket communications (see `Python's socket library <https://docs.python.org/2/library/socket.html>`_ and this helpful `tutorial <https://docs.python.org/2/howto/sockets.html>`_). The :py:class:`~world_communications.WorldServer` class handles this, and contains an instance of a :py:class:`~world_utils.World` object which constitutes the objective world in which the agents and operators act.

In order to act in the world or communicate with other actors, an actor must first send a message to the server. The specific kinds of messages and their formats are laid out in more detail below, but the gist of it is that the agent or operator client sends a string over TCP that indicates the type of message, the sender of the message, and then encodes any relevant message data. The general format for such strings is::

    MSGTYPE:USERID:DATA

The types of messages which can be sent, and their individual formats, are:

.. autodata:: world_communications.WORLD_STATE_REQ

    Upon reception of a message of this type, the server updates the knowledge of the actor sending the message, then sends the client a pickled version of the :py:class:`~world_utils.WorldMap` object of the actor in question. A message of this type does not include any accompanying data, so its format looks like::

        1:USERID

.. autodata:: world_communications.ACTION_SEND

    Messages of this type allow actors to act in the world, and convey information pertaining to a single action taken by the sending actor. When the server receives this kind of message, it examines the accompanying data to understand which action is being taken, then applies it to the world. The data representing the action should be the string form of a MIDCA :py:class:`~MIDCA.plans.Action` object. The format for a message of this type looks like::

        2:USERID:ACTIONSTR

.. autodata:: world_communications.UPDATE_SEND

    Messages of this type allow actors to send updates to other actors. In particular, this kind of message is how actors inform other actors of the existences of objects (including NPCs) in the world. There are two subtypes of messages of this type: the ``list`` subtype and the ``send`` subtype. The ``list`` subtype collects all of the objects known to the sending agent's representation in the world and sends that list to the agent's MIDCA instance operating remotely. The ``send`` subtype requires a recipient and a target to be specified, where the recipient should be an actor and the target should be an object which the recipient is meant to learn about. The general formats for this kind of message are::

        3:USERID:list

    or::

        3:USERID:send:RECIPIENTID:OBJECTID


.. autodata:: world_communications.GOAL_SEND

    Messages of this kind allow actors to send goals to one another. Upon reception of this kind of message, the server stores the accompanying goal string in a list queue of goals for the specified actor. The format for messages of this type is::

        4:USERID:RECIPIENTID:GOALSTRING


.. autodata:: world_communications.GOAL_REQ

    Messages of this kind allow actors to receive the messages from their goal queue. The format is simply::

        5:USERID


.. autodata:: world_communications.AGENT_REQ


.. autodata:: world_communications.DIALOG_SEND


.. autodata:: world_communications.DIALOG_REQ


Classes
=======
.. autoclass:: world_communications.WorldServer
    :members:

.. autoclass:: world_communications.RemoteAgent
    :members:

.. autoclass:: world_communications.AutoOperator
    :members:

.. autoclass:: world_communications.Client
    :members:

.. autoclass:: world_communications.MIDCAClient
    :members:

.. autoclass:: world_communications.OperatorClient
    :members:
