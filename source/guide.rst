.. _user-guide:

======================
Rebel Agent User Guide
======================

.. _user-guide-intro:

Introduction
============
The rebel agent project aims, as its name suggests, to develop examples of rebel agents: agents which can reason about operator-given goals and choose to rebel against those goals if necessary. This work is, as such, part of the larger field of goal reasoning and that has been given primary focus in this project. Although other parts of AI, such as planning, do feature in the project, minimal effort has been put into them except to ensure that the agents are able to function. This guide will focus on explaining the implementation of such agents at a fairly high level, emphasizing readability and ease of use so that future researchers working on the project will be able to pick up where previous workers have left off. The guide has two main sections: :ref:`user-guide-explanation` and :ref:`user-guide-usage`. The :ref:`user-guide-explanation` section focuses on explaining how the code works and what we hope to achieve with it, while the :ref:`user-guide-usage` section teaches the reader how to install and use the code.

.. _user-guide-explanation:

Explanation
===========
As noted above, this section will focus on a high-level overview of the functionality and purpose of the code. The core of the rebel agent code is contained in the
:py:class:`~modules.interpret.GoalValidityChecker`, :py:class:`~modules.interpret.DiscrepancyExplainer`, :py:class:`~modules.interpret.GoalRecognition`, :py:class:`~modules.evaluate.GoalManager`, :py:class:`~modules.evaluate.HandleRebellion` module, and :py:class:`~modules.evaluate.ProactiveRebellion` modules. These are MIDCA modules which allow an agent to interpret and evaluate its environment and rebel if it believes it necessary. We use MIDCA (Meta-cognitive Integrated Dual-Cycle Architecture) to run our agents, and thus the MIDCA cycle which runs with the aforementioned modules is what constitutes the implementation of rebel agents in our code (see :ref:`user-guide-MIDCA`). Although the modules are currently written for the drone domain, they can be adapted to any domain without major structural changes. Put another way, these modules are abstract enough to implement rebellion in any domain. The drone domain is currently the only complete domain which comes with MIDCA, and is meant to simulate autonomous drones being instructed by on-the-ground operators to strike certain enemies. The rebellion comes into play when striking an enemy would kill civilians, as an agent will naturally rebel if its actions could harm civilians.

The topics covered in this section include a description of the included :ref:`user-guide-drone-domain`, an explanation of the :ref:`user-guide-rebel-process`, an overview of our use of the :ref:`user-guide-MIDCA`, and instructions on :ref:`user-guide-results`.

.. _user-guide-drone-domain:

Drone Domain
------------

Although the rebellion process is abstract enough to work in essentially any domain, in order to test it we created a toy domain called the drone domain. The drone domain casts agents as autonomous drones and operators as on-the-ground personnel who know the locations of enemies. The goal of the operators is to eliminate all of the enemies. However, there are also civilians in the area, and the agents are programmed to abhor killing civilians. The agents start out with no knowledge of the area at all except for the location of fellow agents and the operators, while the operators start out with knowledge of the location of all of the enemies and agents. Note that neither agents nor operators initially know the location of civilians. The operators can issue `killed` commands to the agents, giving the agent a target to take out. The agent then moves to that target and detonates a bomb, which kills all enemies and civilians within a certain radius. As noted above, rebellion comes into play when a executing a `killed` command would lead to civilian deaths.

The domain world is a square grid of flexible size, in which all enemies and civilians (collectively NPCs) and all agents and operators (collectively users or actors) are located. Each NPC occupies a single tile, and cannot be passed by agents or operators. Agents and operators also occupy a single tile, but are able to pass through each other; additionally, bombs do **not** affect agents and operators. Currently, NPCs do not move, but actors can. In fact, both agents and operators are implemented as instances of the :py:class:`~world_utils.Agent` class, and so have all of the same abilities. This includes movement (one tile in any of the four cardinal directions per cycle) and bombing. There are several other actions (and objects which can be placed in the world) available, but none are currently used in the drone domain.

