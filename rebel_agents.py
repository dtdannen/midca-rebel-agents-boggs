"""Allows command-line running of demos and tests."""
import sys
from getopt import getopt
from world_utils import interactive_World_maker, build_World_from_file
from testing import Testbed


def run_demos(demos):
    """
    Run one or more demos given as arguments.

    Arguments:
        ``demos``, *list*:
            A list of the demo filenames which should be run, without the
            filetype appended.

        ``return``, *None*
    """
    for demo in demos:
        if '/' not in demo:
            # If a folder isn't specified, default to the demos folder.
            demo = 'demos/{}.demo'.format(demo)
            kwargs = {}
            with open(demo, 'r') as demoFile:
                for line in demoFile:
                    line = line.strip()
                    arg, opt = line.split('=')
                    opt = eval(opt)
                    kwargs[arg] = opt
            if 'world' in kwargs:
                kwargs['world'] = build_World_from_file(kwargs['world'])
            tBed = Testbed(**kwargs)
            tBed.run_tests()
            tBed.testRecords.save_records()


if __name__ == '__main__':
    options = ''
    optlist, args = getopt(sys.argv[1:], options)

    if args[0] == "run":
        run_demos(args[1:])

    elif args[0] == "build":
        interactive_World_maker()
