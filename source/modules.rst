MIDCA Modules
*************

Nearly every module which our rebel agent runs is one of our own, custom-made modules which interact with ``World`` and ``Agent`` objects. The only module which is not of our own make is the planning module, which uses MIDCA's built-in ``GenericPyhopPlanner``. Each of our modules is built to work with ``Agent`` objects as the state representation and either a ``MIDCAClient`` or ``OperatorClient`` as its world. Thus, anytime a module uses ``self.world`` it is accessing its client, and every time a module retrieves ``self.mem.STATE`` or ``self.mem.STATES`` it will be getting an ``Agent`` object. All of the modules our autonomous operators run are custom-made, and similarly only interact with clients. Agent and autonomous operator MIDCA cycles are listed below.

Agent MIDCA Cycle
-----------------

1. Perceive

    a. :py:class:`~modules.perceive.Observer`
    b. :py:class:`~modules.perceive.ShowMap`

2. Interpret

    a. :py:class:`~modules.interpret.CompletionEvaluator`
    b. :py:class:`~modules.interpret.StateDiscrepancyDetector`
    c. :py:class:`~modules.interpret.GoalValidityChecker`
    d. :py:class:`~modules.interpret.DiscrepancyExplainer`
    e. :py:class:`~modules.interpret.RemoteUserGoalInput`

3. Eval

    a. :py:class:`~modules.evaluate.GoalManager`
    b. :py:class:`~modules.evaluate.HandleRebellion`

4. Intend

    a. :py:class:`~modules.intend.QuickIntend`

5. Plan

    a. :py:class:`~modules.MIDCA.planning.GenericPyhopPlanner`

6. Act

    a. :py:class:`~modules.act.SimpleAct`

Autonomous Operator MIDCA Cycle
-------------------------------

1. Perceive

    a. :py:class:`~modules.perceive.OperatorObserver`

2. Interpret

    a. :py:class:`~modules.interpret.OperatorInterpret`

3. Eval

    a. :py:class:`~modules.evaluate.OperatorHandleRebelsFlexible`

4. Plan

    a. :py:class:`~modules.plan.OperatorPlanGoals`

5. Act

    a. :py:class:`~modules.act.OperatorGiveGoals`

All Modules
-----------

.. toctree::
    :maxdepth: 2

    modules/perceive
    modules/interpret
    modules/eval
    modules/intend
    modules/plan
    modules/act