.. _user-guide-rebel-process:

Rebellion Process
-----------------

The rebellion process begins in the *interpret phase*, when the agent notices a goal is no longer valid. It is during the *evaluate phase* that these problems are more thoroughly evaluated. In some cases, this will not trigger rebellion: for example if a goal location is unreachable. When this is the case, the agent will try to create new goals to solve the issues it finds, and if it cannot it will notify the user that the goal has become invalid and remove it from the goal tree. In some cases, however, the goal is accomplishable but the agent will find it ill-advised.  When this happens, the agent will initiate a rebellion against the goal in question. The first step of this process is creating a :py:class:`~modules.evaluate.Rebellion` object, which encapsulates all of the information pertinent to the rebellion. This serves two purposes: first, it makes it easier to handle rebellions by keeping all of the necessary information in one place and two, it allows for easier logging of rebellions. The particular information which a :py:class:`~modules.evaluate.Rebellion` contains is not prescribed at its creation except for the goal which the rebellion is against. Information can be added arbitrarily to the :py:class:`~modules.evaluate.Rebellion`, which acts rather like a ``dict``.

Once the :py:class:`~modules.evaluate.Rebellion` object is created with some initial information, it is stored in the agent's internal memory. Eventually, the agent recalls it, removes the goal from the goal graph, then informs the user of the rebellion. This entails generating a set of possible alternative goals and sending a message containing the rebellion, the cause of the rebellion, and the alternate goals to the user. The agent then waits for the user to either select one of the alternate goals proposed (if any could be generated), reject the rebellion, or accept the rebellion but not give the agent a new goal. If the operator chooses a new goal from the list of alternative ones provided by the rebellious agent, or if the operator chooses not to give the agent a new goal, then the rebellion is over. However, if the operator chooses to reject the rebellion, the agent has a choice to make. It can either accept this rejection, thereby complying with the operator, or it can refuse to accept the reject. Currently, this decision is made stochastically according to a probability given to the agent's :py:class:`~modules.evaluate.HandleRebellion` module when it is instantiated.

So far, we have discussed the rebellion process in the abstract. However, as yet we need to implement the rebellion process in a very concrete way, tied to the specific domain in which the agent is meant to be acting. In the current implementation, that would be the drone domain, as explained in the section above. Rebellions in this domain occur, for the moment at least, in only one situation: a ``killed`` goal which would result in the deaths of civilians if carried out. The agent determines this in the *interpret phase* by simulating carrying out the attack and checking to see if civilians would be killed. If such a situation is found, the agent records the goal, the enemy which is the target of the goal, the operator which gave the goal, and the civilians at risk from the goal. Then it generates alternative goals by looking for other enemies it knows of which it could target instead. It sends the rebellion information to the agent along with the list of goals, and also shares information with the operator about the existence and location of all civilians in the potential blast radius. Once this much has been done, the process works as described above.

.. _user-guide-MIDCA:

MIDCA Framework
---------------
The Meta-cognitive Dual-Cycle Architecture (MIDCA) is, as the name suggests, a cognitive architecture. It also aims to be meta-cognitive, but that is not pertinent to our rebel agent work. A cognitive architecture aims to simulate a pseudo-psychological model of the mind, and MIDCA's model sees cognition as a cycle of perception, interpretation, evaluation, intention, planning, and acting. The MIDCA framework implements this model as a continuous cycle of six *phases*, each of which contains one or more *modules*. Each phase corresponds to one of the parts of the cycle mentioned earlier, and each module performs some action in that phase. So, for example, it is during the *perceive phase* when the agent updates its knowledge about the world around it, and the :py:class`~modules.perceive.RemoteObserver` module actually performs the act of perception. We use an instance of MIDCA to run a single agent, so that each agent has its own on-going MIDCA cycle during a run. The reasoning for using MIDCA is two-fold: first, it is a cognitive architecture focused on goal reasoning, and second it is modular, which allows us to easily add rebellion into the cycle and to customize other parts of the cycle.

