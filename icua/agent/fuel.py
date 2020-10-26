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
import pprint

from pystarworlds.Agent import new_sensor

from .agent import ICUMind, ICUBody
from ..perception import FuelTankPerception, PumpPerception, EyeTrackerPerception, HighlightPerception
from ..action import ICUAction

ICUFuelSensor = new_sensor('ICUFuelSensor', FuelTankPerception, PumpPerception, EyeTrackerPerception, HighlightPerception)

class ICUFuelMind(ICUMind):

    LABELS = SimpleNamespace(highlight='highlight', gaze='gaze', saccade='saccade', click='click',
                                burn='burn', transfer='transfer', change="change", fuel='fuel', repair='repair', fail='fail')

    def __init__(self, config, window_properties):
        super(ICUFuelMind, self).__init__()

        self.config = config
        # agents beliefs
        (x,y), (w,h) = window_properties['fuel']['position'], window_properties['fuel']['size']
        self.bounding_box = (x,y,x+w,y+h) # location of the system monitoring task (in window coordinates)

        self.eye_position = (0,0) #gaze position of the users eyes

        self.components = set(list(window_properties['fuel'].keys()))
        self.components.remove('size')
        self.components.remove('position')

        self.pump_status = {pump:1 for pump in self.components if "Pump" in pump} # "ready" by default
        self.tank_status = {tank:self.config[tank]["fuel"] for tank in self.components if "Tank" in tank}
        
        self.highlighted = defaultdict(lambda: False) # is the component highlighted?
        self.viewed = defaultdict(lambda : 0)  # when was the component last viewed?
        self.last_viewed = 0 # when was this task last viewed? (never)

        # control variables
        self.grace_period = 3 # how long should I wait before giving the user some feedback if something is wrong

    def __str__(self):
        return pprint.pformat([self.__class__.__name__ + ":" + self.ID, self.eye_position, self.bounding_box, 
                               self.tank_status, self.tank_status, self.highlighted, self.viewed, self.last_viewed, self.grace_period], indent=2)

    def __repr__(self):
        return self.__class__.__name__ + ":" + self.ID

    def revise(self, *perceptions):
        #pprint.pprint(["{0}:{1}:{2}".format(p.ID, p.name, p.timestamp) for p in sorted(perceptions, key=lambda p: p.timestamp)])

        for percept in sorted(perceptions, key=lambda p: p.name):
            #print(perception)
            if not percept.data.label in ICUFuelMind.LABELS.__dict__: #received an unknown event
                raise ValueError("Unknown event label: {0}".format(percept.data.label))

            if percept.data.label == ICUFuelMind.LABELS.gaze: #gaze position
                #print("FUEL EYE: ", self.eye_position)
                self.eye_position = (percept.data.x, percept.data.y)
                if self.is_looking():
                    self.last_viewed = percept.timestamp
            
            elif percept.data.label == ICUFuelMind.LABELS.change:
                # PUMP ATTENTION
                if "Pump" in percept.src: #update the pumps for use in action decision making...
                    #print(percept)
                    self.pump_status[percept.src] = percept.data.value # off, on, fail

            # TANK ATTENTION
            elif percept.data.label == ICUFuelMind.LABELS.fuel:
                self.tank_status[percept.src] = percept.data.acceptable
                
            elif percept.data.label == ICUFuelMind.LABELS.highlight: #revise highlights
                src = percept.src.split(':', 1)[1]
                self.highlighted[src] = percept.data.value

    def decide(self):
        actions = []
        
        if not self.is_looking():
            if time.time() - self.last_viewed > self.grace_period and not any(self.highlighted.values()):
                
                # if the main tanks are not at an acceptable level, highlight them!
                if not self.tank_status['FuelTank:A']:
                    actions.append(self.highlight_action('FuelTank:A'))
            
                if not self.tank_status['FuelTank:B']:
                    actions.append(self.highlight_action('FuelTank:B'))

            #remove the highlight if its not needed
            if self.is_highlighted('FuelTank:A') and self.tank_status['FuelTank:A']:
                actions.append(self.highlight_action('FuelTank:A', value=False))
            
            if self.is_highlighted('FuelTank:B') and self.tank_status['FuelTank:B']:
                actions.append(self.highlight_action('FuelTank:B', value=False))

            return actions
        else:   
            return self.clear_highlights() # the user is looking, clear highlights

    def others_highlighted(self): # are there currently any highlights?
        return any(self.highlighted.values())

    def clear_highlights(self):
        """ Generate actions for clearing all highlights from the fuel monitoring task (e.g. if the user is now looking)

        Returns:
            list(ICUAction): list of highlight actions (turn off).
        """
        actions = []
        for component, highlighted in self.highlighted.items():
            if highlighted and (component in self.pump_status or component in self.tank_status): #only unhighlight components that belong to this task
                actions.append(self.highlight_action(component, value=False)) #add an action to turn off the highlight
        print(actions)
        return actions


    def is_highlighted(self, component): # is a component currently highlighted?
        return self.highlighted[component]

    def is_looking(self): #is the user looking at the system monitoring task?
        ex, ey = self.eye_position
        x1,y1,x2,y2= self.bounding_box
        return not (ex < x1 or ey < y1 or ex > x2 or ey > y2)

class ICUFuelBody(ICUBody):

    def __init__(self, *args):
        super(ICUFuelBody, self).__init__(ICUFuelMind(*args), [ICUFuelSensor()])
