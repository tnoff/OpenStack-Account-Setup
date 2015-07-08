from openstack_account import schema
from openstack_account import settings
from openstack_account import utils

from openstack_account.openstack import keystone as os_keystone

from cinderclient.v1 import client as cinder_v1
from glanceclient import Client as glance_client
from keystoneclient.v2_0 import client as key_v2
from neutronclient.v2_0 import client as neutron_v2
from neutronclient.common import exceptions as neutron_exceptions
from novaclient.v1_1 import client as nova_v1 #pylint: disable=no-name-in-module
from novaclient import exceptions as nova_exceptions

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

    def __find_sec_group(self, nova, name):
        for group in nova.security_groups.list():
            if group.name == name:
                return group.id
        return None

    def __find_image(self, glance, name):
        for im in glance.images.list():
            if im.name == name:
                return im
        return None

    def __find_network(self, neutron, name, tenant_id):
        for net in neutron.list_networks()['networks']:
            if net['name'] == name:
                if tenant_id:
                    if tenant_id == net['tenant_id']:
                        return net
                else:
                    return net
        return None

    def __find_subnet(self, neutron, name, tenant_id, network_id):
        for sub in neutron.list_subnets()['subnets']:
            if sub['name'] == name:
                if network_id:
                    if sub['network_id'] == network_id:
                        return sub
                elif tenant_id:
                    if tenant_id == sub['tenant_id']:
                        return sub
                else:
                    return sub
        return None

    def __find_router(self, neutron, name, tenant_id):
        for router in neutron.list_routers()['routers']:
            if router['name'] == name:
                if tenant_id:
                    if tenant_id == router['tenant_id']:
                        return router
                else:
                    return router
        return None

    def __find_volume(self, cinder, name):
        for volume in cinder.volumes.list():
            if volume.name == name:
                return volume
        return None

    def __find_server(self, nova, name):
        for server in nova.servers.list():
            if server.name == name:
                return server
        return None

    def create_user(self, **args):
        return os_keystone.create_user(self.keystone, **args)

    def create_project(self, **args):
        return os_keystone.create_project(self.keystone, **args)

    def create_flavor(self, **args):
        log.info('Creating flavor:%s' % args)
        try:
            self.nova.flavors.create(**args)
        except nova_exceptions.Conflict:
            # Flavor already exists
            log.debug('Flavor already exists')
        except TypeError, e:
            log.error('Cannot create flavor:%s', e)

    def set_nova_quota(self, **args):
        log.info('Setting nova quotas:%s' % args)
        tenant_name = args.pop('tenant_name', None)
        project = os_keystone.find_project(tenant_name, self.keystone)
        if not project:
            log.error('Cannot find project:%s' % tenant_name)
            return
        try:
            self.nova.quotas.update(project.id, **args)
        except nova_exceptions.BadRequest, e:
            log.error('Cannot set quotas:%s' % e)

    def set_cinder_quota(self, **args):
        log.info('Setting cinder quotas:%s' % args)
        project = os_keystone.find_project(args.pop('tenant_name', None),
                                           self.keystone)
        self.cinder.quotas.update(project.id, **args)

    def create_security_group(self, **args):
        log.debug('Creating security group:%s' % args)
        tenant = os_keystone.find_project(args.pop('tenant_name', None),
                                          self.keystone)
        rules = args.pop('rules', None)
        # By default use self.nova
        # If another user returned, use that nova
        nova = self.nova
        with os_keystone.temp_user(tenant, self.keystone) as (user, user_password):
            # If user is None, just use regular nova
            if user:
                nova = nova_v1.Client(user.name,
                                      user_password,
                                      tenant.name,
                                      self.os_auth_url)
            group_id = self.__find_sec_group(nova, args['name'])
            if group_id:
                log.debug('Group already exists:%s' % group_id)
            else:
                try:
                    group = nova.security_groups.create(**args)
                    group_id = group.id # pylint: disable=no-member
                    log.debug('Created security group:%s' % group_id)
                except nova_exceptions.BadRequest:
                    # Group already exists
                    group_id = self.__find_sec_group(nova, args.pop('name', None))
                    log.debug('Group already exists:%s' % group_id)
                except nova_exceptions.ClientException, e:
                    log.error('Cannot create security group:%s' % e)
                    return
            for rule in rules:
                try:
                    r = nova.security_group_rules.create(group_id, **rule)
                except nova_exceptions.BadRequest:
                    log.debug('Cannot create rule, already exists')
                    continue
                except nova_exceptions.CommandError, e:
                    log.error('Cannot create rule:%s' % e)
                    continue
                log.info('Created security group rule:%s' % r)

    def create_keypair(self, **args):
        log.info('Creating keypair:%s' % args)
        nova = self.nova
        if args['file']:
            with open(args.pop('file'), 'r') as f:
                args['public_key'] = f.read()
        try:
            nova.keypairs.create(**args)
            log.debug('Created keypair:%s' % args['name'])
        except nova_exceptions.Conflict:
            log.debug('Keypair already exists')

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
        log.debug('Creating network:%s' % args)
        tenant = os_keystone.find_project(args.pop('tenant_name', None),
                                          self.keystone)
        net = self.__find_network(self.neutron, args['name'], tenant.id)
        if net:
            log.info('Network already exists:%s' % net['id'])
            return
        if tenant:
            args['tenant_id'] = tenant.id
        network = self.neutron.create_network({'network' : args})
        log.info('Created network:%s' % network['network']['id'])

    def create_subnet(self, **args):
        log.debug('Creating subnet:%s' % args)
        tenant = os_keystone.find_project(args.pop('tenant_name', None),
                                          self.keystone)
        network = self.__find_network(self.neutron, args.pop('network', None),
                                      tenant.id)
        args['network_id'] = network['id']
        sub = self.__find_subnet(self.neutron, args['name'], tenant.id,
                                 network['id'])
        if sub:
            log.info('Subnet already exists:%s' % sub['id'])
            return
        if tenant:
            args['tenant_id'] = tenant.id
        try:
            subnet = self.neutron.create_subnet({"subnet" : args})
        except neutron_exceptions.BadRequest, e:
            log.error('Cannot create subnet:%s' % str(e))
            return
        log.info('Created subnet:%s' % subnet['subnet']['id'])

    def create_router(self, **args):
        log.debug('Create router:%s' % args)
        tenant = os_keystone.find_project(args.pop('tenant_name', None),
                                          self.keystone)
        if tenant:
            args['tenant_id'] = tenant.id
        router = self.__find_router(self.neutron, args['name'], None)
        external = self.__find_network(self.neutron,
                                       args.pop('external_network', None),
                                       None)
        internal = self.__find_subnet(self.neutron,
                                      args.pop('internal_subnet', None),
                                      None, None)
        if router:
            log.info('Router already exists:%s' % router['id'])
        else:
            router = self.neutron.create_router({'router' : args})['router']
            log.info('Created router:%s' % router['id'])

        if external:
            data = {'network_id' : external['id']}
            self.neutron.add_gateway_router(router['id'],
                                            data)
            log.info('Set external network:%s for router:%s' % (external['id'],
                                                                router['id']))
        if internal:
            data = {'subnet_id' : internal['id']}
            try:
                self.neutron.add_interface_router(router['id'], data)
                log.info('Set internal subnet:%s for router:%s' % (internal['id'],
                                                                   router['id']))
            except neutron_exceptions.BadRequest, e:
                log.error('Cannot add internal subnet:%s' % str(e))

    def create_volume(self, **args):
        log.debug('Create volume:%s' % args)
        name = args.pop('name', None)
        wait = args.pop('wait', settings.VOLUME_WAIT)
        timeout = args.pop('timeout', settings.VOLUME_WAIT_TIMEOUT)
        interval = args.pop('interval', settings.VOLUME_WAIT_INTERVAL)
        volume = self.__find_volume(self.cinder, name)
        # Cinder uses 'display name' because fuck convention i suppose
        args['display_name'] = name
        if volume:
            log.info('Volume already exists:%s' % volume.id)
        else:
            volume = self.cinder.volumes.create(**args)
            log.info('Volume created:%s' % volume.id)
        if wait:
            log.info('Waiting for volume:%s' % volume.id)
            utils.wait_status(self.cinder.volumes.get, volume.id,
                              ['available'], ['error'], interval, timeout)

    def create_server(self, **args):
        log.debug('Create server:%s' % args)
        name = args.get('name')
        wait = args.pop('wait', settings.SERVER_WAIT)
        timeout = args.pop('timeout', settings.SERVER_WAIT_TIMEOUT)
        interval = args.pop('interval', settings.SERVER_WAIT_INTERVAL)
        server = self.__find_server(self.nova, name)
        flavor_name = args.pop('flavor_name', None)
        if flavor_name:
            args['flavor'] = self.__find_flavor(self.nova, flavor_name)
        image_name = args.pop('image_name', None)
        if image_name:
            args['image'] = self.__find_image(self.glance, image_name)
        # Check for and build server
        server = self.__find_server(self.nova, name)
        if server:
            log.info('Server already exists:%s' % server.id)
        else:
            server = self.nova.servers.create(**args)
            log.info('Server created:%s' % server.id)
        if wait:
            log.info("Waiting for server:%s" % server.id)
            utils.wait_status(self.nova.servers.get, server.id,
                              ['ACTIVE'], ['ERROR'], interval, timeout)

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
