from contextlib import contextmanager
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

@contextmanager
def temp_user(keystone):
    username = random_string(prefix='user-')
    password = random_string()
    user = keystone.users.create(username, password, None)
    try:
        yield user, password
    finally:
        keystone.users.delete(user.id)

def pretty_dict(data):
    for key, value in data.iteritems():
        if isinstance(value, bool):
            continue
        if isinstance(value, int):
            continue
        data[key] = str(value)
    return data

def find_sec_group(nova, name):
    for group in nova.security_groups.list():
        if group.name == name:
            return group.id
    return None

def find_flavor(nova, name):
    for flavor in nova.flavors.list():
        if flavor.name == name:
            return flavor.id
    return None

def find_server(nova, name):
    for server in nova.servers.list():
        if server.name == name:
            return server
    return None

def find_image(nova, name):
    for image in nova.images.list():
        if image.name == name:
            return image
    return None

def find_volume(cinder, name):
    for volume in cinder.volumes.list():
        if volume.display_name == name:
            return volume
    return None

def find_user(keystone, name):
    if not name:
        return None
    for user in keystone.users.list():
        if user.name == name:
            return user
    return None

def find_role(keystone, name):
    if not name:
        return None
    for role in keystone.roles.list():
        if name.lower() == role.name.lower():
            return role
    return None

def find_project(keystone, name):
    if not name:
        return None
    for tenant in keystone.tenants.list():
        if tenant.name == name:
            return tenant
    return None

def find_network(neutron, name, tenant_id):
    for net in neutron.list_networks()['networks']:
        if net['name'] == name:
            if tenant_id:
                if tenant_id == net['tenant_id']:
                    return net
            else:
                return net
    return None

def find_subnet(neutron, name, tenant_id, network_id):
    for sub in neutron.list_subnets()['subnets']:
        if sub['name'] == name:
            if network_id:
                if sub['network_id'] == network_id:
                    return sub
            elif tenant_id:
                if tenant_id == sub['tenant_id']:
                    return sub
            else:
                return sub
    return None

def find_router(neutron, name, tenant_id):
    for router in neutron.list_routers()['routers']:
        if router['name'] == name:
            if tenant_id:
                if tenant_id == router['tenant_id']:
                    return router
            else:
                return router
    return None
