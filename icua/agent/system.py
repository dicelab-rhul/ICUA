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
import copy
import time

from pystarworlds.Agent import new_sensor

from .agent import ICUMind, ICUBody
from ..perception import WarningLightPerception, ScalePerception, EyeTrackerPerception
from ..action import ICUAction

ICUSystemSensor = new_sensor('ICUSystemSensor', WarningLightPerception, ScalePerception, EyeTrackerPerception)

class ICUSystemMind(ICUMind):

    LABELS = SimpleNamespace(switch='switch', slide='slide', click='click', highlight='highlight')

    def __init__(self, config, window_properties):
        # agents beliefs
        self.scale_threshold = 2 # when should a warning be generated for a scale?
        self.grace_period = 10 # how long should I wait before giving the user some feedback if something is wrong

        self.eye_position = (0,0)
        self.scale_state = copy.deepcopy({k:v for k,v in config.items() if 'Scale' in k})
        self.warning_light_state = copy.deepcopy({k:v for k,v in config.items() if 'WarningLight' in k})

    def revise(self, *perceptions):
        for perception in perceptions:

            print(perception)
            assert perception.data.label in ICUSystemMind.LABELS.__dict__ #received an unknown event
            
            if perception.data.label == ICUSystemMind.LABELS.switch: # warning light changed its state
                self.revise_warning_light(perception)
            elif perception.data.label == ICUSystemMind.LABELS.slide: # scale changed its state
                self.revise_scale(perception)
            elif perception.data.label == ICUSystemMind.LABELS.click: #something was clicked
                if perception.dst in self.scale_state:
                    self.reset_scale(perception)
                    self.scale_state[perception.dst]['clicked'] = perception.timestamp 

                elif perception.dst in self.warning_light_state:
                    self.revise_warning_light(perception)
                    self.warning_light_state[perception.dst]['clicked'] = perception.timestamp 

    # these rules mirror the icu system logic for updating the widgets state
    def revise_warning_light(self, perception):
        self.warning_light_state[perception.dst]['state'] = int(not self.warning_light_state[perception.dst]['state'])

    def revise_scale(self, perception):
        self.scale_state[perception.dst]['position'] += perception.data.slide
        self.scale_state[perception.dst]['position'] = max(0, min(self.scale_state[perception.dst]['size']-1, self.scale_state[perception.dst]['position']))

    def reset_scale(self, perception):
        self.scale_state[perception.dst]['position'] = int(self.scale_state[perception.dst]['size'] / 2)

    def decide(self):
        actions = []
        for scale, state in self.scale_state.items():
            # if the scales are more than the threshold number of slots away then highlight
            if abs(state['position'] - (state['size'] // 2)) >= self.scale_threshold: 
                print("bad scale: ", scale)
                #if the grace period is up (i.e. the scales have been bad for a while) then highlight
                if time.time() - state.get('clicked', 0) > self.grace_period:
                    actions.append(self.highlight_action(scale, value=True)) 
            else:
                actions.append(self.highlight_action(scale, value=False))

        print(self.scale_state)
        return actions

    def highlight_action(self, dst, value=True):
        return ICUAction('Highlight:{0}'.format(dst), label=ICUSystemMind.LABELS.highlight, value=value)


class ICUSystemBody(ICUBody):

    def __init__(self, *args):
        super(ICUSystemBody, self).__init__(ICUSystemMind(*args), [ICUSystemSensor()])
