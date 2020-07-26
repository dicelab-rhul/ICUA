#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    Created on 24-07-2020 17:44:58

    [Description]
"""
__author__ = "Benedict Wilkins"
__email__ = "benrjw@gmail.com"
__status__ = "Development"

from types import SimpleNamespace

from abc import abstractmethod

from pystarworlds.Agent import Body, Mind, new_actuator, new_sensor

from ..action import ICUAction

ICUActuator = new_actuator('ICUActuator', ICUAction) #common across all agents

class ICUMind(Mind):

    LABELS = SimpleNamespace(switch='switch', slide='slide', click='click', highlight='highlight',
                             gaze='gaze', saccade='saccade', move='move')

    def __init__(self):
        super(ICUMind, self).__init__()

    def cycle(self):
        perceptions = self.body.perceive()
        perceptions = next(iter(perceptions.values())) #only 1 sensor
        self.revise(*perceptions) # process perceptions and update beliefs

        actuator = next(iter(self.body.actuators.keys()))
        actions = self.decide() # decide on actions based on beliefs

        # execute with an actuator
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

    def highlight_action(self, dst, value=True):
        """ Create a new highlight action.

        Args:
            dst (str): ICU destination (id of the component to end the event)
            value (bool, optional): highlight/dehighlight. Defaults to True.

        Returns:
            ICUAction: the action
        """
        if not dst.startswith('Highlight'):
            dst = 'Highlight:{0}'.format(dst)
        print("HIGHLIGHT", dst, value)
        return ICUAction(dst, label=ICUMind.LABELS.highlight, value=value)


class ICUBody(Body):

    def __init__(self, mind, sensors):
        super(ICUBody, self).__init__(mind, [ICUActuator()], sensors)



