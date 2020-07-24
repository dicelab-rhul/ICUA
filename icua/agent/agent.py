#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    Created on 24-07-2020 17:44:58

    [Description]
"""
__author__ = "Benedict Wilkins"
__email__ = "benrjw@gmail.com"
__status__ = "Development"

from abc import abstractmethod

from pystarworlds.Agent import Body, Mind, new_actuator, new_sensor

from ..action import ICUAction

ICUActuator = new_actuator('ICUActuator', ICUAction) #common across all agents

class ICUMind(Mind):

        
    def cycle(self):
        perceptions = self.body.perceive()
        perceptions = next(iter(perceptions.values())) #only 1 sensor
        self.revise(*perceptions)

        actuator = next(iter(self.body.actuators.keys()))
        actions = self.decide()

        if isinstance(actions, (list, tuple)):
            for action in actions:
                self.body.attempt(**{actuator:action})
        else:
            self.body.attempt(**{actuator:actions})

    @abstractmethod
    def revise(self, *perceptions):
        pass 

    @abstractmethod
    def decide(self):
        pass

class ICUBody(Body):

    def __init__(self, mind, sensors):
        super(ICUBody, self).__init__(mind, [ICUActuator()], sensors)
