#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    Created on 11-10-2020 15:36:10

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

from ..evaluate import EvalTracking, EvalTime, EvalScale

from .agent import ICUMind, ICUBody
from ..perception import WarningLightPerception, ScalePerception, TrackPerception, FuelTankPerception, PumpPerception, EyeTrackerPerception, HighlightPerception
from ..action import ICUAction, InputAction

ICUEvalSensor = new_sensor('ICUEvalSensor', WarningLightPerception, ScalePerception, TrackPerception, FuelTankPerception, PumpPerception, EyeTrackerPerception, HighlightPerception)

LABELS = SimpleNamespace(switch='switch', slide='slide', click='click', highlight='highlight',
                             gaze='gaze', saccade='saccade', key='key', move='move', change='change',
                              fuel='fuel')

KEY_CODES = {"Up":98, "Down":104, "Left":100, "Right":102}

class Evaluator(ICUMind):

    def __init__(self, config, window_properties):
        super(Evaluator, self).__init__()
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


        # TRACKING EVALUATION
        # - evaluated in a normalised space (size of the tracking widget = (1,1))
        # - score in [0,1] range
        self.target = "Target:0"
        self.target_position = (0,0) # (normalised) position of the target
        self.target_prop = np.array([1/6,1/6]) # TODO update if made configurable in ICU

        self.tracking_size = np.array(self.window_properties['track']['size'])
        
        # TODO this does not work as intended
        self.tracking_acceptable_prop = np.array([1/4, 1/4]) #TODO update if made configurable in ICU 
        self.tracking_acceptable_prop = 2 * (self.tracking_acceptable_prop * self.tracking_size) / ((1 - self.target_prop) * self.tracking_size) #includes size of target to get 0-1 range 

        self.eval_tracking = EvalTracking(w=self.tracking_acceptable_prop[0], h=self.tracking_acceptable_prop[1])
        self.eval_tracking_time = EvalTime() # time spent outside of the acceptable range


        self.eval_warning_light0 = EvalTime()
        self.eval_warning_light1 = EvalTime()

        self.eval_scales = [EvalScale() for c in self.components if "Scale" in c]
        self.eval_tanks = {"FuelTank:A":EvalTime(), "FuelTank:B":EvalTime()} #two main tanks...?

        self.highlighted = defaultdict(lambda: (False, 0.)) # is the component highlighted?

    def revise(self, *perceptions):
        for percept in sorted(perceptions, key=lambda p: p.name):

            if percept.data.label == LABELS.highlight:
                src = percept.src.split(':', 1)[1]
                if self.highlighted[src][0] != percept.data.value: #its a new highlight event
                    self.highlighted[src] = (percept.data.value, percept.timestamp)

            # TRACKING PERFORMANCE MEASURES
            elif percept.data.label == LABELS.move and 'x' in percept.data.__dict__:
                position = np.array([percept.data.x, percept.data.y])
                self.target_position =  2 * position / ((1 - self.target_prop) * self.tracking_size) #TODO
                #self.target_position = position / self.tracking_size

                d = self.eval_tracking(*self.target_position)
                #print(d, self.target_position)
                if d > 0:
                    self.eval_tracking_time.start() # target is now out of range, start the clock
                else:
                    self.eval_tracking_time.stop() # target is back in range, stop the clock
                
            # WARNING LIGHT EVALUATION
            elif percept.data.label == LABELS.change: # warning light changed its state
                if "WarningLight" in percept.src:
                    self.evaluate_warning_light(percept)
                elif "Scale" in percept.src:
                    self.evaluate_scales(percept)

            elif percept.data.label == LABELS.fuel:
                self.evaluate_tanks(percept)


        self.priority = dict(filter(lambda x: x[1][1], self.highlighted.items()))
        self.priority =  [k for k,v in sorted(self.priority.items(), key=lambda x: x[1][1])] #sort by timestep
        if len(self.priority) > 0:
            self.eye_to = self.task_positions[self.priority[0]]
        else:
            self.eye_to = self.task_positions['window'] #default position, no warnings are being displayed

    def evaluate_tanks(self, percept):
        e = self.eval_tanks[percept.src]
        if not percept.data.acceptable: # start clock, fuel tank not acceptable
            e.start()
        else:
            e.stop()
        #print(e.score)

    def evaluate_scales(self, percept):
        e = self.eval_scales[int(percept.src.split(":")[1])]
        e(percept.data.value)
        #print(e.score)

    def evaluate_warning_light(self, percept):
        """ 
            Total time spent in a bad state for each warning light.
        """
        if percept.src == "WarningLight:0":
            if not percept.data.value:
                self.eval_warning_light0.start()
            else:
                self.eval_warning_light0.stop()
                #print(percept.src, self.eval_warning_light0.score)

        elif percept.src == "WarningLight:1":
            if percept.data.value:
                self.eval_warning_light1.start()
            else:
                self.eval_warning_light1.stop()
                #print(percept.src, self.eval_warning_light1.score)

  

    def decide(self):
        #print(self.eval_tracking_time.score)
        pass
    

class ICUEvalBody(ICUBody):

    def __init__(self, *args):
        super(ICUEvalBody, self).__init__(Evaluator(*args), [ICUEvalSensor()])



