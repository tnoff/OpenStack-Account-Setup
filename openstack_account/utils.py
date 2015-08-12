import random
import string
import time

def random_string(prefix='', length=20):
    chars = string.ascii_lowercase + string.digits
    s = ''.join(random.choice(chars) for _ in range(length))
    return prefix + s

def wait_status(function, obj_id, accept_states, reject_states,
                interval, timeout):
    obj = function(obj_id)
    expires = time.time() + timeout
    while time.time() <= expires:
        if obj.status in accept_states:
            return obj
        if obj.status in reject_states:
            return None
        time.sleep(interval)
        obj = function(obj_id)
    return None
