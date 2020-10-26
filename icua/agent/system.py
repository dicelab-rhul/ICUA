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
                             gaze='gaze', saccade='saccade', change='change')

    def __init__(self, config, window_properties):
        super(ICUSystemMind, self).__init__()

        # agents beliefs
        (x,y), (w,h) = window_properties['system']['position'], window_properties['system']['size']
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

        self.time = time.time()
        self.num_percepts = 0



    def revise(self, *perceptions):
        self.num_percepts += len(perceptions)
        _time = time.time()
        if _time - self.time >= 1: #after 1 second
            print("{0:4f}-{1:4f}: {2}".format(self.time, _time, self.num_percepts))
            self.time = _time
            self.num_percepts = 0

        for percept in sorted(perceptions, key=lambda p: p.name):
            assert percept.data.label in ICUSystemMind.LABELS.__dict__ #received an unknown event
            
            if percept.data.label == ICUSystemMind.LABELS.gaze: #gaze position
                self.eye_position = (percept.data.x, percept.data.y)
                #print("GAZE", self.eye_position)
                if self.is_looking():
                    self.last_viewed = percept.timestamp

            elif percept.data.label == ICUSystemMind.LABELS.highlight:
                src = percept.src.split(':', 1)[1]
                self.highlighted[src] = percept.data.value
            elif percept.data.label == ICUSystemMind.LABELS.change:
                if "WarningLight" in percept.src:
                    self.revise_warning_light(percept)
                elif "Scale" in percept.src:
                    self.revise_scale(percept)


    # these rules mirror the icu system logic for updating the component states
    def revise_warning_light(self, percept):
        self.warning_light_state[percept.src]['state'] = percept.data.value

    def revise_scale(self, percept):
        self.scale_state[percept.src]['position'] = percept.data.value

    def others_highlighted(self): # are there currently any highlights?
        return any(self.highlighted.values())

    def decide(self):
        # DEMO -- this requires some discussion!

        actions = []

        if not self.is_looking(): #the user is not looking at the task
            if time.time() - self.last_viewed > self.grace_period: # wait until the grace period is up before displaying any warnings
                if not any(self.highlighted.values()): # if nothing else is already highlighted
                    for scale, state in self.scale_state.items():
                        actions.append(self.highlight_scale(scale, state))

                    actions.append(self.highlight_warning_light('WarningLight:0', 1))
                    actions.append(self.highlight_warning_light('WarningLight:1', 0))
                
        else: #if the user is looking, remove all of the warnings that have been displayed
            return self.clear_highlights()
        
        # remove any highlights if needed
        for scale, state in self.scale_state.items():
            actions.append(self.unhighlight_scale(scale, state))
        actions.append(self.unhighlight_warning_light('WarningLight:0', 1))
        actions.append(self.unhighlight_warning_light('WarningLight:1', 0))

        return actions
    
    def highlight_scale(self, scale, state):
        in_range = abs(state['position'] - (state['size'] // 2)) < self.scale_threshold
        print(in_range)
        if not self.is_highlighted(scale) and not in_range: # if the scales are more than the threshold number of slots away then highlight
            return self.highlight_action(scale, value=True)

    def unhighlight_scale(self, scale, state):
        in_range = abs(state['position'] - (state['size'] // 2)) < self.scale_threshold
        if self.is_highlighted(scale) and in_range: #unhighlight if highlighted and in the acceptable range
            return self.highlight_action(scale, value=False)

    def highlight_warning_light(self, warning_light, desired_state):
        if not self.is_highlighted(warning_light): 
            if self.warning_light_state[warning_light]['state'] != desired_state: # the light is is a bad state, highlight it!
                return self.highlight_action(warning_light, value=True)

    def unhighlight_warning_light(self, warning_light, desired_state):
        if self.is_highlighted(warning_light): 
            if self.warning_light_state[warning_light]['state'] == desired_state: # the light is highlighted but in a good state, unhighlight it!
                return self.highlight_action(warning_light, value=False)

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
