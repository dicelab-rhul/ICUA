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
from icua.agent.users import User, PerfectUser, DelayedUser

class PathAction(argparse.Action):

    def __call__(self, parser, namespace, path, option_string=None):
        setattr(namespace, self.dest, os.path.abspath(path))
            
parser = argparse.ArgumentParser(description='ICU')

parser.add_argument('--config', '-c', metavar='C', action=PathAction, type=str, help='path of the ICU config file to use.')

args = parser.parse_args()

agents = [FuelMonitor, SystemMonitor, TrackMonitor, PerfectUser, Evaluator]

NUM_EXPERIMENTS = 10

for i in range(NUM_EXPERIMENTS):
    env = ICUEnvironment(*agents, **args.__dict__)
    env.simulate()

    evaluator = [a for a in env.ambient.agents.values() if hasattr(a.mind, "result")][0].mind
    with open("results_perfect_user.txt", "a") as f:
        f.write("# PERFECT USER {0}".format(i))
        f.write(evaluator.result)
