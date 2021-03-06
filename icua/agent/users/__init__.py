#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    Created on 21-10-2020 12:56:47

    [Description]
"""
__author__ = "Benedict Wilkins"
__email__ = "benrjw@gmail.com"
__status__ = "Development"

from . import user
from . import user_perfect
from . import user_delayed
from . import user_fixated
from . import user_fixed

def User(*args, **kwargs):
    return user.ICUUserBody(*args, **kwargs)

def PerfectUser(*args, **kwargs):
    return user_perfect.ICUUserBody(*args, **kwargs)

def DelayedUser(*args, delay=0.5, **kwargs):
    return user_delayed.ICUUserBody(*args, delay=delay, **kwargs)

def FixatedUser(*args, delay=0.5, **kwargs):
    return user_fixated.ICUUserBody(*args, delay=delay, **kwargs)

def FixedUser(*args, delay=0.5, **kwargs):
    return user_fixed.ICUUserBody(*args, delay=delay, **kwargs)