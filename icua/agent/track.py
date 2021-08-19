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
from ..perception import TrackPerception, EyeTrackerPerception, HighlightPerception
from ..action import ICUAction

ICUTrackSensor = new_sensor('ICUTrackSensor', TrackPerception, EyeTrackerPerception, HighlightPerception)

class ICUTrackMind(ICUMind):

    LABELS = SimpleNamespace(move='move',  key='key', highlight='highlight', gaze='gaze', saccade='saccade')

    def __init__(self, config, window_properties):
        super(ICUTrackMind, self).__init__()

        # agents beliefs
        (x,y), (w,h) = window_properties['track']['position'], window_properties['track']['size']
        self.bounding_box = (x,y,x+w,y+h) # location of the system monitoring task (in window coordinates)

        self.eye_position = (0,0) #gaze position of the users eyes
        # mirrored state of each component of the system monitoring task (updated in revise)
   
        
        self.target_state = copy.deepcopy({k:v for k,v in config.items() if 'Target' in k})
        assert len(self.target_state) == 1 #multiple targets???
        self.target = next(iter(self.target_state.keys())) #target id
        self.target_state = self.target_state[self.target]
        assert 'position' not in self.target_state
        self.target_state['position'] = (0,0) #TODO update if we add a config option for position!
        
        self.highlighted = defaultdict(lambda: False) # is the component highlighted?
        self.last_viewed = 0 # when was this task last viewed? (never)
        self.last_failed = 0 # when did this component last fail? 

        # control variables
        self.distance_threshold = 50 # how far from the center can the target be? (pixels)
        
        #self.grace_period = 2 # how long should I wait before giving the user some feedback if something is wrong
        #self.grace_period = 2

        # control variables from config TODO streamline using defaults
        try:
            self.grace_period = config['agent']['track']['grace_period']
        except:
            self.grace_period = 2

    def revise(self, *perceptions):
        for perception in sorted(perceptions, key=lambda p: p.name):

            assert perception.data.label in ICUTrackMind.LABELS.__dict__ #received an unknown event
            
            if perception.data.label == ICUTrackMind.LABELS.gaze: #gaze position
                #print("EYE MOVED", self.eye_position)
                self.eye_position = (perception.data.x, perception.data.y)
                if self.is_looking():
                    self.last_viewed = perception.timestamp
            
            elif perception.data.label == ICUTrackMind.LABELS.move: #the tracking target moved
                if perception.src == self.target: #otherwise ignore it (TODO is there any nice fix in ICU? or perhaps block unwanted events down stream)
                    #print(perception.data.x, perception.data.y)
                    x,y = self.target_state['position']
                    d_old = (x**2 + y**2)**0.5 
                    self.target_state['position'] = (perception.data.x, perception.data.y) # TODO last_failed
                    x,y = self.target_state['position']
                    d_new = (x**2 + y**2)**0.5 
                    if d_new > self.distance_threshold and d_old <= self.distance_threshold: # if transition from good to bad 
                        self.last_failed = time.time()

            elif perception.data.label == ICUTrackMind.LABELS.highlight:
                src = perception.src.split(':', 1)[1]
                self.highlighted[src] = perception.data.value

    def decide(self):

        x,y = self.target_state['position']
        d = (x**2 + y**2)**0.5 

        if not self.is_looking():
            if not any(self.highlighted.values()):
                if time.time() - self.last_viewed > self.grace_period:
                    if time.time() - self.last_failed > self.grace_period:
                        
                        if not self.is_highlighted() and d > self.distance_threshold: #the target is away from the center!
                            return self.highlight_action(self.target, value=True)
                        elif self.is_highlighted() and d < self.distance_threshold:
                            return self.highlight_action(self.target, value=False)
        else:   
            if self.is_highlighted(): #if the user is looking and the task is highlighted, unhighlight it
                return self.highlight_action(self.target, value=False)
                
        if d <= self.distance_threshold and self.is_highlighted():
            return self.highlight_action(self.target, value=False)
    
    def others_highlighted(self): # are there currently any highlights?
        return any(self.highlighted.values())

    def is_highlighted(self): # is a component currently highlighted?
        return self.highlighted[self.target]

    def is_looking(self): #is the user looking at the system monitoring task?
        ex, ey = self.eye_position
        x1,y1,x2,y2= self.bounding_box
        return not (ex < x1 or ey < y1 or ex > x2 or ey > y2)

class ICUTrackBody(ICUBody):

     def __init__(self, *args):
        super(ICUTrackBody, self).__init__(ICUTrackMind(*args), [ICUTrackSensor()])

