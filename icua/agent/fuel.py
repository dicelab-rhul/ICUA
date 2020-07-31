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

        self.tank_state['FuelTank:A']['acceptable'] = True
        self.tank_state['FuelTank:B']['acceptable'] = True

        print(self.pump_state)
        print(self.tank_state)
        
        self.highlighted = defaultdict(lambda: False) # is the component highlighted?
        self.viewed = defaultdict(lambda : 0)  # when was the component last viewed?
        self.last_viewed = 0 # when was this task last viewed? (never)

        # control variables
        self.grace_period = 3 # how long should I wait before giving the user some feedback if something is wrong

    def __str__(self):
        return pprint.pformat([self.__class__.__name__ + ":" + self.ID, self.eye_position, self.bounding_box, 
                               self.pump_state, self.tank_state, self.highlighted, self.viewed, self.last_viewed, self.grace_period], indent=2)

    def __repr__(self):
        return self.__class__.__name__ + ":" + self.ID

    def revise(self, *perceptions):
        #pprint.pprint(["{0}:{1}:{2}".format(p.ID, p.name, p.timestamp) for p in sorted(perceptions, key=lambda p: p.timestamp)])

        for perception in sorted(perceptions, key=lambda p: p.name):
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
                #print(perception)
                self.tank_state["FuelTank:{0}".format(t1)]['fuel'] -= perception.data.value
                self.tank_state["FuelTank:{0}".format(t2)]['fuel'] += perception.data.value
                #print(self.tank_state["FuelTank:{0}".format(t1)]['fuel'])
            
            elif perception.data.label == ICUFuelMind.LABELS.fuel:
                self.tank_state[perception.src]['acceptable'] = perception.data.acceptable

            #TODO this might be made easier by emitting an event in ICU directly from the pump whenever its state changes... rather than mirroring the logic here...
            elif perception.data.label == ICUFuelMind.LABELS.fail:
                self.pump_state[perception.dst]['state'] = 2

            elif perception.data.label == ICUFuelMind.LABELS.repair:
                self.pump_state[perception.dst]['state'] = 1
                
            elif perception.data.label == ICUFuelMind.LABELS.click:
                state = self.pump_state[perception.dst]['state'] 
                if state != 2: #pump has not failed
                    self.pump_state[perception.dst]['state']  = abs(state - 1)                
                
            elif perception.data.label == ICUFuelMind.LABELS.highlight: #revise highlights
                src = perception.src.split(':', 1)[1]
                self.highlighted[src] = perception.data.value

    def decide(self):
        actions = []
        if not self.is_looking():
            
            if time.time() - self.last_viewed > self.grace_period:

                # if the main tanks are not at an acceptable level, highlight them!
                if not self.tank_state['FuelTank:A']['acceptable']:
                    actions.append(self.highlight_action('FuelTank:A'))
                if not self.tank_state['FuelTank:B']['acceptable']:
                    actions.append(self.highlight_action('FuelTank:B'))

                # TODO other highlighting? 
                
            return actions
        else:   
            return self.clear_highlights() # the user is looking, clear highlights

    def clear_highlights(self):
        """ Generate actions for clearing all highlights from the fuel monitoring task (e.g. if the user is now looking)

        Returns:
            list(ICUAction): list of highlight actions (turn off).
        """
        actions = []
        for component, highlighted in self.highlighted.items():
            if highlighted and (component in self.pump_state or component in self.tank_state): #only unhighlight components that belong to this task
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
