from Crypto.PublicKey import RSA
import os
import unittest

from openstack_account.client import AccountSetup
from openstack_account.exceptions import OpenStackAccountError

from tests import settings
from tests.data import cinder as cinder_data
from tests.data import flavors as flavor_data
from tests.data import glance as glance_data
from tests.data import keypair as keypair_data
from tests.data import keystone as keystone_data
from tests.data import neutron as neutron_data
from tests.data import quotas as quota_data
from tests.data import security_groups as sec_data
from tests.data import server as server_data

def find_tenant(keystone, tenant_name):
    for tenant in keystone.tenants.list():
        if tenant.name == tenant_name:
            return tenant.id
    return None

def find_image(glance, image_name):
    for im in glance.images.list():
        if im.name == image_name:
            return im
    return None

class TestOSAccount(unittest.TestCase):
    def setUp(self):
        self.client = AccountSetup(settings.OS_USERNAME,
                                   settings.OS_PASSWORD,
                                   settings.OS_TENANT_NAME,
                                   settings.OS_AUTH_URL,)

    def test_keystone_simple(self):
        config_data = keystone_data.DATA
        self.client.setup_config(config_data)
        user_names = [i.name for i in self.client.keystone.users.list()]
        tenant_names = [i.name for i in self.client.keystone.tenants.list()]
        self.assertTrue(config_data[0]['user']['name'] in user_names)
        self.assertTrue(config_data[1]['project']['name'] in tenant_names)

    def test_keystone_update_password(self):
        config_data = keystone_data.DATA
        self.client.setup_config(config_data)

        # make sure updating a password works
        config_data[0]['user']['password'] = 'supernew'
        self.client.setup_config(config_data)

    def test_flavors(self):
        config_data = flavor_data.DATA
        self.client.setup_config(config_data)
        flavor_names = [i.name for i in self.client.nova.flavors.list()]
        self.assertTrue(config_data[0]['flavor']['name'] in flavor_names)

    def test_quotas(self):
        config_data = quota_data.DATA
        self.client.setup_config(config_data)

        # Delete tenant, remove from data, make sure exception thrown
        tenant_id = find_tenant(self.client.keystone,
                                config_data[0]['project']['name'])
        self.client.keystone.tenants.delete(tenant_id)
        config_data.pop(0)
        self.assertRaises(OpenStackAccountError,
                          self.client.setup_config, config_data)

    def test_security_group(self):
        config_data = sec_data.DATA
        self.client.setup_config(config_data)

        # make sure it works without projects as well
        config_data.pop(0)
        self.client.setup_config(config_data)

    def test_keypair(self):
        config_data = keypair_data.DATA
        key = RSA.generate(2048)
        pubkey = key.publickey()
        with open(config_data[0]['keypair']['file'], 'w') as f:
            f.write(pubkey.exportKey('OpenSSH'))
        os.chmod(config_data[0]['keypair']['file'], 0600)
        self.client.setup_config(config_data)
        os.remove(config_data[0]['keypair']['file'])

    def test_neutron(self):
        config_data = neutron_data.DATA
        self.client.setup_config(config_data)

    def test_glance(self):
        config_data = glance_data.DATA
        self.client.setup_config(config_data)

        # check updating images works
        config_data[0]['image']['is_public'] = True
        self.client.setup_config(config_data)

        image = find_image(self.client.glance,
                           config_data[0]['image']['name'])
        self.assertTrue(image.is_public)

    def test_cinder(self):
        config_data = cinder_data.DATA
        self.client.setup_config(config_data)

        volume_names = [i.display_name for i in self.client.cinder.volumes.list()]
        self.assertTrue(config_data[0]['volume']['name'] in volume_names)

    def test_server(self):
        config_data = server_data.DATA
        self.client.setup_config(config_data)
