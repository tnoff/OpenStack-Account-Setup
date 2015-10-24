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

SECTION_KEYS = SECTION_SCHEMA.keys() + ['os_tenant_name']

class AccountSetupResults(list):
    '''Custom Account Client Results'''
    def __add__(self, new_item):
        assert isinstance(new_item, list), 'add type must be list'
        for item in new_item:
            self.append(item)

    def append(self, new_item):
        assert isinstance(new_item, dict), 'must append dict type'
        for key in new_item.keys():
            assert key in SECTION_KEYS, 'key:%s must in section keys' % key
        super(AccountSetupResults, self).append(new_item)

    def sort_by_keys(self):
        '''Sort item keys into dict'''
        my_list = list(self)
        return_data = {}
        for item in my_list:
            for key in item:
                if key == 'os_tenant_name':
                    continue
                return_data.setdefault(key, [])
                return_data[key].append(item)
        return return_data


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
        return {'source_file' : file_name}

    def create_image(self, **args):
        return os_glance.create_image(self.glance, **args)

    def create_network(self, **args):
        return os_neutron.create_network(self.neutron, self.keystone, **args)

    def create_subnet(self, **args):
        return os_neutron.create_subnet(self.neutron, self.keystone, **args)

    def create_router(self, **args):
        return os_neutron.create_router(self.neutron, self.keystone, **args)

    def create_volume(self, **args):
        return os_cinder.create_volume(self.cinder, self.nova, **args)

    def create_server(self, **args):
        return os_nova.create_server(self.nova, self.neutron, self.cinder, **args)

    def __set_client_auth(self, username, password, tenant_name, auth_url):
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
        return_data = AccountSetupResults()
        for action in config:
            # for each item reset the openstack clients used
            # .. take either the arguments provided by the user
            # .. or the arguments that are used when authenticating
            # .. the initial client
            self.__set_client_auth(action.pop('os_username', None),
                                   action.pop('os_password', None),
                                   action.pop('os_tenant_name', None),
                                   action.pop('os_auth_url', None),)
            for key, data in action.iteritems():
                method = getattr(self, SECTION_SCHEMA[key])
                result = method(**data)
                if result:
                    return_data.append(result)
        log.info('Finished with results :%s' % return_data)
        return return_data

    def export_config(self):
        log.info("Gathering data to export")
        export_data = AccountSetupResults()
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
                export_data += [os_nova.save_quotas(self.nova, tenant)]
                export_data += [os_cinder.save_quotas(self.cinder, tenant)]
                # set up temp user to get security groups
                self.keystone.tenants.add_user(tenant.id, user.id, member_role.id)
                nova = nova_v1.Client(user.name, user_password,
                                      tenant.name, self.os_auth_url)
                export_data += os_nova.save_security_groups(nova, tenant)
        return export_data

    def export_images(self, save_directory):
        if save_directory:
            save_directory = utils.check_directory(save_directory)
        log.info("Gathering image data and/or metadata")
        export_data = AccountSetupResults()
        # the glance client will not list all images for some reason, use nova
        for image in self.nova.images.list():
            export_data += [os_glance.save_image_meta(self.glance, self.keystone,
                                                      image)]
            if save_directory:
                # TODO this should probably verify with checksums
                # TODO once checksum is done, should check if image exists
                # .. already
                os_glance.save_image_data(self.glance, image, save_directory)
        return export_data
