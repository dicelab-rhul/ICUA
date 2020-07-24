#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    Created on 24-07-2020 17:45:03

    [Description]
"""
__author__ = "Benedict Wilkins"
__email__ = "benrjw@gmail.com"
__status__ = "Development"

from types import SimpleNamespace

from pystarworlds.Agent import new_sensor

from .agent import ICUMind, ICUBody
from ..perception import TrackPerception, EyeTrackerPerception
from ..action import ICUAction

ICUTrackSensor = new_sensor('ICUTrackSensor', TrackPerception, EyeTrackerPerception)

class ICUTrackMind(ICUMind):

    LABELS = SimpleNamespace(move='move')

    def __init__(self):
        self.target_position = (0,0)
        self.eye_position = (0,0)

    def revise(self, *perceptions):
        
        for perception in perceptions:

            assert perception.data.label in ICUTrackMind.LABELS.__dict__ #received an unknown event
            
            if perception.data.label == ICUTrackMind.LABELS.move: #the tracking target moved
                self.target_position = (self.target_position[0] + perception.data.dx, self.target_position[1] + perception.data.dy)

    def decide(self):
        print(self.target_position)
        return ICUAction()

class ICUTrackBody(ICUBody):

    def __init__(self):
        super(ICUTrackBody, self).__init__(ICUTrackMind(), [ICUTrackSensor()])
