"""Notification transition rules. UNKNOWN never rearms an existing alert."""
def should_notify(previous, current):
    if current not in {'AVAILABLE', 'SOLD_OUT', 'UNKNOWN'}:
        raise ValueError('invalid availability status')
    return current == 'AVAILABLE' and previous.get('last_confirmed') != 'AVAILABLE'


def advance(previous, current, *, delivered=False):
    state = dict(previous)
    state['last_observed'] = current
    if current == 'SOLD_OUT':
        state['last_confirmed'] = current
    elif current == 'AVAILABLE':
        if delivered or previous.get('last_confirmed') == 'AVAILABLE':
            state['last_confirmed'] = current
    elif current != 'UNKNOWN':
        raise ValueError('invalid availability status')
    return state
