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
    """ Perception class for ICU agents, wraps an ICU event. """

    def __init__(self, event):
        self.timestamp, self.name, self.src, self.dst, self.data =  event.timestamp, event.name, event.src, event.dst, event.data

    def __str__(self):
        return "{0}:{1} - ({2}->{3}): {4}".format(self.name, self.timestamp, self.src, self.dst, self.data.__dict__)
    
    def __repr__(self):
        return str(self)

class EyeTrackerPerception(ICUPerception):
    """ Perception corresponding to an ICU eyetracker event. """
    pass

class WarningLightPerception(ICUPerception):
    """ Perception corresponding to an ICU warning light event. """
    pass

class FuelTankPerception(ICUPerception):
    """ Perception corresponding to an ICU fuel tank event. """
    pass

class PumpPerception(ICUPerception):
    """ Perception corresponding to an ICU pump event. """
    pass

class ScalePerception(ICUPerception):
    """ Perception corresponding to an ICU scale event. """
    pass

class TrackPerception(ICUPerception):
    """ Perception corresponding to an ICU track event. """
    pass

class HighlightPerception(ICUPerception):
    """ Perception corresponding to an ICU highlight event. """
    pass


# used to convert ICU event to the appropriate perception type for use in publish/subscribe
ICU_PERCEPTION_GROUPS = {'WarningLight':WarningLightPerception, 
                         'FuelTank':FuelTankPerception,
                         'Pump':PumpPerception,
                         'Scale':ScalePerception,
                         'Overlay':EyeTrackerPerception,
                         'Target':TrackPerception,
                         'Highlight':HighlightPerception}
                         
def perception(event):
    """
    Generate a new perception given an ICU event.

    Args:
        event (ICU.event.Event): an event received from the ICU environment

    Returns:
        ICUPerception : a perception
    """

    """
    #TODO remove (testing)
    if filter_print(event, ["EyeTrackerStub", "Target:0", "Highlight",
                            "TargetEventGenerator", "ScaleEventGenerator",
                            "PumpEventGenerator", "WarningLightEventGenerator"], 
                            [],
                            ["burn", "transfer"]):
        print(event)
    """

    group = event.src.split(":")[0]
    if group in ICU_PERCEPTION_GROUPS:
        return ICU_PERCEPTION_GROUPS[group](event)

    group = event.dst.split(":")[0]
    if group in ICU_PERCEPTION_GROUPS:
        return ICU_PERCEPTION_GROUPS[group](event)

    raise ValueError("Failed to find perception group for event:\n    {0}\n    avaliable groups are: {1}".format(event, list(ICU_PERCEPTION_GROUPS.keys())))


def filter_print(event, src, dst, label):
    result = True
    for s in src: 
        result = result and s not in event.src
    for d in dst:
        result = result and d not in event.dst
    for l in label:
        result = result and l not in event.data.label

    return result
