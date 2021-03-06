#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    Created on 11-10-2020 15:37:41

    [Description]
"""
__author__ = "Benedict Wilkins"
__email__ = "benrjw@gmail.com"
__status__ = "Development"

from abc import abstractmethod
import time

class Eval:
    
    @abstractmethod
    def __call__(self, *args, **kwargs):
        pass

class CMA:

    def __init__(self):
        self._n = 0
        self._avg = 0
    
    @property
    def avg(self):
        if self._n < 0:
            return float('nan')
        return self._avg

    def __call__(self, x, w=1):
        nc = self._n + w
        self._avg = ((self._avg * self._n) + w * x) / nc
        self._n = nc
        return self.avg

    def reset(self):
        self._n = 0
        self._avg = 0

class EvalTime:

    def __init__(self):
        self.t = None
        self.f = False
        self._score = 0
        self.start_time = time.time()

    def start(self):
        if not self.f:
            self.t = time.time()
            self.f = True

    def stop(self):
        if self.f: 
            self._score += time.time() - self.t
            self.f = False

    @property
    def score(self):
        if self.f: # currently running so add to score
            return self._score + time.time() - self.t
        return self._score

class EvalScale:

    def __init__(self, x, c=5):
        self.c = c
        self.cma = CMA()
        self.t = time.time()
        self.px = x
        
    def __call__(self, x):
        t = time.time()
        d = abs(self.px - self.c)
        self.cma(d, t - self.t) #time weighted average
        #print(d, t - self.t)
        self.t = t
        self.px = x
        return d

    @property
    def score(self):
        return self.cma.avg


class EvalTracking: 
    """
        Statistics for distance of target from center.
    """

    def __init__(self, cx=0, cy=0, w=0, h=0):
        """

        Args:
            cx (float, optional): center of the tracking widget (relative). Defaults to 0.
            cy (float, optional): center of the tracking widget (relative). Defaults to 0.
            w (float, optional): (total) width of the acceptable region. Defaults to 0.
            h (float, optional): (total) height of the acceptable region. Defaults to 0.
        
        Acceptable region is always treated as 0, the region is computed as:
            (cx - w/2, cy - h/2, cx + w/2, cy + h/2)
        """
        self.position = (cx,cy)
        self.size = (w,h)
        self.cma = CMA()

    @property
    def score(self):
        return self.cma.avg

    @property
    def steps(self):
        return self.cma.n

    def reset(self):
        self.cma.reset()

    def __call__(self, x, y):
        px, py = self.position
        w, h = self.size
        dx = max(abs(x - px) - w / 2, 0)
        dy = max(abs(y - py) - h / 2, 0)

        d = max(abs(dx), abs(dy))
        self.cma(d) # update moving average distance...
        return d

# - total time warnings are displayed