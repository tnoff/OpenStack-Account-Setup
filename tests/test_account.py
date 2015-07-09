import unittest

from openstack_account.client import AccountSetup
from openstack_account.exceptions import OpenStackAccountError

from tests import settings
from tests.data import keystone as keystone_data

class TestOSAccount(unittest.TestCase):
    def setUp(self):
        self.client = AccountSetup(settings.OS_USERNAME,
                                   settings.OS_PASSWORD,
                                   settings.OS_TENANT_NAME,
                                   settings.OS_AUTH_URL,)

    def test_keystone(self):
        config_data = keystone_data.DATA
        self.client.setup_config(config_data)
        user_names = [i.name for i in self.client.keystone.users.list()]
        tenant_names = [i.name for i in self.client.keystone.tenants.list()]
        for user in config_data[0]['users']:
            self.assertTrue(user['name'] in user_names)
        for tenant in config_data[0]['projects']:
            self.assertTrue(tenant['name'] in tenant_names)

        # make sure updating a password works
        config_data[0]['users'][0]['password'] = 'supernew'
        self.client.setup_config(config_data)

        # remove role/ then user from project data, make sure exception raised
        role = config_data[0]['projects'][0].pop('role')
        self.assertRaises(OpenStackAccountError,
                          self.client.setup_config, config_data)
        config_data[0]['projects'][0]['role'] = role
        config_data[0]['projects'][0].pop('user')
        self.assertRaises(OpenStackAccountError,
                          self.client.setup_config, config_data)
