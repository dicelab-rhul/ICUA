#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    Created on 24-07-2020 17:44:47

    [Description]
"""
__author__ = "Benedict Wilkins"
__email__ = "benrjw@gmail.com"
__status__ = "Development"

from pystarworlds.Agent import new_sensor

from .agent import ICUMind, ICUBody
from ..perception import FuelTankPerception, PumpPerception, EyeTrackerPerception
from ..action import ICUAction

ICUFuelSensor = new_sensor('ICUFuelSensor', FuelTankPerception, PumpPerception, EyeTrackerPerception)

class ICUFuelMind(ICUMind):

    def revise(self, *perceptions):
        for perception in perceptions:
            print(perception)

    def decide(self):
        return ICUAction()

class ICUFuelBody(ICUBody):

    def __init__(self):
        super(ICUFuelBody, self).__init__(ICUFuelMind(), [ICUFuelSensor()])
