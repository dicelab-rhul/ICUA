from icu.config import Option, validate_options, is_type

# specify ICUA options

options_system_ag = dict(
    grace_period = Option('system', is_type(int, float)),
    highlight = Option('system', is_type(str))
)
options_fuel_ag = dict(
    grace_period = Option('fuel', is_type(int, float)),
    highlight = Option('fuel', is_type(str))
)
options_track_ag = dict(
    grace_period = Option('track', is_type(int, float))
) 

options_agent = dict(
    system = Option("agent", validate_options('system', _options=options_system_ag)),
    fuel = Option("agent", validate_options('fuel', _options=options_fuel_ag)),
    track = Option("agent", validate_options('track', _options=options_track_ag)),  
)

options = dict(
    agent = Option("main", validate_options('agent', _options=options_agent)),
)


# default options for ICUA
defaults = dict(
    # TODO!
)

