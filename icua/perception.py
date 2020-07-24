#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    Created on 24-07-2020 17:45:34

    [Description]
"""
__author__ = "Benedict Wilkins"
__email__ = "benrjw@gmail.com"
__status__ = "Development"

from icu.event import Event
from pystarworlds.Event import Perception

class ICUPerception(Perception):

    def __init__(self, event):
        self.timestamp, self.name, self.src, self.dst, self.data =  event.timestamp, event.name, event.src, event.dst, event.data

    def __str__(self):
        return "{0}:{1} - ({2}->{3}): {4}".format(self.name, self.timestamp, self.src, self.dst, self.data.__dict__)
    
    def __repr__(self):
        return str(self)

class EyeTrackerPerception(ICUPerception):
    pass

class WarningLightPerception(ICUPerception):
    pass

class FuelTankPerception(ICUPerception):
    pass

class PumpPerception(ICUPerception):
    pass

class ScalePerception(ICUPerception):
    pass

class TrackPerception(ICUPerception):
    pass

ICU_PERCEPTION_GROUPS = {'WarningLight':WarningLightPerception, 
                         'FuelTank':FuelTankPerception,
                         'Pump':PumpPerception,
                         'Scale':ScalePerception,
                         'EyeTracker':EyeTrackerPerception,
                         'Target':TrackPerception}
                         
def perception(event):
    """
    Generate a new perception given an ICU event.

    Args:
        event (ICU.event.Event): an event received from the ICU environment

    Returns:
        ICUPerception : a perception
    """
    group = event.src.split(":")[0]
    if group in ICU_PERCEPTION_GROUPS:
        return ICU_PERCEPTION_GROUPS[group](event)

    group = event.dst.split(":")[0]
    if group in ICU_PERCEPTION_GROUPS:
        return ICU_PERCEPTION_GROUPS[group](event)

    raise ValueError("Failed to find perception group for event: {0}, avaliable groups are: {1}".format(event, list(ICU_PERCEPTION_GROUPS.keys())))

    #ICU_PERCEPTION_GROUPS