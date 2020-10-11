#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    Created on 24-07-2020 17:45:28

    [Description]
"""
__author__ = "Benedict Wilkins"
__email__ = "benrjw@gmail.com"
__status__ = "Development"

CYCLE_DELAY = 0.1 # seconds WARNING see below
assert CYCLE_DELAY > 10e-4 #otherwise crash (interprocess communication cant keep up)

import icu

import time
import random 
from pprint import pprint

from threading import Thread

from icu.process import PipedMemory

from pystarworlds.Environment import Environment, Physics, Ambient, Process

from .action import ICUAction, InputAction
from .perception import ICUPerception, perception

from .icu_stub import ICUProcessStub, ICUProcessStub2 # EXPERIMENTS

class ICUEventSink(icu.ExternalEventSink):

    def __init__(self):
        super(ICUEventSink, self).__init__()

class ICUEventSource(icu.ExternalEventSource):

    def __init__(self):
        super(ICUEventSource, self).__init__()

class ICUProcess(Process): #connection to the ICU environment via an environmental Process

    def __init__(self, *args, **kwargs):
        self.__icu_sink = ICUEventSink()
        self.__icu_source = ICUEventSource()
        self.__icu_process, self.__icu_memory = icu.start(*args, sinks=[self.__icu_sink], sources=[self.__icu_source], **kwargs)
    
    def shared_memory(self):
        return self.__icu_memory

    def __call__(self, *args, **kwargs):
        events = []
        if self.__icu_process.is_alive():
            while not self.__icu_sink.empty():
                event = perception(self.__icu_sink.get())
                events.append(event)

        return events

    def sink(self, agent, destination, data): #send an event to the icu system
        self.__icu_source.source(agent, destination, **data)

    def join(self):
        self.__icu_process.join()

    def is_alive(self):
        return self.__icu_process.is_alive()

class ICUEnvironment(Environment):
    
    def __init__(self, *agents, **kwargs):

       
        #processes = [ICUProcessStub2()]
        processes = [ICUProcess(**kwargs)]
        print("SHARED MEMORY")
        #pprint(processes[0].shared_memory().window_properties)
        #pprint(sorted(processes[0].shared_memory().event_sinks))
        #pprint(processes[0].shared_memory().event_sources)
        #pprint(processes[0].shared_memory().config)

        config = processes[0].shared_memory().config # the configuration data used when launching ICU
        window_properties = processes[0].shared_memory().window_properties # the position of each widget in the current window

        if not isinstance(config, dict):
            config = config.__dict__

        agents = [agent(config, window_properties) for agent in agents]

        ambient = ICUAmbient(agents)
        physics = ICUPhysics([ICUAction, InputAction])


        super(ICUEnvironment, self).__init__(physics, ambient, processes=processes)
        
    def simulate(self, *args, **kwargs):

        while self.processes[0].is_alive():
            self.evolve()
            time.sleep(CYCLE_DELAY)
        
        self.processes[0].join()

    def evolveEnvironment(self): #TODO remove in favour of evolve
        #allow all processes to do their thing
        total_events = 0
        for process in self.processes:
            events = process(self)
            total_events += len(events)
            self.execute_events(events)

        # measure time to execute
        #start_time = time.time()
        
        agents = self.ambient.agents.values()
        for a in agents:
            a.cycle()

        #print("Agents took: {0} to process {1} events.".format(time.time() - start_time, total_events))
        attempts = [action for agent in agents for actuator in agent.actuators.values() for action in actuator]
        events = self.execute_events(attempts)
        
    def execute_events(self, events): # this should be moved into pystarworlds
        events = self.physics.execute(self, events)
       
        if len(events) > 0:
            #print("EVENTS:", len(events))
            self.execute_events(events)



        


        




class ICUPhysics(Physics):
    pass 

class ICUAmbient(Ambient):
    pass 



"""
 'Canvas',
 'EyeTrackerStub',
 'Highlight:FuelTank:A',
 'Highlight:FuelTank:B',
 'Highlight:FuelTank:C',
 'Highlight:FuelTank:D',
 'Highlight:FuelTank:E',
 'Highlight:FuelTank:F',
 'Highlight:Pump:AB',
 'Highlight:Pump:BA',
 'Highlight:Pump:CA',
 'Highlight:Pump:DB',
 'Highlight:Pump:EA',
 'Highlight:Pump:EC',
 'Highlight:Pump:FB',
 'Highlight:Pump:FD',
 'Highlight:Scale:0',
 'Highlight:Scale:1',
 'Highlight:Scale:2',
 'Highlight:Scale:3',
 'Highlight:Target:0',
 'Highlight:WarningLight:0',
 'Highlight:WarningLight:1',
 'KeyHandler',
 'Overlay:0',
 'PumpEventGenerator',
 'ScaleEventGenerator',
 'TargetEventGenerator',
 'WarningLightEventGenerator'
"""

