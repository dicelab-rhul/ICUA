#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    Created on 24-07-2020 17:44:47

    [Description]
"""
__author__ = "Benedict Wilkins"
__email__ = "benrjw@gmail.com"
__status__ = "Development"

from types import SimpleNamespace
from collections import defaultdict
import copy
import time

from pystarworlds.Agent import new_sensor

from .agent import ICUMind, ICUBody
from ..perception import FuelTankPerception, PumpPerception, EyeTrackerPerception, HighlightPerception
from ..action import ICUAction

ICUFuelSensor = new_sensor('ICUFuelSensor', FuelTankPerception, PumpPerception, EyeTrackerPerception, HighlightPerception)

class ICUFuelMind(ICUMind):

    LABELS = SimpleNamespace(highlight='highlight', gaze='gaze', saccade='saccade', click='click',
                                burn='burn', transfer='transfer', fuel='fuel', repair='repair', fail='fail')

    def __init__(self, config, window_properties):
        super(ICUFuelMind, self).__init__()

        # agents beliefs
        (x,y), (w,h) = window_properties['fuel']['position'], window_properties['fuel']['size']
        self.bounding_box = (x,y,x+w,y+h) # location of the system monitoring task (in window coordinates)

        self.eye_position = (0,0) #gaze position of the users eyes
        # mirrored state of each component of the system monitoring task (updated in revise)
   
        self.pump_state = copy.deepcopy({k:v for k,v in config.items() if 'Pump' in k})
        self.tank_state = copy.deepcopy({k:v for k,v in config.items() if 'Tank' in k})

        print(self.pump_state)
        print(self.tank_state)
        
        self.highlighted = defaultdict(lambda: False) # is the component highlighted?
        self.viewed = defaultdict(lambda : 0)  # when was the component last viewed?
        self.last_viewed = 0 # when was this task last viewed? (never)

        # control variables
        self.grace_period = 3 # how long should I wait before giving the user some feedback if something is wrong


    def revise(self, *perceptions):
        for perception in perceptions:
            #print(perception)
            assert perception.data.label in ICUFuelMind.LABELS.__dict__ #received an unknown event
            
            if perception.data.label == ICUFuelMind.LABELS.gaze: #gaze position
                self.eye_position = (perception.data.x, perception.data.y)
                if self.is_looking():
                    self.last_viewed = perception.timestamp

            elif perception.data.label == ICUFuelMind.LABELS.burn:
                self.tank_state[perception.src]['fuel'] += perception.data.value
            
            elif perception.data.label == ICUFuelMind.LABELS.transfer:
                t1, t2 = perception.src.split(":")[1]
                self.tank_state["FuelTank:{0}".format(t1)]['fuel'] -= perception.data.value
                self.tank_state["FuelTank:{0}".format(t2)]['fuel'] += perception.data.value
            
            #TODO this might be made easier by emitting an event in ICU directly from the pump whenever its state changes... rather than mirroring the logic here...
            elif perception.data.label == ICUFuelMind.LABELS.fail:
                self.pump_state[perception.dst]['state'] = 2

            elif perception.data.label == ICUFuelMind.LABELS.repair:
                self.pump_state[perception.dst]['state'] = 1
                
            elif perception.data.label == ICUFuelMind.LABELS.click:
                state = self.pump_state[perception.dst]['state'] 
                print(perception.data.value)
                if state != 2: #pump has not failed
                    self.pump_state[perception.dst]['state']  = abs(state - 1)                
                
            elif perception.data.label == ICUFuelMind.LABELS.highlight: #revise highlights
                src = perception.src.split(':', 1)[1]
                self.highlighted[src] = perception.data.value

    def decide(self):
        print(self.pump_state)
        pass

    def is_highlighted(self, component): # is a component currently highlighted?
        return self.highlighted[component]

    def is_looking(self): #is the user looking at the system monitoring task?
        ex, ey = self.eye_position
        x1,y1,x2,y2= self.bounding_box
        return not (ex < x1 or ey < y1 or ex > x2 or ey > y2)

class ICUFuelBody(ICUBody):

    def __init__(self, *args):
        super(ICUFuelBody, self).__init__(ICUFuelMind(*args), [ICUFuelSensor()])