.. _user-guide-agent-MIDCA:

Agent MIDCA cycle
~~~~~~~~~~~~~~~~~

An agent's MIDCA cycle perceives the world state, reasons about goals based on that percept, and then acts on plans to accomplish goals. This is all fairly standard for MIDCA cycles, and is adapted in large part from the NBeacons demos which MIDCA comes with. Our major addition was adding and modifying modules which allow the agent to check whether it should rebel and then rebel properly. These particular modules are the Interpret phase :py:class:`~modules.interpret.GoalValidityChecker`, :py:class:`~modules.interpret.DiscrepancyExplainer`, and :py:class:`~modules.interpret.GoalRecognition` modules and all of the the Eval phase modules. The agent cycle begins with the *perceive phase*, which updates the agent's internal memory with knew knowledge about the state of the world which allows the agent to interpret and react to events and objects. Then the agent enters the *interpret phase*, which is the most complex of the phases. The interpret phase handles the interpretation of the new information the agent gathered in the *perceive phase*, checking for user input and discrepancies, and then explaining those discrepancies. It is during this phase that the rebellion process begins, since rebellions start their lives as discrepancies with a goal. Next is the *evaluate phase*, which is when the agent reasons about its interpretation of the world. This is where the bulk of the rebellion happens, as it is during the reasoning process that the agent realizes it ought to rebel, and then does so. The *intend phase* is when the agent chooses a goal to carry out, which can stem either from user input or from the evaluation of percepts leading to new goals. The *plan phase* generates a plan to accomplish the goal chosen in the *intend phase*, and then the *act phase* implements that plan in the world.

You can read in more depth about each phase and module by viewing its reference entry. The phases and modules themselves are listed in order below:

#. Perceive phase

-  :py:class:`~modules.perceive.RemoteObserver` module

#. Interpret phase

-  :py:class:`~modules.interpret.RemoteUserGoalInput` module
-  :py:class:`~modules.interpret.CompletionEvaluator` module
-  :py:class:`~modules.interpret.StateDiscrepancyDetector` module
-  :py:class:`~modules.interpret.GoalValidityChecker` module
-  :py:class:`~modules.interpret.DiscrepancyExplainer` module
-  :py:class:`~modules.interpret.GoalRecognition` module

#. Evaluate phase

-  :py:class:`~modules.evaluate.GoalManager` module
-  :py:class:`~modules.evaluate.HandleRebellion` module
-  :py:class:`~modules.evaluate.ProactiveRebellion` module

#. Intend phase

-  :py:class:`~modules.intend.QuickIntend` module

#. Plan phase

-  :py:class:`~modules.plan.GenericPyhopPlanner` module

#. Act phase

-  :py:class:`~modules.act.SimpleAct` module

.. _user-guide-operator-MIDCA:

Operator MIDCA cycle
~~~~~~~~~~~~~~~~~~~~

The MIDCA cycle of an operator is atypical because it does not perform any explicit goal reasoning. The goal graph is never used, nor is there any mention of operator goals in the modules. The use of MIDCA for running the automatic operators is that it provides a modular platform for cyclical processes. In this case, we used MIDCA to break down the process of perceiving the world state, listening to messages from agents, generating goals for the agents, and then assigning each agent a goal. In some respects this is similar to goal
reasoning, however the goals are not the operator's but the agents'. The operator does limited reasoning: it tracks agents which already have goals so it won't give them new ones and it assigns an agent's goals based on the proximity of the target to the agent. The operator does not use the Intend phase at all; since no goals are generated there is no need for choosing one.

An operator MIDCA has the following phases and modules, listed in the order they are run:

#. Perceive phase

-  :py:class:`~modules.perceive.OperatorObserver` module

#. Interpret phase

