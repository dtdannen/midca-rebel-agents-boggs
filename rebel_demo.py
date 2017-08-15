"""
MIDCA demo using a world-ish environment.

Agent explores a world with a limited view.
"""

import json
import logging

# Domain Specific Imports
import world_utils
import testing

WORLD_LOGGER = logging.getLogger("WorldEvents")
handler = logging.FileHandler("logs/world_events.log")
formatter = logging.Formatter(fmt="%(asctime)s:%(funcName)s: %(message)s",
                              datefmt="%M:%S")
WORLD_LOGGER.setLevel(logging.INFO)
handler.setLevel(logging.INFO)
handler.setFormatter(formatter)
WORLD_LOGGER.addHandler(handler)

WORLD_FILE = './dng_files/proactiveTest.dng'
world = world_utils.build_World_from_file(WORLD_FILE)
world.log = WORLD_LOGGER

TEST_NUM = 7
REJECTION_PROB_STEP = 1.0
COMPLIANCE_STEP = -0.5


# testing.run_test(world)


compliance = 1.0
scores = {}
while 0 <= compliance <= 1.0:
    rejectionProb = 0.0
    while rejectionProb <= 1.0:
        key = str((rejectionProb, compliance))
        scores[key] = []
        for test in range(TEST_NUM):
            world = world_utils.generate_random_drone_demo(dim=20,
                                                           civilians=25,
                                                           enemies=30,
                                                           operators=1,
                                                           agents=5,
                                                           log=WORLD_LOGGER)
            score = testing.run_test(world, limit=60, rebel=True,
                                     rejectionProb=rejectionProb,
                                     compliance=compliance)
            scores[key].append(score)
            print(score, test, key)
        rejectionProb += REJECTION_PROB_STEP
    compliance += COMPLIANCE_STEP


print(scores)
with open('results.txt', 'w') as resFile:
    json.dump(scores, resFile)
