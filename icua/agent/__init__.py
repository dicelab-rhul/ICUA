from . import agent
from . import fuel
from . import system
from . import track

__all__ = ('agent', 'fuel', 'system', 'track')

def FuelMonitor(*args, **kwargs):
    return fuel.ICUFuelBody(*args, **kwargs)

def SystemMonitor(*args, **kwargs):
    return system.ICUSystemBody(*args, **kwargs)

def TrackMonitor(*args, **kwargs):
    return track.ICUTrackBody(*args, **kwargs)

