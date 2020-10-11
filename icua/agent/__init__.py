from . import agent
from . import fuel
from . import system
from . import track
from . import user
from . import evaluator


__all__ = ('agent', 'fuel', 'system', 'track', 'user', 'evaluator')

def FuelMonitor(*args, **kwargs):
    return fuel.ICUFuelBody(*args, **kwargs)

def SystemMonitor(*args, **kwargs):
    return system.ICUSystemBody(*args, **kwargs)

def TrackMonitor(*args, **kwargs):
    return track.ICUTrackBody(*args, **kwargs)

def User(*args, **kwargs):
    return user.ICUUserBody(*args, **kwargs)

def Evaluator(*args, **kwargs):
    return evaluator.ICUEvalBody(*args, **kwargs)
