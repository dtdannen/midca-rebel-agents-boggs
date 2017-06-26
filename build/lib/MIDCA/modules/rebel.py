import copy
import random

from MIDCA import base, goals


class UserGoalInputRebelRand(base.BaseModule):

    '''
    MIDCA module that allows users to input goals in a predicate representation.
    These will be stored in MIDCA goals of the form Goal(arg1Name, arg2Name...,
    argiName, predicate = predName). Note that this class only allows for simple
    goals with only predicate and argument information. It does not currently
    check to see whether the type or number of arguments is appropriate.
    '''
    def __init__(self, rebelChance=0.5):
        """
        Creates module which takes user input but can rebel randomly.

        0 <= rebelChance <= 1.0 dictates the chance of rebellion.
        """
        super(UserGoalInputRebelRand, self).__init__()
        self.rebChance = rebelChance

    def parseGoal(self, txt):
        if not txt.endswith(")"):
            print "Error reading goal. Goal must be given in the form: predicate(arg1, arg2,...,argi-1,argi), where each argument is the name of an object in the world"
            return None
        try:
            if txt.startswith('!'):
                negate = True
                txt = txt[1:]
            else:
                negate = False
            predicateName = txt[:txt.index("(")]
            args = [arg.strip() for arg in txt[txt.index("(") + 1:-1].split(",")]
            #use on-table predicate
            if predicateName == 'on' and len(args) == 2 and 'table' == args[1]:
                predicateName = 'on-table'
                args = args[:1]
            if negate:
                goal = goals.Goal(*args, predicate = predicateName, negate = True)
            else:
                goal = goals.Goal(*args, predicate = predicateName)
            return goal
        except Exception:
            print "Error reading goal. Goal must be given in the form: predicate(arg1, arg2,...,argi-1,argi), where each argument is the name of an object in the world"
            return None

    def objectNames(self, world):
        return world.objects.keys()

    def predicateNames(self, world):
        return world.predicates.keys()

    def validGoal(self, goal, world):
        try:
            for arg in goal.args:
                if arg not in self.objectNames(world):
                    return False
            return goal['predicate'] in self.predicateNames(world)
        except Exception:
            return False

    def run(self, cycle, verbose = 2):
        if verbose == 0:
            return #if skipping, no user input
        goals_entered = []
        while True:
            val = raw_input("Please input a goal if desired. Otherwise, press enter to continue\n")
            if not val:
                return "continue"
            elif val == 'q':
                return val
            goal = self.parseGoal(val.strip())
            if goal:
                world = self.mem.get(self.mem.STATES)[-1]
                if not self.validGoal(goal, world):
                    print str(goal), "is not a valid goal\nPossible predicates:", self.predicateNames(world), "\nPossible arguments", self.objectNames(world)
                    continue

                rebel, explan = self.choose_rebel(goal)
                if rebel:
                    print("Agent has chosen to rebel against {} because {}".format(str(goal), explan))
                else:
                    self.mem.get(self.mem.GOAL_GRAPH).insert(goal)
                    print("Agent has chosen to accept {} because {}".format(str(goal), explan))
                    print "Goal added."
                    goals_entered.append(goal)

        trace = self.mem.trace
        if trace:
            trace.add_module(cycle,self.__class__.__name__)
            trace.add_data("USER GOALS", goals_entered)
            trace.add_data("GOAL GRAPH", copy.deepcopy(self.mem.GOAL_GRAPH))

    def choose_rebel(self, goal):
        """
        Choose whether the agent rebels against the human goal.

        To choose whether to rebel, the agent generates a random number [0., 1)
        and compares it a threshold. The threshold is initially set, but changes
        as the rebel chooses to rebel or not rebel. Every time the agent accepts
        a goal, the chance of it rebelling increases by 10%. Every time it rebels,
        the chance of a subsequent rebellion decreases by 10%.
        """
        roll = random.random()
        rebel = roll < self.rebChance
        explan = "the agent rolled a {} against a {} chance.".format(roll, self.rebChance)
        self.rebChance = self.rebChance - .1 if rebel else self.rebChance + .1
        return rebel, explan


class Introspection(base.BaseModule):
    """
    Module which makes MIDCA regurgitate some of its memory.
    """

    def run(self, cycle, verbose=2):
        if verbose == 0:
            return
        curState = self.mem.get(self.mem.STATE)

        curGoals = self.mem.get(self.mem.CURRENT_GOALS)
        if curGoals:
            curGoals = [str(g) for g in curGoals]

        plans = self.mem.get(self.mem.PLANS)
        if plans:
            plans = [str(p) for p in plans]

        actions = self.mem.get(self.mem.ACTIONS)
        if actions:
            actions = [[str(a) for a in b] for b in actions]

        goalsAchieved = self.mem.get(self.mem.GOALS_ACHIEVED)

        curPlan = self.mem.get(self.mem.CURR_PLAN)
        print("""Current State: {}
Current Goals: {}
Plans: {}
Actions: {}
Goals Achieved: {}
Current Plan: {}""".format(curState, curGoals, plans, actions, goalsAchieved, curPlan))
