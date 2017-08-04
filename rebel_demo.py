"""
MIDCA demo using a world-ish environment.

Agent explores a world with a limited view.
"""

import json
import logging

# Domain Specific Imports
import world_utils
import testing

WORLD_FILE = './dng_files/largeMultiAgent.dng'
world = world_utils.build_World_from_file(WORLD_FILE)

TEST_NUM = 10
REJECTION_PROB_STEP = 0.5

WORLD_LOGGER = logging.getLogger("WorldEvents")
handler = logging.FileHandler("logs/world_events.log")
formatter = logging.Formatter(fmt="%(asctime)s:%(funcName)s: %(message)s",
                              datefmt="%M:%S")
WORLD_LOGGER.setLevel(logging.INFO)
handler.setLevel(logging.INFO)
handler.setFormatter(formatter)
WORLD_LOGGER.addHandler(handler)


rejectionProb = 0.0
scores = {}
while rejectionProb <= 1.0:
    scores[rejectionProb] = []
    for test in range(TEST_NUM):
        world = world_utils.generate_random_drone_demo(dim=15,
                                                       civilians=12,
                                                       enemies=10,
                                                       operators=1,
                                                       agents=5,
                                                       log=WORLD_LOGGER)
        score = testing.run_test(world, moveLimit=100, rebel=True, rejectionProb=rejectionProb)
        scores[rejectionProb].append(score)
        print(score, test, rejectionProb)
    rejectionProb += REJECTION_PROB_STEP

print(scores)
with open('results.txt', 'w') as resFile:
    json.dump(scores, resFile)
