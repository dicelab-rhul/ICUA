#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    Created on 21-09-2020 16:04:10

    [Description]
"""
__author__ = "Benedict Wilkins"
__email__ = "benrjw@gmail.com"
__status__ = "Development"

from types import SimpleNamespace
import time
import random

import icu
from pystarworlds.environment import Process

from .perception import perception


window_properties = {'fuel': {'FuelTank:A': {'position': (341.6666666666667, 424.0),
                         'size': (91.66666666666666, 100.0)},
          'FuelTank:B': {'position': (616.6666666666615, 424.0),
                         'size': (91.66666666666666, 100.0)},
          'FuelTank:C': {'position': (295.83333333333337, 576.0),
                         'size': (45.83333333333333, 100.0)},
          'FuelTank:D': {'position': (570.8333333333385, 576.0),
                         'size': (45.83333333333333, 100.0)},
          'FuelTank:E': {'position': (424.16666666666663, 576.0),
                         'size': (64.16666666666666, 100.0)},
          'FuelTank:F': {'position': (699.1666666666646, 576.0),
                         'size': (64.16666666666666, 100.0)},
          'Pump:AB': {'position': (512.1093749999973, 446.08333333333337),
                      'size': (25.78125, 22.5)},
          'Pump:BA': {'position': (512.1093749999973, 479.41666666666674),
                      'size': (25.78125, 22.5)},
          'Pump:CA': {'position': (305.859375, 538.75),
                      'size': (25.78125, 22.5)},
          'Pump:DB': {'position': (580.859375, 538.75),
                      'size': (25.78125, 22.5)},
          'Pump:EA': {'position': (443.359375, 538.75),
                      'size': (25.78125, 22.5)},
          'Pump:EC': {'position': (370.02604166666663, 614.75),
                      'size': (25.78125, 22.5)},
          'Pump:FB': {'position': (718.359375, 538.75),
                      'size': (25.78125, 22.5)},
          'Pump:FD': {'position': (645.0260416666708, 614.75),
                      'size': (25.78125, 22.5)},
          'position': (250.0, 400.0),
          'size': (550.0, 300.0)},
 'system': ({'Scale:0': {'position': (12.5, 121.24999999999999),
                         'size': (32.142857142857146, 236.25)},
             'Scale:1': {'position': (76.78571428571428, 121.24999999999999),
                         'size': (32.142857142857146, 236.25)},
             'Scale:2': {'position': (141.0714285714286, 121.24999999999999),
                         'size': (32.142857142857146, 236.25)},
             'Scale:3': {'position': (205.3571428571429, 121.24999999999999),
                         'size': (32.142857142857146, 236.25)},
             'WarningLight:0': {'position': (12.5, 42.5),
                                'size': (75.0, 47.25)},
             'WarningLight:1': {'position': (162.50000000000003, 42.5),
                                'size': (75.0, 47.25)},
             'position': (0.0, 25.0),
             'size': (250.0, 350.0)},),
 'track': ({'position': (350.0, 25.0), 'size': (350.0, 350.0)},),
 'window': {'position': (67, 57), 'size': (800, 700)}}

config = SimpleNamespace(**{'FuelTank:A': {'accept_position': 0.5,
                'accept_proportion': 0.3,
                'burn_rate': 6,
                'capacity': 2000,
                'fuel': 10},
 'FuelTank:B': {'accept_position': 0.5,
                'accept_proportion': 0.3,
                'burn_rate': 6,
                'capacity': 2000,
                'fuel': 1000},
 'FuelTank:C': {'capacity': 1000, 'fuel': 100},
 'FuelTank:D': {'capacity': 1000, 'fuel': 100},
 'FuelTank:E': {'capacity': 1000, 'fuel': 1000},
 'FuelTank:F': {'capacity': 1000, 'fuel': 1000},
 'Pump:AB': {'event_rate': 10, 'flow_rate': 100, 'state': 1},
 'Pump:BA': {'event_rate': 10, 'flow_rate': 100, 'state': 1},
 'Pump:CA': {'event_rate': 10, 'flow_rate': 100, 'state': 1},
 'Pump:DB': {'event_rate': 10, 'flow_rate': 100, 'state': 1},
 'Pump:EA': {'event_rate': 10, 'flow_rate': 100, 'state': 1},
 'Pump:EC': {'event_rate': 10, 'flow_rate': 100, 'state': 1},
 'Pump:FB': {'event_rate': 10, 'flow_rate': 100, 'state': 1},
 'Pump:FD': {'event_rate': 10, 'flow_rate': 100, 'state': 1},
 'Scale:0': {'key': '<F1>', 'position': 5, 'size': 11},
 'Scale:1': {'key': '<F2>', 'position': 5, 'size': 11},
 'Scale:2': {'key': '<F3>', 'position': 5, 'size': 11},
 'Scale:3': {'key': '<F4>', 'position': 5, 'size': 11},
 'Target:0': {'invert': True, 'step': 1},
 'WarningLight:0': {'grace': 2, 'key': '<F5>', 'state': 1},
 'WarningLight:1': {'grace': 2, 'key': '<F6>', 'state': 0},
 'background_colour': 'blue',
 'input': {'eyetracker': {'calibrate': False,
                          'enabled': True,
                          'sample_rate': 100,
                          'stub': True},
           'joystick': False,
           'keyboard': True,
           'mouse': True},
 'overlay': {'arrow': True,
             'enable': True,
             'highlight_colour': 'red',
             'highlight_thickness': 4,
             'outline': True,
             'transparent': True},
 'screen_aspect': None,
 'screen_full': False,
 'screen_height': 700,
 'screen_max_size': (2000, 2000),
 'screen_min_size': (400, 400),
 'screen_position': (0, 0),
 'screen_resizable': True,
 'screen_size': (800, 700),
 'screen_width': 800,
 'screen_x': 0,
 'screen_y': 0,
 'task': {'fuel': True, 'system': True, 'track': True}})

class ICUProcessStub(Process):

    """
        MP event generation stress test for agents (DOESNT WORK WELL DUE TO OS SCHEDULING?)
    """

    def __init__(self, *args, **kwargs):

        self.e_sink = icu.ExternalEventSink()
 
        self.pumps = ['Pump:AB', 'Pump:BA', 'Pump:CA', 'Pump:DB', 'Pump:EA', 'Pump:EC', 'Pump:FB', 'Pump:FD']
        self.tanks = ['FuelTank:A', 'FuelTank:B', 'FuelTank:C', 'FuelTank:D', 'FuelTank:E', 'FuelTank:F',]
        self.warninglights = ['WarningLight:0', 'WarningLight:1']
        self.scales = ['Scale:0', 'Scale:1', 'Scale:2', 'Scale:3']
        self.targets = ['Target:0']

        print("pumps: ", self.pumps)
        print("tanks: ", self.tanks)
        print("warninglights: ", self.warninglights)
        print("scales:", self.scales)
        print("targets:", self.targets)

        self.generators = [*[icu.generator.WarningLightEventGenerator(p) for p in self.warninglights],
                            *[icu.generator.PumpEventGenerator(p) for p in self.pumps],
                            *[icu.generator.ScaleEventGenerator(p) for p in self.scales],
                            *[icu.generator.TargetEventGenerator(p) for p in self.targets]]
        
        class ClickGenerator:
            
            def __next__(self):
                return Event("Canvas", self.__warning_light, label=C.EVENT_LABEL_SWITCH)

        
        self.run_for = 3
        
        from multiprocessing import Process as MProcess
        self.process = MProcess(target=self.run, args=(self.e_sink,))
        self.process.daemon = False 
        self.process.start()


    def run(self, sink, *args, **kwargs):
        # add some events
        start_time = time.time()
        while time.time() - start_time < self.run_for:

            #time.sleep(0.000001) 
            
            #generate some events
            event = next(self.generators[0])
            sink._ExternalEventSink__buffer.put(event)

    def __call__(self, *args, **kwargs):
        events = []
        if self.process.is_alive():
            while not self.e_sink.empty():
                event = perception(self.e_sink.get())
                events.append(event)
        print("events:", len(events))
        return events
                            
    def sink(self, *arg, **kwargs):
        return lambda *args, **kwargs: None  
    
    def is_alive(self):
        return self.process.is_alive()

    def join(self):
        self.process.join()

    def shared_memory(self):
        return SimpleNamespace(config=config, window_properties = window_properties)


class ICUProcessStub2(Process):

    """
        Serial event generation stress test for agents (DOESNT WORK WELL DUE TO OS SCHEDULING?)
    """

    def __init__(self, *args, **kwargs):

        self.e_sink = icu.ExternalEventSink()
 
        self.pumps = ['Pump:AB', 'Pump:BA', 'Pump:CA', 'Pump:DB', 'Pump:EA', 'Pump:EC', 'Pump:FB', 'Pump:FD']
        self.tanks = ['FuelTank:A', 'FuelTank:B', 'FuelTank:C', 'FuelTank:D', 'FuelTank:E', 'FuelTank:F',]
        self.warninglights = ['WarningLight:0', 'WarningLight:1']
        self.scales = ['Scale:0', 'Scale:1', 'Scale:2', 'Scale:3']
        self.targets = ['Target:0']

        print("pumps: ", self.pumps)
        print("tanks: ", self.tanks)
        print("warninglights: ", self.warninglights)
        print("scales:", self.scales)
        print("targets:", self.targets)

        self.generators = [*[icu.generator.WarningLightEventGenerator(p) for p in self.warninglights],
                            *[icu.generator.PumpEventGenerator(p) for p in self.pumps],
                            *[icu.generator.ScaleEventGenerator(p) for p in self.scales],
                            *[icu.generator.TargetEventGenerator(p) for p in self.targets]]
        
        class ClickGenerator:
            
            def __next__(self):
                return Event("Canvas", self.__warning_light, label=C.EVENT_LABEL_SWITCH)

        self.num_events = 1000000

    def run(self, sink, *args, **kwargs):
        pass 

    def __call__(self, *args, **kwargs):
        

        events = [perception(next(self.generators[random.randint(0,len(self.generators)-1)])) for i in range(self.num_events)]
        #print("events:", len(events))
        return events
                            
    def sink(self, *arg, **kwargs):
        return lambda *args, **kwargs: None  
    
    def is_alive(self):
        return True

    def join(self):
        pass

    def shared_memory(self):
        return SimpleNamespace(config=config, window_properties = window_properties)
