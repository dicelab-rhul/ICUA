#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    Created on 25-10-2020 15:27:44

    [Description]
"""
__author__ = "Benedict Wilkins"
__email__ = "benrjw@gmail.com"
__status__ = "Development"


import argparse
import os

from icua.environment import ICUEnvironment
from icua.agent import FuelMonitor, TrackMonitor, SystemMonitor, Evaluator
from icua.agent.users import User, PerfectUser, DelayedUser, FixatedUser, FixedUser

class PathAction(argparse.Action):

    def __call__(self, parser, namespace, path, option_string=None):
        setattr(namespace, self.dest, os.path.abspath(path))
            
parser = argparse.ArgumentParser(description='ICU')

parser.add_argument('--config', '-c', metavar='C', action=PathAction, type=str, help='path of the ICU config file to use.')

args = parser.parse_args()

NUM_EXPERIMENTS = 10

for fix in ['fuel']:
    
    for dif in ['med']:
        config = os.path.abspath("config/{0}-config.json".format(dif))

        file = "experiment4/results-{0}-{1}.txt".format(fix, dif)

        with open(file, "w") as f:
            f.write("# AVERAGED OVER {0} RUNS".format(NUM_EXPERIMENTS))

        for delay in [0, 0.1, 0.5, 1., 2., 4.]:

            with open(file, "a") as f:
                f.write("\n# DELAY {0}".format(delay))

            for i in range(NUM_EXPERIMENTS):
                
                agents = [FuelMonitor, SystemMonitor, TrackMonitor, lambda *args, delay=delay: FixedUser(*args, fix, delay=delay), Evaluator]

                env = ICUEnvironment(*agents, config=config)
                env.simulate()

                evaluator = [a for a in env.ambient.agents.values() if hasattr(a.mind, "result")][0].mind

                with open(file, "a") as f:
                    f.write("\n# RUN {0}".format(i))
                    f.write(evaluator.result)

            

    