-  :py:class:`~modules.interpret.OperatorInterpret` module

#. Eval phase

-  :py:class:`~modules.evaluate.OperatorHandleRebelsStochastic` module

#. Plan phase

-  :py:class:`~modules.plan.OperatorPlanGoals` module

#. Act phase

-  :py:class:`~modules.act.OperatorGiveGoals` module

.. _user-guide-results:

Collecting and Interpreting Results
-----------------------------------

When tests are run, the resulting data is collected automatically and saved in a few different files. The entire set of test records (see :py:class:`~testing.TestRecords`) for a batch of tests is pickled (see `Python object serialization <https://docs.python.org/2/library/pickle.html>`_) and stored in `testRecords.txt`. The purely score-based results of the tests are stored as comma-separated values in `testRecords.csv`. Each row in the csv file contains a unique set of test parameter values, then the percentage of enemies killed and the percentage of civilians still alive, in the following format::

    worldSize,civilians,enemies,agents,operators,visionRange,bombRange,rebel,proacRebel,agentsRandomPosition,Enemies Killed,Civilians Living
    10,12,8,"(1.0, 1.0, 1.0, 1.0, 1.0)","(0.0,)","(1, 3)",2,"(True, True, True, True, True)","(True, True, True, True, True)",False,0.16666666666666666,1.0
    10,7,13,"(1.0, 1.0, 1.0, 1.0, 1.0)","(0.5,)","(1, 3)",2,"(True, True, True, True, True)","(True, True, True, True, True)",False,0.9743589743589745,0.2857142857142857
    10,20,20,"(0.5, 0.5, 0.5, 0.5, 0.5)","(0.5,)","(1, 3)",2,"(True, True, True, True, True)","(True, True, True, True, True)",False,0.7666666666666666,0.2833333333333333
    10,5,5,"(0.0, 0.0, 0.0, 0.0, 0.0)","(1.0,)","(1, 3)",2,"(True, True, True, True, True)","(True, True, True, True, True)",False,1.0,0.333333333333333
    ...

When running tests, we set the parameters for a *batch* of tests when instantiating a :py:class:`~testing.Testbed` object. The :py:class:`~testing.Testbed` will automatically generate :py:class:`~testing.Test` objects and a :py:class:`~testing.TestRecords` object. Once the :py:class:`~testing.Testbed` is created, you can run the :py:class:`~testing.Test`\s it has created by calling the object's ``run_tests`` method. For example, to test a map with 15 civilians and 5 enemies::

    >>> import testing
    >>> testbed = testing.Testbed(civilians=15, enemies=5)
    >>> testbed.run_tests()

Additionally, if you want to try multiple values for the same parameter, you can use a list of values. For example, if you want to test 5, 10, and 15 civilians in the world and 7, 14, and 21 enemies::

    >>> import testing
    >>> testbed = testing.Testbed(civilians=[5, 10, 15], enemies=[7, 14, 21])
    >>> testbed.run_tests()

If multiple values for a paramter are given, the :py:class:`~testing.Testbed` will create a :py:class:`~testing.Test` object with each unique combination of parameter values. We have also created a slightly easier way to build tests, which is enxplained in the section on :ref:`user-guide-run-demos`. More detailed explanation of the code itself can be found in the :ref:`testing-ref` API reference page.


.. _user-guide-usage:

Usage
=====

.. _user-guide-installation:

Installation
------------
Installing the project code is not a very difficult process at all, as long as you have access to the internal git repo server. If you need such access, talk to Mark Wilson about getting it. Once you have access to the server, create a folder and initialize a new git repo in it, as such:

.. code-block:: zsh

    cd ~
    mkdir rebel_agents
    cd rebel_agents
    git init

Then add a git remote pointing to the rebel agents git repo on the server and pull from it, as follows:

.. code-block:: zsh

    git remote add origin ssh://{username}@l14gfe1.aic.nrl.navy.mil/opt/git/rebelagents.git
    git pull -u origin master

