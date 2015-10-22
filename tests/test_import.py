from openstack_account.exceptions import OpenStackAccountError
from openstack_account import utils

from tests import utils as test_utils

class TestImport(test_utils.TestClient):
    # teardown will take care of deleting created resources
    # assume that if they can be deleted, they were created correctly
    # utils code will catch resources in error

    def test_keystone(self):
        user_name = utils.random_string()
        project_name = utils.random_string()
        keystone_data = [
            {
                'user' : {
                    'password' : utils.random_string(prefix='old'),
                    'name' : user_name,
                    'email' : None,

                },
            },
            {
                'project' : {
                    'description' : utils.random_string(),
                    'role' : 'admin',
                    'user' : user_name,
                    'name' : project_name,
                },
            }
        ]
        self.results = self.client.import_config(keystone_data)

    def test_keystone_password_update(self):
        user_name = utils.random_string()
        keystone_data = [
            {
                'user' : {
                    'password' : utils.random_string(prefix='old'),
                    'name' : user_name,
                    'email' : None,

                },
            },
        ]
        self.client.import_config(keystone_data)
        keystone_data[0]['user']['password'] = utils.random_string(prefix='new')
        self.results = self.client.import_config(keystone_data)

    def test_flavors(self):
        flavor_name = utils.random_string()
        flavor_data = [
            {
                'flavor' : {
                    'vcpus' : 4,
                    'disk' : 0,
                    'ram' : 4096,
                    'name' : flavor_name,
                }
            },
        ]
        self.results = self.client.import_config(flavor_data)

    def test_quotas(self):
        project_name = utils.random_string()
        quota_data = [
            {
                'project' : {
                    'name' : project_name,
                }
            },
            {
                'nova_quota' : {
                    "cores": 80,
                    "ram": 5120000,
                    "instances": 20,
                    "tenant_name": project_name,
                },
                "cinder_quota": {
                    "gigabytes": 1000000,
                    "tenant_name": project_name,
                    "volumes": 20
                },
            },
        ]

        self.results = self.client.import_config(quota_data)

    def test_quotas_assert_tenant(self):
        project_name = utils.random_string()
        quota_data = [
            {
                'project' : {
                    'name' : project_name,
                }
            },
            {
                'nova_quota' : {
                    "cores": 80,
                    "ram": 5120000,
                    "instances": 20,
                    "tenant_name": project_name,
                },
                "cinder_quota": {
                    "gigabytes": 1000000,
                    "tenant_name": project_name,
                    "volumes": 20
                },
            },
        ]

        results = self.client.import_config(quota_data)
        tenant_id = results[0]['project']
        # Delete tenant, remove from data, make sure exception thrown
        self.client.keystone.tenants.delete(tenant_id)
        quota_data.pop(0)
        self.assertRaises(OpenStackAccountError,
                          self.client.import_config, quota_data)

    def test_security_group(self):
        secgroup_name = utils.random_string()
        sec_data = [
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
                    'name' : secgroup_name,
                    'description' : utils.random_string(),
                },
            },
        ]
        self.results = self.client.import_config(sec_data)

    def test_keypair(self):
        keyname = utils.random_string()
        filename = utils.random_string(prefix='/tmp/')
        keypair_data = [
            {
                'keypair' : {
                    'name' : keyname,
                    'file' : filename,
                },
            },
        ]
        with test_utils.temp_keypair(filename) as _:
            self.results = self.client.import_config(keypair_data)

    def test_neutron(self):
        project_name = utils.random_string()
        network_name = utils.random_string()
        subnet_name = utils.random_string()
        router_name = utils.random_string()
        cidr = '192.168.0.0/24'
        neutron_data = [
            {
                "project": {
                    "name": project_name,
                }
            },
            {
                "network": {
                    "tenant_name": project_name,
                    "name": network_name,
                    "shared": True,
                }
            },
            {
                "subnet": {
                    "ip_version": "4",
                    "tenant_name": project_name,
                    "cidr": cidr,
                    "name": subnet_name,
                    "network": network_name,
                }
            },
            {
                "router": {
                    "tenant_name": project_name,
                    "external_network": "external",
                    "name": router_name,
                    "internal_subnet": subnet_name,
                }
            },
        ]
        self.results = self.client.import_config(neutron_data)

    def test_glance(self):
        image_name = utils.random_string()
        image_url = "http://cloudhyd.com/openstack/images/cirros-0.3.0-x86_64-disk.img"
        glance_data = [
            {
                "image": {
                    "name": image_name,
                    "container_format": "bare",
                    "disk_format": "qcow2",
                    "copy_from": image_url,
                    "is_public": False,
                    "wait": True,
                }
            },
        ]
        self.results = self.client.import_config(glance_data)

    def test_glance_update_image(self):
        image_name = utils.random_string()
        image_url = "http://cloudhyd.com/openstack/images/cirros-0.3.0-x86_64-disk.img"
        glance_data = [
            {
                "image": {
                    "name": image_name,
                    "container_format": "bare",
                    "disk_format": "qcow2",
                    "copy_from": image_url,
                    "is_public": False,
                    "wait": True,
                }
            },
        ]
        self.client.import_config(glance_data)
        glance_data[0]['image']['is_public'] = True
        self.results = self.client.import_config(glance_data)

        image = self.client.glance.images.get(self.results[0]['image'])
        self.assertTrue(image.is_public)

    def test_volume(self):
        volume_name = utils.random_string()
        cinder_data = [
            {
                "volume": {
                    "size": 5,
                    "name": volume_name,
                    "timeout": 3600,
                    "wait": True,
                }
            }
        ]
        self.results = self.client.import_config(cinder_data)

    def test_volume_with_image(self):
        # make sure can boot volume from image
        volume_name = utils.random_string()
        image_name = utils.random_string()
        image_url = "http://cloudhyd.com/openstack/images/cirros-0.3.0-x86_64-disk.img"
        cinder_data = [
            {
                "image": {
                    "name": image_name,
                    "container_format": "bare",
                    "disk_format": "qcow2",
                    "copy_from": image_url,
                    "is_public": False,
                    "wait": True,
                }
            },
            {
                "volume": {
                    "size": 5,
                    "name": volume_name,
                    "timeout": 3600,
                    "wait": True,
                    "image_name": image_name,
                }
            },
        ]
        self.results = self.client.import_config(cinder_data)

    def test_server(self):
        image_name = utils.random_string()
        image_url = "http://cloudhyd.com/openstack/images/cirros-0.3.0-x86_64-disk.img"
        network_name = utils.random_string()
        subnet_name = utils.random_string()
        flavor_name = utils.random_string()
        server_name = utils.random_string()
        cidr = '192.168.0.0/24'
        server_data = [
            {
                "network": {
                    "name": network_name,
                }
            },
            {
                "subnet": {
                    "ip_version": "4",
                    "cidr": cidr,
                    "name": subnet_name,
                    "network": network_name,
                }
            },
            {
                "image": {
                    "name": image_name,
                    "container_format": "bare",
                    "disk_format": "qcow2",
                    "copy_from": image_url,
                    "is_public": False,
                    "wait": True,
                }
            },
            {
                "flavor": {
                    "vcpus": 4,
                    "disk": 0,
                    "ram": 4096,
                    "name": flavor_name,
                }
            },
            {
                "server": {
                    "flavor_name": flavor_name,
                    "timeout": 1200,
                    "image_name": image_name,
                    "name": server_name,
                    "wait": True,
                    "nics": [{
                        "network_name": network_name,
                    }]
                }
            }
        ]
        self.results = self.client.import_config(server_data)

    def test_server_boot_volume(self):
        image_name = utils.random_string()
        image_url = "http://cloudhyd.com/openstack/images/cirros-0.3.0-x86_64-disk.img"
        network_name = utils.random_string()
        subnet_name = utils.random_string()
        flavor_name = utils.random_string()
        server_name = utils.random_string()
        volume_name = utils.random_string()
        cidr = '192.168.0.0/24'
        server_data = [
            {
                "network": {
                    "name": network_name,
                }
            },
            {
                "subnet": {
                    "ip_version": "4",
                    "cidr": cidr,
                    "name": subnet_name,
                    "network": network_name,
                }
            },
            {
                "image": {
                    "name": image_name,
                    "container_format": "bare",
                    "disk_format": "qcow2",
                    "copy_from": image_url,
                    "is_public": False,
                    "wait": True,
                }
            },
            {
                "flavor": {
                    "vcpus": 4,
                    "disk": 0,
                    "ram": 4096,
                    "name": flavor_name,
                }
            },
            {
                "volume": {
                    "name" : volume_name,
                    "size" : 5,
                    "image_name": image_name,
                    "wait" : True,
                }
            },
            {
                "server": {
                    "flavor_name": flavor_name,
                    "timeout": 1200,
                    "image_name": image_name,
                    "name": server_name,
                    "wait": True,
                    "nics": [{
                        "network_name": network_name,
                    }],
                    "volumes" : [
                        {
                            "volume_name" : volume_name,
                            "device_name" : "vda",
                        },
                    ],
                }
            }
        ]
        self.results = self.client.import_config(server_data)
