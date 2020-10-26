from . import agent
from . import fuel
from . import system
from . import track
from . import evaluator
from . import users

__all__ = ('agent', 'fuel', 'system', 'track', 'users', 'evaluator')

def FuelMonitor(*args, **kwargs):
    return fuel.ICUFuelBody(*args, **kwargs)

def SystemMonitor(*args, **kwargs):
    return system.ICUSystemBody(*args, **kwargs)

def TrackMonitor(*args, **kwargs):
    return track.ICUTrackBody(*args, **kwargs)

def Evaluator(*args, **kwargs):
    return evaluator.ICUEvalBody(*args, **kwargs)
