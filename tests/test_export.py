from openstack_portation import utils

from tests import utils as test_utils

class TestExport(test_utils.TestClient):
    def test_users(self):
        # Get current user data, create new user and ensure is different
        keystone_data = [
            {
                'user' : {
                    'password' : utils.random_string(),
                    'name' : utils.random_string(prefix='user-'),
                    'email' : None,
                },
            },
        ]
        original_data = self.client.export_config().\
                            sort_by_keys()['user']
        self.results = self.client.import_config(keystone_data)
        new_data = self.client.export_config().\
                            sort_by_keys()['user']
        self.assertNotEqual(cmp(original_data, new_data), 0)

    def test_projects(self):
        # Get current project data, create new project and ensure is different
        keystone_data = [
            {
                'project' : {
                    'description' : utils.random_string(),
                    'role' : 'admin',
                    'name' : utils.random_string(prefix='project-'),
                },
            }
        ]
        original_data = self.client.export_config().\
                            sort_by_keys()['project']

        self.results = self.client.import_config(keystone_data)
        new_data = self.client.export_config().\
                        sort_by_keys()['project']

        self.assertNotEqual(cmp(original_data, new_data), 0)

    def test_roles(self):
        user_name = utils.random_string(prefix='user-')
        keystone_data = [
            {
                'user' : {
                    'password' : utils.random_string(),
                    'name' : user_name,
                    'email' : None,
                },
            },
            {
                'project' : {
                    'description' : utils.random_string(),
                    'role' : 'admin',
                    'user' : user_name,
                    'name' : utils.random_string(prefix='project-'),
                },
            },
        ]
        original_data = self.client.export_config().\
                            sort_by_keys()['project']

        self.results = self.client.import_config(keystone_data)
        new_data = self.client.export_config().\
                        sort_by_keys()['project']

        self.assertNotEqual(cmp(original_data, new_data), 0)

    def test_flavors(self):
        flavor_data = [
            {
                'flavor' : {
                    'ram' : 512,
                    'disk' : 0,
                    'vcpus' : 2,
                    'name' : utils.random_string(prefix='flavor-')
                },
            },
        ]
        original_data = self.client.export_config().\
                            sort_by_keys()['flavor']

        self.results = self.client.import_config(flavor_data)
        new_data = self.client.export_config().\
                        sort_by_keys()['flavor']

        self.assertNotEqual(cmp(original_data, new_data), 0)

    def test_nova_quotas(self):
        tenant_name = utils.random_string(prefix='project-')
        tenant_data = [
            {
                'project' : {
                    'name' : tenant_name,
                    'description' : utils.random_string(),
                },
            },
        ]
        self.client.import_config(tenant_data)
        tenant = utils.find_project(self.client.keystone, tenant_name)
        old_quota = self.client.nova.quotas.get(tenant.id)

        original_data = self.client.export_config().\
                            sort_by_keys()['nova_quota']
        quota_data = tenant_data + [
            {
                'nova_quota' : {
                    'tenant_name' : tenant_name,
                    'instances' : old_quota.instances + 9999999999,
                },
            },
        ]
        self.results = self.client.import_config(quota_data)
        new_data = self.client.export_config().\
                        sort_by_keys()['nova_quota']
        self.assertNotEqual(cmp(original_data, new_data), 0)

    def test_cinder_quotas(self):
        tenant_name = utils.random_string(prefix='project-')
        tenant_data = [
            {
                'project' : {
                    'name' : tenant_name,
                    'description' : utils.random_string(),
                },
            },
        ]
        self.client.import_config(tenant_data)
        tenant = utils.find_project(self.client.keystone, tenant_name)
        old_quota = self.client.cinder.quotas.get(tenant.id)
        original_data = self.client.export_config().\
                            sort_by_keys()['cinder_quota']
        quota_data = tenant_data + [
            {
                'cinder_quota' : {
                    'tenant_name' : tenant_name,
                    'volumes' : old_quota.volumes + 9999999999,
                },
            },
        ]
        self.results = self.client.import_config(quota_data)
        new_data = self.client.export_config().\
                        sort_by_keys()['cinder_quota']
        self.assertNotEqual(cmp(original_data, new_data), 0)


    def test_security_groups(self):
        security_group_data = [
            {
                'security_group' : {
                    'rules' : [
                        {
                            'to_port': 22,
                            'cidr' : '0.0.0.0/0',
                            'from_port': 22,
                            'ip_protocol' : 'tcp'
                        },
                    ],
                    'name' : utils.random_string(prefix='sec-'),
                    'description' : utils.random_string(),
                },
            },
        ]
        original_data = self.client.export_config().\
                            sort_by_keys()['security_group']
        self.results = self.client.import_config(security_group_data)
        new_data = self.client.export_config().\
                        sort_by_keys()['security_group']
        self.assertNotEqual(cmp(original_data, new_data), 0)

    def test_images(self):
        image_url = "http://cloudhyd.com/openstack/images/cirros-0.3.0-x86_64-disk.img"
        image_data = [
            {
                "image": {
                    "name": utils.random_string(prefix='image-'),
                    "container_format": "bare",
                    "disk_format": "qcow2",
                    "copy_from": image_url,
                    "is_public": False,
                    "wait": True,
                }
            },
        ]
        original_data = self.client.export_images(None).\
                            sort_by_keys()['image']
        self.results = self.client.import_config(image_data)
        new_data = self.client.export_images(None).\
                         sort_by_keys()['image']
        self.assertNotEqual(cmp(original_data, new_data), 0)
