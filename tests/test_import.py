from Crypto.PublicKey import RSA
import os
import time
import unittest

from openstack_account.client import AccountSetup
from openstack_account.exceptions import OpenStackAccountError
from openstack_account import utils

from tests import settings

class TestImport(unittest.TestCase):
    def setUp(self):
        self.client = AccountSetup(settings.OS_USERNAME,
                                   settings.OS_PASSWORD,
                                   settings.OS_TENANT_NAME,
                                   settings.OS_AUTH_URL,)

    def __delete_router(self, router_id):
        # find any interfaces on a router and delete
        self.client.neutron.remove_gateway_router(router_id)
        for port in self.client.neutron.list_ports()['ports']:
            if port['device_id'] == router_id:
                data = {'subnet_id' : port['fixed_ips'][0]['subnet_id']}
                self.client.neutron.remove_interface_router(router_id, data)
        self.client.neutron.delete_router(router_id)

    def __next_cidr(self):
        subnet_list = self.client.neutron.list_subnets()['subnets']
        cidr = '192.168.0.0/24'
        current_cidr = [i['cidr'] for i in subnet_list]
        while cidr in current_cidr:
            temp_int = cidr.split('.')[2]
            cidr = '192.168.%d.0/24' % (int(temp_int) + 1)
        return cidr

    def __wait_deletion(self, list_function, obj_id, timeout=3600, interval=5): #pylint:disable=no-self-use
        stop = time.time() + timeout
        while True:
            obj_list = list_function()
            if obj_id not in [i.id for i in obj_list]:
                return True
            time.sleep(interval)
            if time >= stop:
                return False

    def __cleanup(self, results): #pylint: disable=too-many-branches, too-many-locals
        # reverse order of ordered dict for deletion
        deletion_order = ['server', 'volume', 'image', 'router', 'subnet',
                          'network', 'keypair', 'security_group',
                          'flavor', 'user', 'project']
        for key in deletion_order:
            try:
                if key == 'project':
                    for tenant in results[key]:
                        self.client.keystone.tenants.delete(tenant)
                elif key == 'user':
                    for user in results[key]:
                        self.client.keystone.users.delete(user)
                elif key == 'flavor':
                    for flavor in results[key]:
                        self.client.nova.flavors.delete(flavor)
                elif key == 'security_group':
                    for sec in results[key]:
                        self.client.nova.security_groups.delete(sec)
                elif key == 'keypair':
                    for keypair in results[key]:
                        self.client.nova.keypairs.delete(keypair)
                elif key == 'image':
                    for image in results[key]:
                        self.client.glance.images.delete(image)
                elif key == 'volume':
                    for volume in results[key]:
                        self.client.cinder.volumes.delete(volume)
                elif key == 'server':
                    for server in results[key]:
                        self.client.nova.servers.delete(server)
                        self.__wait_deletion(self.client.nova.servers.list,
                                             server)
                elif key == 'router':
                    for router in results[key]:
                        self.__delete_router(router)
                elif key == 'subnet':
                    for subnet in results[key]:
                        self.client.neutron.delete_subnet(subnet)
                elif key == 'network':
                    for network in results[key]:
                        self.client.neutron.delete_network(network)
            except KeyError:
                continue

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
        self.client.import_config(keystone_data)
        user_names = [i.name for i in self.client.keystone.users.list()]
        tenant_names = [i.name for i in self.client.keystone.tenants.list()]
        self.assertTrue(user_name in user_names)
        self.assertTrue(project_name in tenant_names)

        # make sure updating a password works
        keystone_data[0]['user']['password'] = utils.random_string(prefix='new')
        results = self.client.import_config(keystone_data)

        self.__cleanup(results)

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
        results = self.client.import_config(flavor_data)
        flavor_names = [i.name for i in self.client.nova.flavors.list()]
        self.assertTrue(flavor_name in flavor_names)
        self.__cleanup(results)

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

        results = self.client.import_config(quota_data)

        tenant_id = results['project'][0]
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
        results = self.client.import_config(sec_data)
        sec_names = [i.name for i in self.client.nova.security_groups.list()]
        self.assertTrue(secgroup_name in sec_names)
        self.__cleanup(results)

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
        key = RSA.generate(2048)
        pubkey = key.publickey()
        with open(filename, 'w') as f:
            f.write(pubkey.exportKey('OpenSSH'))
        os.chmod(filename, 0600)
        results = self.client.import_config(keypair_data)
        keypairs = [i.name for i in self.client.nova.keypairs.list()]
        self.assertTrue(keyname in keypairs)
        os.remove(filename)
        self.__cleanup(results)

    def test_neutron(self):
        project_name = utils.random_string()
        network_name = utils.random_string()
        subnet_name = utils.random_string()
        router_name = utils.random_string()
        cidr = self.__next_cidr()
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
        results = self.client.import_config(neutron_data)
        networks = [i['name']
                    for i in self.client.neutron.list_networks()['networks']]
        subnets = [i['name']
                   for i in self.client.neutron.list_subnets()['subnets']]
        routers = [i['name']
                   for i in self.client.neutron.list_routers()['routers']]
        self.assertTrue(network_name in networks)
        self.assertTrue(subnet_name in subnets)
        self.assertTrue(router_name in routers)

        self.__cleanup(results)

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
        results = self.client.import_config(glance_data)

        # check updating images works
        glance_data[0]['image']['is_public'] = True
        self.client.import_config(glance_data)

        image = self.client.glance.images.get(results['image'][0])
        self.assertTrue(image.is_public)
        self.__cleanup(results)

    def test_cinder(self):
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
        results = self.client.import_config(cinder_data)

        volume_names = [i.display_name for i in self.client.cinder.volumes.list()]
        self.assertTrue(volume_name in volume_names)
        self.__cleanup(results)

    def test_server(self):
        image_name = utils.random_string()
        image_url = "http://cloudhyd.com/openstack/images/cirros-0.3.0-x86_64-disk.img"
        network_name = utils.random_string()
        subnet_name = utils.random_string()
        flavor_name = utils.random_string()
        server_name = utils.random_string()
        cidr = self.__next_cidr()
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
        results = self.client.import_config(server_data)
        servers = [i.name for i in self.client.nova.servers.list()]
        self.assertTrue(server_name in servers)
        self.__cleanup(results)
