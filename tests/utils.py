from Crypto.PublicKey import RSA
import contextlib
import os
import time
import unittest

from openstack_portation.client import PortationClient, PortationResults
from tests import settings

from neutronclient.common.exceptions import NotFound

deletion_map = {
    'nova_quota' : {
        'delete' : None,
    },
    'cinder_quota' : {
        'delete' : None,
    },
    'os_tenant_name' : {
        'delete' : None,
    },
    'source_file' : {
        'delete' : None,
    },
    'project' : {
        'delete' : ['keystone', 'tenants', 'delete'],
    },
    'user' : {
        'delete' : ['keystone', 'users', 'delete'],
    },
    'flavor' : {
        'delete' : ['nova', 'flavors', 'delete'],
    },
    'security_group' : {
        'delete' : ['nova', 'security_groups', 'delete'],
    },
    'server' : {
        'delete' : ['nova', 'servers', 'delete'],
        'list' : ['nova', 'servers', 'list'],
    },
    'keypair' : {
        'delete' : ['nova', 'keypairs', 'delete'],
    },
    'volume' : {
        'delete' : ['cinder', 'volumes', 'delete'],
        'list' : ['cinder', 'volumes', 'list'],
    },
    'image' : {
        'delete' : ['glance', 'images', 'delete'],
        'list' : ['glance', 'images', 'list'],
    },
    'router' : {
        'delete' : ['neutron', 'delete_router'],
    },
    'subnet' : {
        'delete' : ['neutron', 'delete_subnet'],
    },
    'network' : {
        'delete' : ['neutron', 'delete_network'],
    },
}

@contextlib.contextmanager
def temp_keypair(filename):
    key = RSA.generate(2048)
    pubkey = key.publickey()
    with open(filename, 'w') as f:
        f.write(pubkey.exportKey('OpenSSH'))
    os.chmod(filename, 0600)
    try:
        yield None
    finally:
        os.remove(filename)

@contextlib.contextmanager
def temp_file(filename):
    try:
        yield filename
    finally:
        os.remove(filename)

def get_deletion_function(key, client):
    try:
        del_map = deletion_map[key]['delete']
    except KeyError:
        raise Exception("Key not found in deletion map:%s", key)
    # if none skip
    try:
        module_name = del_map[0]
    except TypeError:
        return None
    module = getattr(client, module_name)
    sub_module = getattr(module, del_map[1])
    if len(del_map) > 2:
        sub_module = getattr(sub_module, del_map[2])
    return sub_module

def get_list_function(key, client):
    try:
        list_map = deletion_map[key]['list']
    except KeyError:
        return None
    try:
        module_name = list_map[0]
    except TypeError:
        return None
    module = getattr(client, module_name)
    sub_module = getattr(module, list_map[1])
    if len(list_map) > 2:
        sub_module = getattr(sub_module, list_map[2])
    return sub_module

def wait_deletion(obj_id, list_function, timeout=120, interval=5):
    if not list_function:
        return True
    stop = time.time() + timeout
    while True:
        obj_list = list_function()
        if obj_id not in [i.id for i in obj_list]:
            return True
        time.sleep(interval)
        if time >= stop:
            return False

def special_pre_deletion(client, results):
    # find all results with "router" and act accordingly
    for result in results:
        for key, value in result.iteritems():
            if key == 'router':
                # delete all possible subnets as interfaces
                for subnet in client.neutron.list_subnets()['subnets']:
                    data = {'subnet_id' : subnet['id']}
                    try:
                        client.neutron.remove_interface_router(value, data)
                    except NotFound:
                        continue


class TestClient(unittest.TestCase):
    def setUp(self):
        self.client = PortationClient(settings.OS_USERNAME,
                                      settings.OS_PASSWORD,
                                      settings.OS_TENANT_NAME,
                                      settings.OS_AUTH_URL,)

        self.results = PortationResults()

    def tearDown(self):
        special_pre_deletion(self.client, self.results)
        for result in reversed(self.results):
            # assume each result is a dictionary with one item
            keys = result.keys()
            for key in keys:
                del_function = get_deletion_function(key, self.client)
                list_function = get_list_function(key, self.client)
                if del_function:
                    value = result[key]
                    del_function(value)
                    wait_deletion(value, list_function)
