#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    Created on 24-07-2020 17:45:14

    [Description]
"""
__author__ = "Benedict Wilkins"
__email__ = "benrjw@gmail.com"
__status__ = "Development"


from .environment import ICUEnvironment
from .agent import FuelMonitor, TrackMonitor, SystemMonitor


#agents = [FuelMonitor, TrackMonitor, SystemMonitor]
#agents = [SystemMonitor]
#agents = [TrackMonitor, SystemMonitor]
#agents = [TrackMonitor]
agents = [FuelMonitor]

env = ICUEnvironment(*agents)
env.simulate()

