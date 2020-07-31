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

from pystarworlds.Agent import new_sensor

from .agent import ICUMind, ICUBody
from ..perception import WarningLightPerception, ScalePerception, EyeTrackerPerception, HighlightPerception
from ..action import ICUAction

ICUSystemSensor = new_sensor('ICUSystemSensor', WarningLightPerception, ScalePerception, EyeTrackerPerception, HighlightPerception)

class ICUSystemMind(ICUMind):

    LABELS = SimpleNamespace(switch='switch', slide='slide', click='click', highlight='highlight',
                             gaze='gaze', saccade='saccade')

    def __init__(self, config, window_properties):
        super(ICUSystemMind, self).__init__()

        # agents beliefs
        (x,y), (w,h) = window_properties['system'][0]['position'], window_properties['system'][0]['size']
        self.bounding_box = (x,y,x+w,y+h) # location of the system monitoring task (in window coordinates)
        
        self.eye_position = (0,0) #gaze position of the users eyes
        
        # mirrored state of each component of the system monitoring task (updated in revise)
        self.scale_state = copy.deepcopy({k:v for k,v in config.items() if 'Scale' in k})
        self.warning_light_state = copy.deepcopy({k:v for k,v in config.items() if 'WarningLight' in k})



        self.highlighted = defaultdict(lambda: False) # is the component highlighted?
        self.clicked = defaultdict(lambda : 0) # TODO when was the component last clicked?
        self.viewed = defaultdict(lambda : 0)  # when was the component last viewed?
        self.last_viewed = 0 # when was this task last viewed? (never)


        # control variables
        self.scale_threshold = 2 # when should a warning be generated for a scale?
        self.grace_period = 3 # how long should I wait before giving the user some feedback if something is wrong

    def revise(self, *perceptions):
        for perception in sorted(perceptions, key=lambda p: p.name):

            #print(perception)
            assert perception.data.label in ICUSystemMind.LABELS.__dict__ #received an unknown event
            
            if perception.data.label == ICUSystemMind.LABELS.gaze: #gaze position
                self.eye_position = (perception.data.x, perception.data.y)
                if self.is_looking():
                    self.last_viewed = perception.timestamp

            elif perception.data.label == ICUSystemMind.LABELS.highlight:
                #print(perception)
                src = perception.src.split(':', 1)[1]
                self.highlighted[src] = perception.data.value

            elif perception.data.label == ICUSystemMind.LABELS.switch: # warning light changed its state
                self.revise_warning_light(perception)

            elif perception.data.label == ICUSystemMind.LABELS.slide: # scale changed its state
                self.revise_scale(perception)

            elif perception.data.label == ICUSystemMind.LABELS.click: #something was clicked
                self.clicked[perception.dst] = perception.timestamp 
                if perception.dst in self.scale_state:
                    self.reset_scale(perception)
                elif perception.dst in self.warning_light_state:
                    self.revise_warning_light(perception)
                    

    # these rules mirror the icu system logic for updating the component states
    def revise_warning_light(self, perception):
        self.warning_light_state[perception.dst]['state'] = int(not self.warning_light_state[perception.dst]['state'])

    def revise_scale(self, perception):
        self.scale_state[perception.dst]['position'] += perception.data.slide
        self.scale_state[perception.dst]['position'] = max(0, min(self.scale_state[perception.dst]['size']-1, self.scale_state[perception.dst]['position']))

    def reset_scale(self, perception):
        self.scale_state[perception.dst]['position'] = int(self.scale_state[perception.dst]['size'] / 2)



    def decide(self):
        # DEMO -- this requires some discussion!

        #print(self.scale_state)
        #print(self.eye_position)
        #print(self.is_looking())

        if not self.is_looking(): #the user is not looking at the task
            if time.time() - self.last_viewed > self.grace_period: # wait until the grace period is up before displaying any warnings
                actions = []
                for scale, state in self.scale_state.items():
                    in_range = abs(state['position'] - (state['size'] // 2)) < self.scale_threshold

                    if not self.is_highlighted(scale) and not in_range: # if the scales are more than the threshold number of slots away then highlight
                        actions.append(self.highlight_action(scale, value=True)) 

                    elif self.is_highlighted(scale) and in_range:  #unhighlight if highlighted and in the acceptable range
                            actions.append(self.highlight_action(scale, value=False))

                action = self.decide_warning_light('WarningLight:0', 1)
                actions.append(action)
                action = self.decide_warning_light('WarningLight:1', 0)
                actions.append(action)

                return actions

        else: #if the user is looking, remove all of the warnings that have been displayed
            return self.clear_highlights()
    
    def decide_warning_light(self, warning_light, desired_state):
        if not self.is_highlighted(warning_light): 
            if self.warning_light_state[warning_light]['state'] != desired_state: # the light is is a bad state, highlight it!
                return self.highlight_action(warning_light, value=True)
        else:
            if self.warning_light_state[warning_light]['state'] == desired_state: # the light is highlighted but in a good state, unhighlight it!
                return self.highlight_action(warning_light, value=False)

        return None #do nothing


    def is_highlighted(self, component): # is a component currently highlighted?
        return self.highlighted[component]

    def is_looking(self): #is the user looking at the system monitoring task?
        ex, ey = self.eye_position
        x1,y1,x2,y2= self.bounding_box
        return not (ex < x1 or ey < y1 or ex > x2 or ey > y2)

    def is_looking_at(self, widget): #is the user looking at a specific part of the system monitoring task?
        raise NotImplementedError("This may not be used...? it wont be very accurate")

    # ==== ACTIONS ==== #

    def clear_highlights(self):
        """ Generate actions for clearing all highlights from the system monitoring task (e.g. if the user is now looking)

        Returns:
            list(ICUAction): list of highlight actions (turn off).
        """
        actions = []
        for component, highlighted in self.highlighted.items():
            if highlighted and (component in self.scale_state or component in self.warning_light_state): #only unhighlight components that belong to this task
                actions.append(self.highlight_action(component, value=False)) #add an action to turn off the highlighted
        return actions


class ICUSystemBody(ICUBody):

    def __init__(self, *args):
        super(ICUSystemBody, self).__init__(ICUSystemMind(*args), [ICUSystemSensor()])
