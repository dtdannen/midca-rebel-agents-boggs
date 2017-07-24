MIDCA Modules
*************

Nearly every module which our rebel agent runs is one of our own, custom-made modules which interact with ``World`` and ``Agent`` objects. The only module which is not of our own make is the planning module, which uses MIDCA's built-in ``GenericPyhopPlanner``. Each of our modules is built to work with ``Agent`` objects as the state representation and either a ``MIDCAClient`` or ``OperatorClient`` as its world. Thus, anytime a module uses ``self.world`` it is accessing its client, and every time a module retrieves ``self.mem.STATE`` or ``self.mem.STATES`` it will be getting an ``Agent`` object.

Current, we have MIDCA running the following phases and modules:

1. Perceive

    a. ``perceive.Observer``
    b. ``perceive.ShowMap``

2. Interpret

    a. ``interpret.CompletionEvaluator``
    b. ``interpret.StateDiscrepancyDetector``
    c. ``interpret.GoalValidityChecker``
    d. ``interpret.DiscrepancyExplainer``
    e. ``interpret.RemoteUserGoalInput``

3. Eval

    a. ``evaluate.GoalManager``
    b. ``evaluate.HandleRebellion``

4. Intend

    a. ``intend.QuickIntend``

5. Plan

    a. ``MIDCA.planning.GenericPyhopPlanner``

6. Act

    a. ``act.SimpleAct``

.. toctree::
    :maxdepth: 2

    modules/perceive
    modules/interpret
    modules/eval
    modules/intend
    modules/plan
    modules/act
