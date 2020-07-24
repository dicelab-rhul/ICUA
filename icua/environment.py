#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    Created on 24-07-2020 17:45:28

    [Description]
"""
__author__ = "Benedict Wilkins"
__email__ = "benrjw@gmail.com"
__status__ = "Development"

import icu

import time
import random 
from pprint import pprint

from threading import Thread
from multiprocessing import Process

from icu.process import PipedMemory


from pystarworlds.Environment import Environment, Physics, Ambient, Process

from .action import ICUAction
from .perception import ICUPerception, perception

class ICUEventSink(icu.ExternalEventSink):

    def __init__(self):
        super(ICUEventSink, self).__init__()

class ICUEventSource(icu.ExternalEventSource):

    def __init__(self):
        super(ICUEventSource, self).__init__()

class ICUProcess(Process): #connection to the ICU environment via an environmental Process

    def __init__(self):
        self.__icu_sink = ICUEventSink()
        self.__icu_source = ICUEventSource()
        self.__icu_process, self.__icu_memory = icu.start(sinks=[self.__icu_sink], sources=[self.__icu_source])
        print("MEMORY:", self.__icu_memory.__dict__)
    
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
    
    def __init__(self, *agents):
       
        processes = [ICUProcess()]

        print("SHARED MEMORY")
        pprint(processes[0].shared_memory().window_properties)
        pprint(processes[0].shared_memory().event_sinks)
        pprint(processes[0].shared_memory().event_sources)
        pprint(processes[0].shared_memory().config.__dict__)

        config = processes[0].shared_memory().config # the configuration data used when launching ICU
        window_properties = processes[0].shared_memory().window_properties # the position of each widget in the current window

        if not isinstance(config, dict):
            config = config.__dict__

        agents = [agent(config, window_properties) for agent in agents]

        ambient = ICUAmbient(agents)
        physics = ICUPhysics([ICUAction])


        super(ICUEnvironment, self).__init__(physics, ambient, processes=processes)
        
    def simulate(self, *args, **kwargs):

        while self.processes[0].is_alive():
            self.evolve()
            time.sleep(.5)
        
        self.processes[0].join()





        


        




class ICUPhysics(Physics):
    pass 

class ICUAmbient(Ambient):
    pass 



