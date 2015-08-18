import unittest

from openstack_account.client import AccountSetup
from openstack_account import utils

from tests import settings

class TestExport(unittest.TestCase):
    def setUp(self):
        self.client = AccountSetup(settings.OS_USERNAME,
                                   settings.OS_PASSWORD,
                                   settings.OS_TENANT_NAME,
                                   settings.OS_AUTH_URL,)

    def _get_data(self, item_list, accepted_keys):
        data = []
        for item in item_list:
            add = True
            for key in item:
                if key not in accepted_keys:
                    add = False
                    break
            if add:
                data.append(item)
        return data

    def test_users(self):
        data = self.client.export_config()
        user_data = self._get_data(data, ['user'])
        # create a new temp user
        user_name = utils.random_string(prefix='user-')
        password = utils.random_string()
        user = self.client.keystone.users.create(user_name, password, None)
        new_data = self.client.export_config()
        new_user_data = self._get_data(new_data, ['user'])
        self.assertNotEqual(cmp(user_data, new_user_data), 0)
        self.client.keystone.users.delete(user.id)

    def test_projects(self):
        data = self.client.export_config()
        project_data = self._get_data(data, ['project'])
        # create a new temp project
        project_name = utils.random_string(prefix='project-')
        project = self.client.keystone.tenants.create(project_name)
        new_data = self.client.export_config()
        new_project_data = self._get_data(new_data, ['project'])
        self.assertNotEqual(cmp(project_data, new_project_data), 0)
        self.client.keystone.tenants.delete(project.id)

    def test_roles(self):
        member_role = utils.find_role(self.client.keystone, '_member_')
        data = self.client.export_config()
        project_data = self._get_data(data, ['project'])
        # create a new temp project and uesr
        user_name = utils.random_string(prefix='user-')
        password = utils.random_string()
        tenant_name = utils.random_string(prefix='project-')
        user = self.client.keystone.users.create(user_name, password, None)
        tenant = self.client.keystone.tenants.create(tenant_name)
        self.client.keystone.tenants.add_user(tenant.id, user.id, member_role.id)
        new_data = self.client.export_config()
        new_project_data = self._get_data(new_data, ['project'])
        self.assertNotEqual(cmp(project_data, new_project_data), 0)
        self.client.keystone.tenants.delete(tenant.id)
        self.client.keystone.users.delete(user.id)

    def test_flavors(self):
        data = self.client.export_config()
        flavor_data = self._get_data(data, ['flavor'])
        # create new temporary flavor
        flavor_name = utils.random_string(prefix='flavor-')
        flavor = self.client.nova.flavors.create(flavor_name, 1024, 1, 10)
        new_data = self.client.export_config()
        new_flavor_data = self._get_data(new_data, ['flavor'])
        self.assertNotEqual(cmp(flavor_data, new_flavor_data), 0)
        self.client.nova.flavors.delete(flavor.id)

    def test_nova_quotas(self):
        data = self.client.export_config()
        quota_data = self._get_data(data, ['nova_quota'])
        # change a random quota, make sure it changes
        tenant = self.client.keystone.tenants.list()[0]
        quota = self.client.nova.quotas.get(tenant.id)
        instances = quota.instances
        self.client.nova.quotas.update(tenant.id, instances=instances-1)
        new_data = self.client.export_config()
        new_quota_data = self._get_data(new_data, ['nova_quota'])
        self.assertNotEqual(cmp(quota_data, new_quota_data), 0)
        self.client.nova.quotas.update(tenant.id, instances=instances)

    def test_cinder_quotas(self):
        data = self.client.export_config()
        quota_data = self._get_data(data, ['cinder_quota'])
        # change a random quota, make sure it changes
        tenant = self.client.keystone.tenants.list()[0]
        quota = self.client.cinder.quotas.get(tenant.id)
        volumes = quota.volumes
        self.client.cinder.quotas.update(tenant.id, volumes=volumes-1)
        new_data = self.client.export_config()
        new_quota_data = self._get_data(new_data, ['cinder_quota'])
        self.assertNotEqual(cmp(quota_data, new_quota_data), 0)
        self.client.cinder.quotas.update(tenant.id, volumes=volumes)

    def test_security_groups(self):
        data = self.client.export_config()
        sec_data = self._get_data(data, ['security_group', 'os_tenant_name'])
        # create a new security group
        secname = utils.random_string(prefix='sec-')
        sec = self.client.nova.security_groups.create(secname, "")
        new_data = self.client.export_config()
        new_sec_data = self._get_data(new_data, ['security_group', 'os_tenant_name'])
        self.assertNotEqual(cmp(sec_data, new_sec_data), 0)
        self.client.nova.security_groups.delete(sec.id) #pylint: disable=no-member
