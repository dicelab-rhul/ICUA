#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    Created on 24-07-2020 17:45:20

    [Description]
"""
__author__ = "Benedict Wilkins"
__email__ = "benrjw@gmail.com"
__status__ = "Development"

from types import SimpleNamespace
import time

from pystarworlds.event import Action, Executor
from .perception import ICUPerception, EyeTrackerPerception



class ICUExecutor(Executor):

    def __call__(self, env, action):
        env.icuprocess.sink(action.source, action.destination, action.data)

class ICUAction(Action):

    executor = ICUExecutor

    def __init__(self, dst, **data):
        super(ICUAction, self).__init__()
        self.destination = dst
        self.data = data

class InputExecutor(ICUExecutor): # used for fake input that originates from agents, ensures that the input is sent to both ICU and any agents that subscribe to user input events

    def __call__(self, env, action):
        super().__call__(env, action) # send event to icu...
        event = SimpleNamespace(timestamp=time.time(), src=action.source, dst=action.destination, name='0', data=SimpleNamespace(**action.data)) #fake event... a bit hacky... hopefully the name doesnt cause any problems
        return (EyeTrackerPerception(event),)

class InputAction(ICUAction):
    executor = InputExecutor

