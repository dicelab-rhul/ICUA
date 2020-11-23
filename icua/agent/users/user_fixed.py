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
import numpy as np
from pprint import pprint

from pystarworlds.Agent import new_sensor

from ..agent import ICUMind, ICUBody
from ...perception import WarningLightPerception, ScalePerception, TrackPerception, FuelTankPerception, PumpPerception, EyeTrackerPerception, HighlightPerception
from ...action import ICUAction, InputAction

ICUUserSensor = new_sensor('ICUUserSensor', WarningLightPerception, ScalePerception, TrackPerception, FuelTankPerception, PumpPerception, EyeTrackerPerception, HighlightPerception)

LABELS = SimpleNamespace(switch='switch', slide='slide', click='click', highlight='highlight', key='key',
                             gaze='gaze', saccade='saccade', move='move', change='change', fuel='fuel')

KEY_CODES = {"Up":98, "Down":104, "Left":100, "Right":102}

class ICUUser(ICUMind):

    def __init__(self, config, window_properties, fix, delay=1.):
        super(ICUUser, self).__init__()
        self.config = config
        self.window_properties = window_properties

        self.fix = fix
        self.delay = delay
     
        self.components = set(list(window_properties['fuel'].keys()) + list(window_properties['system'].keys()) + list(window_properties['track'].keys()))  
        self.components.remove('size')
        self.components.remove('position')
        self.components.add('Target:0')

        self.task_positions = {k:(v['position'][0] + v['size'][0]/2, v['position'][1] + v['size'][1]/2, *v['size']) for k,v in self.window_properties.items()}
        self.task_positions.update({k:(v['position'][0] + v['size'][0]/2, v['position'][1] + v['size'][1]/2, *v['size']) for k,v in self.window_properties['system'].items() if k in self.components})
        self.task_positions.update({k:(v['position'][0] + v['size'][0]/2, v['position'][1] + v['size'][1]/2, *v['size']) for k,v in self.window_properties['fuel'].items() if k in self.components})
        self.task_positions['Target:0'] = self.task_positions['track']

        # EYE
        self.eye_position = list(self.task_positions['window'][:2])
        self.eye_to =  list(self.task_positions['window'][:2])
        self.eye_speed = 0.1 # CHANGE ME

        self.time_to_solve = 0.2 # CHANGE ME

        self.highlighted = defaultdict(lambda: (False, 0.)) # is the component highlighted?

        # TRACKING
        self.tracking_size = np.array(self.window_properties['track']['size'])
        self.tracking_acceptable = self.tracking_size * np.array([1/4, 1/4]) # TODO update if ICU configurable
        self.target_position = np.array([0,0])

        # FUEL
        self.pump_status = {pump:1 for pump in self.components if "Pump" in pump} # "ready" by default
        self.tank_status = {tank:self.config[tank]["fuel"] for tank in self.components if "Tank" in tank}

        # SYSTEM
        self.scale_status = {k:copy.deepcopy(v) for k,v in self.config.items() if "Scale" in k}
        self.warning_light_status = {k:copy.deepcopy(v) for k,v in self.config.items() if "WarningLight" in k}
        self.attention_needed = []

        self.actions = []
        self.last_action_time = 0

    def tank_acceptable(self, tank):
        pos = self.config[tank]["accept_position"] * self.config[tank]["capacity"]
        return pos - self.tank_status[tank]

    def revise(self, *perceptions):
        self.attention_needed = []
        target_moves = []

        for percept in sorted(perceptions, key=lambda p: p.name):

            if percept.data.label == LABELS.highlight:
                src = percept.src.split(':', 1)[1]
                if self.highlighted[src][0] != percept.data.value: #its a new highlight event
                    self.highlighted[src] = (percept.data.value, percept.timestamp)
                    if not self.highlighted[src][0]:
                        del self.highlighted[src]


            # TRACKING ATTENTION
            elif percept.data.label == LABELS.key:
                pass 
            elif percept.data.label == LABELS.move and 'x' in percept.data.__dict__:
                self.target_position = np.array([percept.data.x, percept.data.y])

            elif percept.data.label == LABELS.change:
                if "WarningLight" in percept.src:
                    self.warning_light_status[percept.src]['state'] = percept.data.value
                elif "Scale" in percept.src:
                    self.scale_status[percept.src]["position"] = percept.data.value

                # PUMP ATTENTION
                elif "Pump" in percept.src: #update the pumps for use in action decision making...
                    #print(percept)
                    self.pump_status[percept.src] = percept.data.value # off, on, fail

                # TANK ATTENTION
                elif "Tank" in percept.src:
                    self.tank_status[percept.src] = percept.data.value

        print(self.task_positions)
        self.eye_to = self.task_positions[self.fix][:2]
        

    def decide(self):

        # if there are no other actions to do, move eyes to the next task
        cx,cy = self.eye_position
        tx,ty = self.eye_to
        dx,dy = (tx-cx) * self.eye_speed, (ty-cy) * self.eye_speed

        _t = time.time()
        self.actions.clear()
      
        if self.is_looking_at("fuel"):
            self.handle_fuel(self.actions)
        elif self.is_looking_at("system"):
            self.handle_system(self.actions)
        elif self.is_looking_at("track"): # should not be affected by the action delay (pressing and clicking are different)
            self.handle_tracking(self.actions)
            if len(self.actions) > 0:
                return [*self.actions]
    
        if len(self.actions) > 0 and _t - self.last_action_time > self.delay:
            self.last_action_time = _t
            return self.actions.pop(), self.move_eye(dx,dy)
        
        return self.move_eye(dx, dy)


    def is_looking_at(self, task):
        x, y, w, h = self.task_positions[task]
        x1,x2,y1,y2 = x-w/2,x+w/2,y-h/2,y+h/2
        return self.eye_position[0] >= x1 and self.eye_position[0] <= x2 and self.eye_position[1] >= y1 and self.eye_position[1] <= y2

    def handle_system(self, actions):
        # handle scales
        for scale,data in self.scale_status.items():
             if data['position'] != self.config[scale]['size'] // 2: # scale has moved from the middle
                actions.append(self.click(scale))

        # handle warning lights
        for light,data in self.warning_light_status.items():
            if int(light.split(":")[1]) == data['state']: # the light is in a bad state
                actions.append(self.click(light))

    def handle_tracking(self, actions):
        print(self.target_position)
        if np.linalg.norm(self.target_position) > self.tracking_acceptable[0] / 4:
            invert = (int(self.config["Target:0"]['invert']) * 2) - 1
            direction = ((np.sign(np.array([0,0]) + invert * self.target_position) + 1) / 2).astype(np.uint8)
            vkey, hkey = ["Up", "Down"], ["Left", "Right"] # TODO update for inverted config option!
            actions.append(self.key_press("Target:0", hkey[direction[0]]))
            actions.append(self.key_press("Target:0", vkey[direction[1]]))

    def handle_fuel(self, actions):
        # 1. always keep secondary tanks full
        aux_pumps = ["Pump:FD", "Pump:EC"]
        for a_pump in aux_pumps: 
            if self.pump_status[a_pump] == 1:
                actions.append(self.click(a_pump))
        # 2. fill main tanks (A,B) if not acceptable
        main_pumps = {"FuelTank:A":["Pump:CA", "Pump:EA"], "FuelTank:B":["Pump:FB", "Pump:DB"]}
        for tank, pumps in main_pumps.items():
            if self.tank_acceptable(tank) > 0: # not enough fuel turn on the pumps to the main tank if possible
                actions.extend([self.click(pump) for pump in pumps if self.pump_status[pump] == 1])
            if self.tank_acceptable(tank) < 0: # too much fuel turn off the pumps to the main tank if possible
                actions.extend([self.click(pump) for pump in pumps if self.pump_status[pump] == 0])

    def move_eye(self, dx, dy):
        #print("MOVE EYE", dx, dy)
        self.eye_position[0] += dx
        self.eye_position[1] += dy
        return InputAction('Overlay:0', label=LABELS.gaze, x=self.eye_position[0], y=self.eye_position[1])

    def click(self, component):
        #print("CLICK:", component)
        return ICUAction(component, label=LABELS.click, x=None, y=None)  # TODO position
    
    def key_press(self, component, key):
        return ICUAction(component, label=LABELS.key, keycode=KEY_CODES[key], key=key, action='press')

    def key_release(self, component, key):
        return ICUAction(component, label=LABELS.key, keycode=KEY_CODES[key], key=key, action='release')



class ICUUserBody(ICUBody):

    def __init__(self, *args, **kwargs):
        super(ICUUserBody, self).__init__(ICUUser(*args, **kwargs), [ICUUserSensor()])



