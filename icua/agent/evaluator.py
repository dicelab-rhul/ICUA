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


from pystarworlds.agent import new_sensor

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

        #pprint(window_properties)
        self.task_positions = {k:(v['position'][0] + v['size'][0]/2, v['position'][1] + v['size'][1]/2) for k,v in self.window_properties.items()}
        self.task_positions.update({k:(v['position'][0] + v['size'][0]/2, v['position'][1] + v['size'][1]/2) for k,v in self.window_properties['system'].items() if k in self.components})
        self.task_positions.update({k:(v['position'][0] + v['size'][0]/2, v['position'][1] + v['size'][1]/2) for k,v in self.window_properties['fuel'].items() if k in self.components})
        self.task_positions['Target:0'] = self.task_positions['track']

        #pprint(self.task_positions)
        self.eye_position = list(self.task_positions['window'])
        self.eye_to =  list(self.task_positions['window'])

        #pprint(self.components)


        # TRACKING EVALUATION
        # - evaluated in a normalised space (size of the tracking widget = (1,1))
        # - score in [0,1] range
        self.target = "Target:0"
        self.target_position = (0,0) # position of the target
        self.target_prop = np.array([1/6,1/6]) # TODO update if made configurable in ICU

        self.tracking_size = np.array(self.window_properties['track']['size'])
        
        # TODO this does not work as intended
        self.tracking_acceptable_prop = np.array([1/4, 1/4]) #TODO update if made configurable in ICU 
        w,h = self.tracking_acceptable_prop * self.tracking_size
        self.eval_tracking = EvalTracking(w=w,h=h)
        self.eval_tracking_time = EvalTime() # time spent outside of the acceptable range

        self.eval_warning_light0 = EvalTime()
        self.eval_warning_light1 = EvalTime()

        self.eval_scales = [EvalScale(config[c]['position'], c=config[c]['size'] // 2) for c in self.components if "Scale" in c]
        self.eval_tanks = {"FuelTank:A":EvalTime(), "FuelTank:B":EvalTime()} #two main tanks...?

        self.highlighted = {} # all false initially
        self.eval_highlighted = EvalTime()

        self.result = {}

    def revise(self, *perceptions):
        for percept in sorted(perceptions, key=lambda p: p.name):
            
            # HIGHLIGHT PERFORMANCE
            if percept.data.label == LABELS.highlight:
                src = percept.src.split(':', 1)[1]
                self.highlighted[src] = percept.data.value
                if any(self.highlighted.values()): # anything is highlighted after the event, start the timer
                    self.eval_highlighted.start() # has no effect if already started
                else: # nothing is highlighted, stop the timer
                    self.eval_highlighted.stop()

            # TRACKING PERFORMANCE
            elif percept.data.label == LABELS.move and 'x' in percept.data.__dict__:
                self.target_position = np.array([percept.data.x, percept.data.y])
                d = self.eval_tracking(*self.target_position)
                #denom = (self.tracking_size * (1 - (self.target_prop + self.tracking_acceptable_prop)))
                #print(2 * np.sqrt(np.sum(self.target_position**2)) / (self.tracking_size * (1 - self.target_prop)))
                #print(2 * d / denom)
                
                if d > 0:
                    self.eval_tracking_time.start() # target is now out of range, start the clock
                else:
                    self.eval_tracking_time.stop() # target is back in range, stop the clock
                
            # WARNING LIGHT PERFORMANCE
            elif percept.data.label == LABELS.change: # warning light changed its state
                if "WarningLight" in percept.src:
                    self.evaluate_warning_light(percept)
                elif "Scale" in percept.src:
                    self.evaluate_scales(percept)
            
            # TANK PERFORMANCE
            elif percept.data.label == LABELS.fuel:
                #print(percept)
                self.evaluate_tanks(percept)

    def evaluate_tanks(self, percept):
        e = self.eval_tanks[percept.src]
        if not percept.data.acceptable: # start clock, fuel tank not acceptable
            e.start()
        else:
            e.stop()

    def evaluate_scales(self, percept):
        e = self.eval_scales[int(percept.src.split(":")[1])]
        e(percept.data.value)

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
        def print_score():
            scores = "\nWarningLight:   {0:0.3f} {1:0.5f} {2:0.5f}".format(self.warning_light_score, self.eval_warning_light0.score, self.eval_warning_light1.score) + \
                "\nScales:         {0:0.3f} ".format(self.scale_score) + " ".join(["{0:0.3f}".format(e.score) for e in self.eval_scales]) + \
                "\nTracking:       {0:0.3f}".format(self.tracking_score) + \
                "\nFuel:           {0:0.3f}".format(self.fuel_score) + \
                "\nHighlight:      {0:0.3f}".format(self.highlight_score)
            print(scores)
            self.result = scores

        print_score()

        
    @property
    def warning_light_score(self):
        """ Average time spent in an unacceptable state. Normalised over the similation time.
            0 = warning lights are always good
            1 = warning lights are always bad
        
        Returns:
            float [0-1]: score
        """

        l0 = self.eval_warning_light0.score / (time.time() - self.eval_warning_light0.start_time)
        l1 = self.eval_warning_light1.score / (time.time() - self.eval_warning_light1.start_time)
        return ((l0 + l1) / 2)

    @property
    def scale_score(self):
        """
            Time weighted average distance from center, averaged over all scales.
            0 = good (scale is always in the correct central position)
            
        Returns:
            float: [0-n/2] score
        """
        return sum([e.score for e in self.eval_scales]) / len(self.eval_scales)

    @property
    def tracking_score(self):
        """ Distance from the acceptable region edge to the center of the target.
            0 = always acceptable
            1 = unacceptable - bad.

        Returns:
            float: [0-1] score
        """
        #d = self.eval_tracking(*self.target_position)
        denom = max(self.tracking_size * (1 - (self.target_prop + self.tracking_acceptable_prop))) #normalise the distance
        return 2 * self.eval_tracking.score / denom
        
    @property
    def fuel_score(self):
        """ Time spent with an unacceptable amount of fuel averaged over the two main tanks. Scores are normalised over duration of the run.
            0 = always acceptable
            1 = unacceptable

        Returns:
            float: [0-1] score
        """
        return (sum([t.score / (time.time() - t.start_time) for t in self.eval_tanks.values()]) / len(self.eval_tanks))

    @property
    def highlight_score(self):
        """ Time spent with a warning (highlight) active. Scores are normalised over duration of the run.
        
        Returns:
            float: [0-1] score
        """
        return self.eval_highlighted.score / (time.time() - self.eval_highlighted.start_time)
    


class ICUEvalBody(ICUBody):

    def __init__(self, *args):
        super(ICUEvalBody, self).__init__(Evaluator(*args), [ICUEvalSensor()])