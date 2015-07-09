from openstack_account import schema
from openstack_account import settings
from openstack_account import utils

from openstack_account.openstack import cinder as os_cinder
from openstack_account.openstack import keystone as os_keystone
from openstack_account.openstack import neutron as os_neutron
from openstack_account.openstack import nova as os_nova

from cinderclient.v1 import client as cinder_v1
from glanceclient import Client as glance_client
from keystoneclient.v2_0 import client as key_v2
from neutronclient.v2_0 import client as neutron_v2
from novaclient.v1_1 import client as nova_v1 #pylint: disable=no-name-in-module

from jsonschema import validate
import logging

log = logging.getLogger(__name__)

SECTION_SCHEMA = {
    'users' : 'create_user',
    'projects':  'create_project',
    'flavors' : 'create_flavor',
    'nova_quotas' : 'set_nova_quota',
    'cinder_quotas' : 'set_cinder_quota',
    'security_groups' : 'create_security_group',
    'keypairs' : 'create_keypair',
    'source_files' : 'create_source_file',
    'images' : 'create_image',
    'networks' : 'create_network',
    'subnets' : 'create_subnet',
    'routers' : 'create_router',
    'volumes' : 'create_volume',
    'servers' : 'create_server',
}
SECTION_IGNORE = [
    'os_username',
    'os_password',
    'os_tenant_name',
    'os_auth_url',
]

class AccountSetup(object):
    def __init__(self, username, password, tenant_name, auth_url):
        self.os_username = username
        self.os_password = password
        self.os_tenant_name = tenant_name
        self.os_auth_url = auth_url
        self.keystone = self.nova = self.cinder = self.neutron = self.glance = None
        self.__reset_clients(self.os_username, self.os_password,
                             self.os_tenant_name, self.os_auth_url)

    def __reset_clients(self, username, password, tenant_name, auth_url):
        self.keystone = key_v2.Client(username=username,
                                      password=password,
                                      tenant_name=tenant_name,
                                      auth_url=auth_url)
        self.nova = nova_v1.Client(username,
                                   password,
                                   tenant_name,
                                   auth_url)
        self.cinder = cinder_v1.Client(username,
                                       password,
                                       tenant_name,
                                       auth_url)
        self.neutron = neutron_v2.Client(username=username,
                                         password=password,
                                         tenant_name=tenant_name,
                                         auth_url=auth_url)
        token = self.keystone.auth_token
        image_endpoint = self.keystone.service_catalog.url_for(service_type='image')
        self.glance = glance_client('1', endpoint=image_endpoint, token=token)

    def __find_image(self, glance, name):
        for im in glance.images.list():
            if im.name == name:
                return im
        return None

    def create_user(self, **args):
        return os_keystone.create_user(self.keystone, **args)

    def create_project(self, **args):
        return os_keystone.create_project(self.keystone, **args)

    def create_flavor(self, **args):
        return os_nova.create_flavor(self.nova, **args)

    def set_nova_quota(self, **args):
        return os_nova.set_nova_quota(self.nova, self.keystone, **args)

    def set_cinder_quota(self, **args):
        return os_cinder.set_cinder_quota(self.cinder, self.keystone, **args)

    def create_security_group(self, **args):
        return os_nova.create_security_group(self.nova, self.keystone,
                                             self.os_auth_url, **args)

    def create_keypair(self, **args):
        return os_nova.create_keypair(self.nova, **args)

    def create_source_file(self, **args):
        log.info('Creating source file:%s' % args)
        tenant = os_keystone.find_project(args.pop('tenant_name', None),
                                          self.keystone)
        file_name = args.pop('file', None)
        user = args.pop('user', None)
        stringy = '#!/bin/bash\n'
        stringy += 'export OS_USERNAME="%s"\n' % user
        stringy += 'export OS_TENANT_ID="%s"\n' % tenant.id
        stringy += 'export OS_TENANT_NAME="%s"\n' % tenant.name
        stringy += 'export OS_AUTH_URL="%s"\n' % self.os_auth_url
        stringy += 'echo "Please enter your OpenStack Password:"\n'
        stringy += 'read -s OS_PASSWORD_INPUT\n'
        stringy += 'export OS_PASSWORD=$OS_PASSWORD_INPUT\n'
        try:
            with open(file_name, 'w') as f:
                f.write(stringy)
            log.debug('Created source file:%s' % file_name)
        except IOError:
            log.error('Error creating source file:%s' % file_name)

    def create_image(self, **args):
        log.debug('Creating image:%s' % args)
        wait = args.pop('wait', settings.IMAGE_WAIT)
        timeout = args.pop('timeout', settings.IMAGE_WAIT_TIMEOUT)
        interval = args.pop('wait_interval', settings.IMAGE_WAIT_INTERVAL)
        # By default use glance that already exists
        image_name = args.get('name', None)
        image = self.__find_image(self.glance, image_name)
        if image:
            log.info('Image exists:%s' % image.id)
            return
        file_location = args.pop('file', None)
        image = self.glance.images.create(**args)
        if file_location:
            image.update(data=open(file_location, 'rb'))
        log.info('Created image:%s' % image.id)
        if wait:
            log.info('Waiting for image:%s' % image.id)
            utils.wait_status(self.glance.images.get, image.id, ['active'],
                              ['error'], interval, timeout)

    def create_network(self, **args):
        return os_neutron.create_network(self.neutron, self.keystone, **args)

    def create_subnet(self, **args):
        return os_neutron.create_subnet(self.neutron, self.keystone, **args)

    def create_router(self, **args):
        return os_neutron.create_router(self.neutron, self.keystone, **args)

    def create_volume(self, **args):
        return os_cinder.create_volume(self.cinder, **args)

    def create_server(self, **args):
        return os_nova.create_server(self.nova, **args)

    def __set_clients(self, **config_data):
        # Allow for the override of openstack auth args in each action
        # New args will be applied for every section in that action
        username = config_data.pop('os_username', self.os_username)
        password = config_data.pop('os_password', self.os_password)
        tenant_name = config_data.pop('os_tenant_name', self.os_tenant_name)
        auth_url = config_data.pop('os_auth_url', self.os_auth_url)
        self.__reset_clients(username, password, tenant_name, auth_url)

    def setup_config(self, config):
        log.debug('Checking schema')
        validate(config, schema.SCHEMA)
        for action in config:
            self.__set_clients(**action)
            # For each item listed
            for section in action.keys():
                if section in SECTION_IGNORE:
                    log.debug("Ignoring section:%s" % section)
                    continue
                # Do sections randomly
                for item in action[section]:
                    # For item in section
                    method = getattr(self, SECTION_SCHEMA[section])
                    method(**item)
