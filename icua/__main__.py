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
from .agent import FuelMonitor, TrackMonitor, SystemMonitor, Evaluator
from .agent.users import User, PerfectUser, DelayedUser

from icu import get_parser

parser = get_parser()
args = parser.parse_args()

agents = [FuelMonitor, TrackMonitor, SystemMonitor]
#agents = [User]
#agents = [User, Evaluator]
#agents = [FuelMonitor, SystemMonitor, TrackMonitor, DelayedUser, Evaluator]
#agents = [FuelMonitor, SystemMonitor, TrackMonitor, PerfectUser, Evaluator]

#agents = [User]
#agents = [Evaluator]

env = ICUEnvironment(*agents, **args.__dict__, config_hook="icua.config")
env.simulate()

