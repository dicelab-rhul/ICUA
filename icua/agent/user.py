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
from collections import defaultdict
import copy
import time
import random
from pprint import pprint

from pystarworlds.Agent import new_sensor

from .agent import ICUMind, ICUBody
from ..perception import WarningLightPerception, ScalePerception, TrackPerception, FuelTankPerception, PumpPerception, EyeTrackerPerception, HighlightPerception
from ..action import ICUAction, InputAction

ICUUserSensor = new_sensor('ICUUserSensor', WarningLightPerception, ScalePerception, TrackPerception, FuelTankPerception, PumpPerception, EyeTrackerPerception, HighlightPerception)

LABELS = SimpleNamespace(switch='switch', slide='slide', click='click', highlight='highlight',
                             gaze='gaze', saccade='saccade', key='key', move='move')

KEY_CODES = {"Up":98, "Down":104, "Left":100, "Right":102}

class ICUUser(ICUMind):

   
    def __init__(self, config, window_properties):
        super(ICUUser, self).__init__()
        self.config = config
        self.window_properties = window_properties
   
        self.components = set(list(window_properties['fuel'].keys()) + list(window_properties['system'].keys()) + list(window_properties['track'].keys()))
        self.components.remove('size')
        self.components.remove('position')
        self.components.add('Target:0')

        pprint(window_properties)
        self.task_positions = {k:(v['position'][0] + v['size'][0]/2, v['position'][1] + v['size'][1]/2) for k,v in self.window_properties.items()}
        self.task_positions.update({k:(v['position'][0] + v['size'][0]/2, v['position'][1] + v['size'][1]/2) for k,v in self.window_properties['system'].items() if k in self.components})
        self.task_positions.update({k:(v['position'][0] + v['size'][0]/2, v['position'][1] + v['size'][1]/2) for k,v in self.window_properties['fuel'].items() if k in self.components})
        self.task_positions['Target:0'] = self.task_positions['track']

        pprint(self.task_positions)
        self.eye_position = list(self.task_positions['window'])
        self.eye_to =  list(self.task_positions['window'])

        pprint(self.components)

        self.target_position = (0,0)
        self.target_acceptable = (-50,-50,50,50)

        self.highlighted = defaultdict(lambda: (False, 0.)) # is the component highlighted?

    def revise(self, *perceptions):
        for percept in sorted(perceptions, key=lambda p: p.name):

            if percept.data.label == LABELS.highlight:
                src = percept.src.split(':', 1)[1]
                if self.highlighted[src][0] != percept.data.value: #its a new highlight event
                    self.highlighted[src] = (percept.data.value, percept.timestamp)


            elif percept.data.label == LABELS.move and 'x' in percept.data.__dict__:
                self.target_position = (percept.data.x, percept.data.y)
       

        self.priority = dict(filter(lambda x: x[1][1], self.highlighted.items()))
        self.priority =  [k for k,v in sorted(self.priority.items(), key=lambda x: x[1][1])] #sort by timestep
        if len(self.priority) > 0:
            self.eye_to = self.task_positions[self.priority[0]]
        else:
            self.eye_to = self.task_positions['window'] #default position, no warnings are being displayed


    def decide(self):
        cx,cy = self.eye_position
        tx,ty = self.eye_to
        dx,dy = tx-cx,ty-cy

        actions = []
        actions.append(self.move_eye(dx,dy))
        actions.append(self.key_press("Down"))
        
        return actions

    def move_eye_to_task(self, task):
        print(self.window_properties)


    def move_eye(self, dx, dy):
        self.eye_position[0] += dx
        self.eye_position[1] += dy
        return InputAction('Overlay:0', label=LABELS.gaze, x=self.eye_position[0], y=self.eye_position[1])

    def click(self, component):
        return ICUAction(component, label=LABELS.click, x=None, y=None) 
    
    def key_press(self, key):
        return ICUAction('Target:0', label=LABELS.key, keycode=KEY_CODES[key], key=key, action='press')

    def key_release(self, key):
        return ICUAction('Target:0', label=LABELS.key, keycode=KEY_CODES[key], key=key, action='release')



class ICUUserBody(ICUBody):

    def __init__(self, *args):
        super(ICUUserBody, self).__init__(ICUUser(*args), [ICUUserSensor()])



