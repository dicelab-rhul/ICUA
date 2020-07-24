#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    Created on 24-07-2020 17:45:20

    [Description]
"""
__author__ = "Benedict Wilkins"
__email__ = "benrjw@gmail.com"
__status__ = "Development"


from pystarworlds.Event import Action, Executor

class ICUExecutor(Executor):

    def __call__(self, env, action):
        env.processes[0].sink(action.source, action.destination, action.data)

class ICUAction(Action):

    executor = ICUExecutor

    def __init__(self, dst, **data):
        super(ICUAction, self).__init__()
        self.destination = dst
        self.data = data