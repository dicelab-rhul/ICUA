#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    Created on 24-07-2020 17:45:14

    [Description]
"""
__author__ = "Benedict Wilkins"
__email__ = "benrjw@gmail.com"
__status__ = "Development"


import argparse
import os

from .environment import ICUEnvironment
from .agent import FuelMonitor, TrackMonitor, SystemMonitor, User, Evaluator

class PathAction(argparse.Action):

    def __call__(self, parser, namespace, path, option_string=None):
        setattr(namespace, self.dest, os.path.abspath(path))
            
parser = argparse.ArgumentParser(description='ICU')

parser.add_argument('--config', '-c', metavar='C', action=PathAction, type=str, help='path of the ICU config file to use.')

args = parser.parse_args()

#agents = [FuelMonitor, TrackMonitor, SystemMonitor]
agents = [User]
agents = [FuelMonitor, TrackMonitor, SystemMonitor, User]
agents = [Evaluator]


env = ICUEnvironment(*agents, **args.__dict__)
env.simulate()