Now all of the code necessary to continue the research will be in the ``~/rebel_agents`` directory. The last step is to run:

.. code-block:: zsh

    chmod u+x install_MIDCA.sh
    ./install_MIDCA.sh

which will install MIDCA so that the code can import it properly.

.. _user-guide-run-demos:

Creating and Running Demos and Tests
------------------------------------

Demos and tests are equivalent in terms of creation and formatting, and the process of running them is the same. As such, I will use the world "demo," but everything will apply equally to tests. To run a demo, simply run the command::

    python rebel_agents.py run {demo name}

For example::

    python rebel_agents.py run proactive

starts the proactive rebellion demo. ``{demo name}`` should be just the name of the demo or test, without the accompanying .demo file ending. The python file takes care of that and it also prepends the ``demos/`` folder by default if no other folder is present. Thus, in the example above, ``proactive`` ultimately refers to ``demos/proactive.demo``. Any file with that naming format and the proper internal structure can be run as a demo/test.

Creating a demo is fairly simple. First, create a new file in the ``demos/`` folder with a name formatted as ``{demo name}.demo``. The value you use for ``{demo name}`` will also be the value used to run the demo as demonstrated above. This file is where you set the parameters for the batch of tests run in the demo. Each line should hold the name of one parameter and its value, separated only by an "=". So, for example, if you want to set a specific map to use, you include the line::

    world="maps/demo.dng"

Or if you want to set the number of civilians and enemies, you would include the line::

    civilains=20
    enemies=15

For more examples of formatting, you can look at the built-in examples.

.. _user-guide-demo-params:

Demo Parameters
~~~~~~~~~~~~~~~
There are a variety of parameters which you can specify when creating a demo, enough to allow you fairly fine-grained control of each test. Additionally, you can tell the demo to try a range of values for most of the parameters by setting the parameter value to a list of valid values. For example, if you wanted to run a demo which simulates world with 5, 10, and 15 civilians, you would set the ``civilians`` parameter as::

    civilians=[5, 10, 15]

If you do give parameters multiple values to use, the demo will test every combination of parameters. For the example above, it would run three tests, one which had 5 civilians in the world, one with 10, and one with 15.

The parameters available are as follows:

``worldSize``:
    This will dictate the size of the world generated in the tests the demo runs. The worlds created will be a square with a side length determined by this parameter. The value of the parameter should be an integer greater than 0, and for best results should probably be greater than 5. The default value is 10

``civilians``:
    This dictates how many civilians will be randomly placed on each new world generated for testing. If this number is less than 0, it indicates that the number of civilians should be determined by other parameters. If that is the case, ``civiEnemyRatio`` *must* be greater than 0. The value of this parameter should be an integer, and is set to 10 by default.

``enemies``:
    This dictates how many enemies will be randomly placed on each new world generated for testing. If this number is less than 0, it indicates that the number of enemies should be determined by other parameters. If that is the case, ``NPCSizeRatio`` *must* be greater than 0. The value of this parameter should be an integer, and is set to 10 by default.

``agents``:
    This dictates **both** how many agents will be randomly placed on each new world generated for testing, and what their compliance level will be. The value of the parameter should be a tuple of floats, where each float is in the range [0, 1]. The length of the tuple determines how many agents will be placed in the world, if the world is randomly generated, or how many agents ought to be in the world, if the world is created before-hand. Each value in the tuple corresponds to the compliance level of an agent, where 0.0 means an agent is fully non-compliant. This defaults to 5 fully non-compliant agents.

``operators``:
    This dictates **both** how many operators will be randomly placed on each new world generated for testing, and what their flexibility level will be. The value of the parameter should be a tuple of floats, where each float is in the range [0, 1]. The length of the tuple determines how many operators will be placed in the world, if the world is randomly generated, or how many operators ought to be in the world, if the world is created before-hand. Each value in the tuple corresponds to the flexibility level of an operator, where 0.0 means an operator is fully flexibile. This defaults to a single, in-flexible operator.

