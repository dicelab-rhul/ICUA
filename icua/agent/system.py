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

from pystarworlds.agent import new_sensor

from .agent import ICUMind, ICUBody
from ..perception import WarningLightPerception, ScalePerception, EyeTrackerPerception, HighlightPerception
from ..action import ICUAction

ICUSystemSensor = new_sensor('ICUSystemSensor', WarningLightPerception, ScalePerception, EyeTrackerPerception, HighlightPerception)

class ICUSystemMind(ICUMind):

    LABELS = SimpleNamespace(switch='switch', slide='slide', click='click', highlight='highlight',
                             gaze='gaze', saccade='saccade', change='change', rotate='rotate')

    def __init__(self, config, window_properties):
        super(ICUSystemMind, self).__init__()

        # agents beliefs
        (x,y), (w,h) = window_properties['system']['position'], window_properties['system']['size']
        self.bounding_box = (x,y,x+w,y+h) # location of the system monitoring task (in window coordinates)
        
        self.eye_position = (0,0) #gaze position of the users eyes
        
        # mirrored state of each component of the system monitoring task (updated in revise)
        self.scale_state = copy.deepcopy({k:SimpleNamespace(**v, last_failed=0) for k,v in config.items() if 'Scale' in k})
        self.warning_light_state = copy.deepcopy({k:SimpleNamespace(**v, last_failed=0) for k,v in config.items() if 'WarningLight' in k})
       
        self.system_panel = "SystemMonitor" # TODO get this info from somewhere -- the name might change!

        self.highlighted = defaultdict(lambda: False) # is the component highlighted?
        self.last_viewed = 0 # when was this task last viewed? (never)

        self.time = time.time()
        self.num_percepts = 0

        # control variables from config TODO streamline using defaults
        try:
            self.grace_period = config['agent']['system']['grace_period']
        except:
            self.grace_period = 2

        try:
            self.highlight_all = (config['agent']['system']['highlight']) == 'all'
        except:
            self.highlight_all = False

    def revise(self, *perceptions):
        self.num_percepts += len(perceptions)
        _time = time.time()
        if _time - self.time >= 1: #after 1 second
            #print("{0:4f}-{1:4f}: {2}".format(self.time, _time, self.num_percepts))
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
        self.warning_light_state[percept.src].state = percept.data.value
        if percept.data.value == int(percept.src.split(":")[1]): # if the light is in a bad state
            self.warning_light_state[percept.src].last_failed = percept.timestamp

    def revise_scale(self, percept):
        state = self.scale_state[percept.src] 
        was_acceptable = abs(state.position - (state.size // 2)) == 0

        self.scale_state[percept.src].position = percept.data.value
        state = self.scale_state[percept.src] 
        
        if was_acceptable:
            in_range = abs(state.position - (state.size // 2))
            if in_range > 0: # scale is in a bad position, it failed
                self.scale_state[percept.src].last_failed = percept.timestamp

    def others_highlighted(self): # are there currently any highlights?
        return any(self.highlighted.values())

    def highlight_any(self):
        actions = []
        # should anything be highlighted? 
        for scale, state in self.scale_state.items():
            actions.append(self.highlight_scale(scale, state))
        actions.append(self.highlight_warning_light('WarningLight:0', 1))
        actions.append(self.highlight_warning_light('WarningLight:1', 0))
        actions = [a for a in actions if a is not None] # remove all None actions
        
        if not self.highlight_all: # only highlight the panel...
            if len(actions) > 0: # something needs highlighting, highlight the panel
                return  [self.highlight_action(self.system_panel, value=True)]
                #return []

        return actions

    def decide(self):
        # DEMO -- this requires some discussion!

        actions = []

        if not self.is_looking(): #the user is not looking at the task
            if not any(self.highlighted.values()): # if nothing else is already highlighted
                if time.time() - self.last_viewed > self.grace_period: # wait until the grace period is up before displaying any warnings
                    actions.extend(self.highlight_any())
                   
        else: #if the user is looking, remove all of the warnings that have been displayed
            return self.clear_highlights()
        
        # remove any highlights if needed
        for scale, state in self.scale_state.items():
            actions.append(self.unhighlight_scale(scale, state))
        actions.append(self.unhighlight_warning_light('WarningLight:0', 1))
        actions.append(self.unhighlight_warning_light('WarningLight:1', 0))
        actions.append(self.unhighlight_panel())
        #rotate = self.rotate_arrow_action(self.eye_position, self.bounding_box[:2])
        #actions.append(rotate)

        return actions
    
    def unhighlight_panel(self):
        if self.is_highlighted(self.system_panel):
            unhighlight = True
            for scale, state in self.scale_state.items():
                unhighlight = unhighlight and abs(state.position - (state.size // 2)) == 0
            unhighlight = unhighlight and self.warning_light_state['WarningLight:0'].state == 1
            unhighlight = unhighlight and self.warning_light_state['WarningLight:1'].state == 0
            if unhighlight:
                self.highlight_action(self.system_panel, value=False)

    def highlight_scale(self, scale, state):
        in_range = abs(state.position - (state.size // 2)) == 0
        #print(in_range, abs(state.position - (state.size // 2)), self.scale_threshold)
        if not self.is_highlighted(scale) and not in_range and time.time() - state.last_failed > self.grace_period: # if the scales are more than the threshold number of slots away then highlight
            #print("HIGHLIGHT ", scale, self.last_viewed, time.time() - state.last_failed, self.grace_period)
            return self.highlight_action(scale, value=True)

    def unhighlight_scale(self, scale, state):
        in_range = abs(state.position - (state.size // 2)) == 0
        if self.is_highlighted(scale) and in_range: #unhighlight if highlighted and in the acceptable range
            return self.highlight_action(scale, value=False)

    def highlight_warning_light(self, warning_light, desired_state):
        if not self.is_highlighted(warning_light): 
            state = self.warning_light_state[warning_light].state
            last_failed = self.warning_light_state[warning_light].last_failed

            if state != desired_state and time.time() - last_failed > self.grace_period: # the light is in a bad state for too long, highlight it!
                #print("HIGHLIGHT ", warning_light, time.time() - last_failed, self.grace_period)
                return self.highlight_action(warning_light, value=True)

    def unhighlight_warning_light(self, warning_light, desired_state):
        if self.is_highlighted(warning_light): 
            if self.warning_light_state[warning_light].state == desired_state: # the light is highlighted but in a good state, unhighlight it!
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
            if highlighted and (component in self.scale_state or 
                                component in self.warning_light_state or
                                component == self.system_panel): #only unhighlight components that belong to this task
                actions.append(self.highlight_action(component, value=False)) #add an action to turn off the highlighted
        return actions


class ICUSystemBody(ICUBody):

    def __init__(self, *args):
        super(ICUSystemBody, self).__init__(ICUSystemMind(*args), [ICUSystemSensor()])
