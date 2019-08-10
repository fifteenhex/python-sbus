CHANNEL_AILERON = 0
CHANNEL_ROLL = CHANNEL_AILERON
CHANNEL_ELEVATOR = 1
CHANNEL_PITCH = CHANNEL_ELEVATOR
CHANNEL_THROTTLE = 2
CHANNEL_RUDDER = 3
CHANNEL_YAW = CHANNEL_RUDDER


def channel_max(low, high):
    return high - low


def channel_clamp(value, low=200, high=1700):
    value = max(value, low)
    value = min(value, high)
    return value - low


def _float_clamp(value, low=0.0, high=1.0):
    value = max(value, low)
    value = min(value, high)
    return value


def channel_to_bool(value):
    if 0 <= value <= 1000:
        return False
    else:
        return True


def channel_to_float_linear(value, low=200, high=1700):
    value = (1.0 / channel_max(low, high)) * channel_clamp(value, low, high)
    return _float_clamp(value)


def channel_to_deflection(value, low=200, high=1700, deadband=100):
    value = channel_clamp(value, low, high)
    mid_point = channel_max(low, high) / 2
    active_low = mid_point - (deadband / 2)
    active_high = mid_point + (deadband / 2)
    if value < active_low:
        return -1
    elif value > active_high:
        return 1
    else:
        return 0


def mixer_steering(rudder):
    if rudder > 0:
        return abs(rudder), 0
    else:
        return 0, abs(rudder)