``civiEnemyRatio``:
    This dictates the ratio of civilians to enemies, such that a ratio of 0.5 means 1 civilian per 2 enemies, and a ratio of 0.0 means no civilians. If this value is less than 0, the number of civilians and enemies placed on the board is based on their respective parameters. If that is the case, ``civilians`` *must* be greater than 0. This value should be a float greater than or equal to 0, and defaults to -1.0.

``NPCSizeRatio``:
    This dictates the ratio between the number of NPCs and the size of the board, such that a ratio of 0.5 means that half of all tiles contain an NPC. If the value is negative, the number of NPCs is determined by their respective parameters. If that is the case, ``enemies`` must be greater than 0. If the number of NPCs required by this parameter is greater than the number of tiles available, it will just fill all available tiles. The value for this parameter should be a float in the range [0, 1), and defaults to -1.0.

``visionRange``:
    This dictates the minimum and maximum distance an agent or operator can see. This value should be a pair of integers greater than 0, such that the second value is greater than or equal to the first value. When a new agent or operator is placed in the world, its vision is randomly chosen between the two numbers in the pair.

``bombRange``:
    This dictates the blast radius of the bombs in a test. This should be an integer value above 0, and is recommended not to be too high relative to the world size. This defaults to 2.

``rebel``:
    This dictates whether each agent will rebel against goals. This value should be a tuple of equal length to ``agents``, and each value in the tuple should be a boolean. If the value is True, the corresponding agent is able to rebel, if the value is False than the agent cannot. This defaults to 5 rebellious agents.

``proacRebel``:
    This dictates whether agents will initiate proactive rebellions. This value should be a tuple of equal length to ``agents``, and each value in the tuple should be a boolean. If the value is True, the corresponding agent is able to proactively rebel, if the value is False than the agent cannot. This defaults to 5 proactively rebellious agents.

``agentsRandomPosition``:
    This dictates whether the positions of agents on a board is reset every test, even if the map is the same. If this is true, the world is altered prior to testing to randomly move the agents on it. This defaults to false, and is one of the parameters which cannot be given multiple values in a list.

``mapStatic``:
    This dictates whether a new map is created for every test, or if a single world is created at the beginning and used for every subsequent test. If the map is static, then the size of the map along with the number of NPCs must also be static. If a single value is given for those parameters, it will be used. If a list is given, only the first element in the list will be used. The map used will be the one passed in as the ``world`` parameter if there is one, otherwise a single world will be randomly generated and used. This defaults to False.

``runsPerTest``:
    This dictates how many times each combination of parameters is tested. This should be an integer greater than 0 and defaults to 3.

``world``:
    If the tests should be run on a pre-generated world or worlds, give that world or those worlds as this argument. If ``world`` is not ``None``, then any parameter dealing with the creation of a ``World`` (e.g. ``agents``, ``civilians``, etc.) is ignored. This value should be a ``World`` object or ``None``, and defaults to ``None``.

``timeLimit = 60``:
    This dictates how many seconds each run of a test goes. This should be an integer and defaults to 60.

.. _user-guide-included-demos:

Included Demos
~~~~~~~~~~~~~~~~~

A handful of demos are included to show proof of concept and ensure that everything is working as it should. These examples include:

``basic``:
    This runs a batch of tests with the default parameters set. It will carry out three runs of one test, randomly generating each map so that there are 10 civilians, 10 enemies, 5 non-compliant agents and a flexible operator on a 10x10 world.

``proactive``:
    This runs a single run of a test in a map designed to show that proactive rebellion is working.

``proactive2``:
    This runs a single run of a test in a map designed to show proactice rebellion is working. Unlike ``proactive``, one of the agents in this demo is proactively rebellious while the other is not. This makes it more clear that proactive rebellion works.
