from openstack_account import settings
from openstack_account import schema
from openstack_account import utils

from openstack_account.openstack import cinder as os_cinder
from openstack_account.openstack import glance as os_glance
from openstack_account.openstack import keystone as os_keystone
from openstack_account.openstack import neutron as os_neutron
from openstack_account.openstack import nova as os_nova

from cinderclient.v1 import client as cinder_v1
from glanceclient import Client as glance_client
from keystoneclient.v2_0 import client as key_v2
from neutronclient.v2_0 import client as neutron_v2
from novaclient.v1_1 import client as nova_v1 #pylint: disable=no-name-in-module

from collections import OrderedDict
from jsonschema import validate
import logging

log = logging.getLogger(__name__)

SECTION_SCHEMA = {
    'user' : 'create_user',
    'project':  'create_project',
    'flavor' : 'create_flavor',
    'nova_quota' : 'set_nova_quota',
    'cinder_quota' : 'set_cinder_quota',
    'security_group' : 'create_security_group',
    'keypair' : 'create_keypair',
    'source_file' : 'create_source_file',
    'image' : 'create_image',
    'network' : 'create_network',
    'subnet' : 'create_subnet',
    'router' : 'create_router',
    'volume' : 'create_volume',
    'server' : 'create_server',
}

class AccountSetup(object): #pylint: disable=too-many-instance-attributes
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
        return os_nova.create_security_group(self.nova, **args)

    def create_keypair(self, **args):
        return os_nova.create_keypair(self.nova, **args)

    def create_source_file(self, **args):
        log.info('Creating source file:%s' % args)
        tenant = utils.find_project(self.keystone,
                                    args.pop('tenant_name', None))
        file_name = args.pop('file', None)
        user = args.pop('user', None)
        stringy = '#!/bin/bash\n'
        stringy += 'export OS_USERNAME="%s"\n' % user
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
        return file_name

    def create_image(self, **args):
        return os_glance.create_image(self.glance, **args)

    def create_network(self, **args):
        return os_neutron.create_network(self.neutron, self.keystone, **args)

    def create_subnet(self, **args):
        return os_neutron.create_subnet(self.neutron, self.keystone, **args)

    def create_router(self, **args):
        return os_neutron.create_router(self.neutron, self.keystone, **args)

    def create_volume(self, **args):
        return os_cinder.create_volume(self.cinder, **args)

    def create_server(self, **args):
        return os_nova.create_server(self.nova, self.neutron, **args)

    def __set_clients(self, username, password, tenant_name, auth_url):
        # Allow for the override of openstack auth args in each action
        # New args will be applied for every section in that action
        username = username or self.os_username
        password = password or self.os_password
        tenant_name = tenant_name or self.os_tenant_name
        auth_url = auth_url or self.os_auth_url
        self.__reset_clients(username, password, tenant_name, auth_url,)

    def import_config(self, config):
        log.debug('Checking schema')
        validate(config, schema.SCHEMA)
        # schema is a list of items
        # .. we'll call these items 'actions'
        return_data = OrderedDict()
        for action in config:
            # for each item reset the openstack clients used
            # .. take either the arguments provided by the user
            # .. or the arguments that are used when authenticating
            # .. the initial client
            self.__set_clients(action.pop('os_username', None),
                               action.pop('os_password', None),
                               action.pop('os_tenant_name', None),
                               action.pop('os_auth_url', None),)
            for key, data in action.iteritems():
                method = getattr(self, SECTION_SCHEMA[key])
                result = method(**data)
                if result:
                    return_data.setdefault(key, [])
                    return_data[key].append(result)
        log.info('Finished with results :%s' % return_data)
        return return_data

    def export_config(self):
        log.info("Gathering data to export")
        export_data = []
        log.info("Gathering keystone data")
        export_data += os_keystone.save_users(self.keystone)
        export_data += os_keystone.save_projects(self.keystone)
        export_data += os_keystone.save_roles(self.keystone)
        export_data += os_nova.save_flavors(self.nova)
        log.info("Saving quota & security group data")
        member_role = utils.find_role(self.keystone, '_member_')
        with utils.temp_user(self.keystone) as (user, user_password):
            for tenant in self.keystone.tenants.list():
                if tenant.name in settings.EXPORT_SKIP_PROJECTS:
                    continue
                export_data += os_nova.save_quotas(self.nova, tenant)
                export_data += os_cinder.save_quotas(self.cinder, tenant)
                # set up temp user to get security groups
                self.keystone.tenants.add_user(tenant.id, user.id, member_role.id)
                nova = nova_v1.Client(user.name, user_password,
                                      tenant.name, self.os_auth_url)
                export_data += os_nova.save_security_groups(nova, tenant)
        return export_data
