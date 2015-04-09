from openstack_account import schema

from cinderclient.v1 import client as cinder_v1
from glanceclient import Client as glance_client
from keystoneclient.v2_0 import client as key_v2
from keystoneclient.openstack.common.apiclient import exceptions as keystone_exceptions
from neutronclient.v2_0 import client as neutron_v2
from neutronclient.common import exceptions as neutron_exceptions
from novaclient.v1_1 import client as nova_v1
from novaclient import exceptions as nova_exceptions

from contextlib import contextmanager
from jsonschema import validate
import logging
import random
import string
import time

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
}

WAIT_INTERVAL = 5
WAIT_TIMEOUT = 3600

class AccountSetup(object):
    def __init__(self, username, password, tenant_name, auth_url):
        log.debug('Creating Account Setup Object')
        self.os_username = username
        self.os_password = password
        self.os_tenant_name = tenant_name
        self.os_auth_url = auth_url

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


    def __random_string(self, prefix='', length=20):
        chars = string.ascii_lowercase + string.digits
        s = ''.join(random.choice(chars) for _ in range(length))
        return prefix + s

    def __wait_status(self, function, obj_id, accept_states, reject_states,
                      interval, timeout):
        interval = interval or WAIT_INTERVAL
        timeout = timeout or WAIT_TIMEOUT
        obj = function(obj_id)
        expires = time.time() + timeout
        while time.time() <= expires:
            if obj.status in accept_states:
                return True
            if obj.status in reject_states:
                return False
            time.sleep(interval)
            obj = function(obj_id)
        return False

    @contextmanager
    def __temp_user(self, tenant):
        # Create temp user that is authorized to tenant
        log.debug('Creating temp user for tenant:%s' % tenant.id)
        username = self.__random_string(prefix='user-')
        password = self.__random_string(length=30)
        user = self.keystone.users.create(name=username,
                                          password=password,
                                          email=None)
        log.debug('Created temp user:%s for tenant:%s' % (user.id, tenant.id))
        member_role = self.__find_role('member')
        tenant.add_user(user.id, member_role.id)
        try:
            yield user, password
        finally:
            log.debug('Deleting temp user:%s' % user.id)
            self.keystone.users.delete(user.id)

    def __find_user(self, name):
        for user in self.keystone.users.list():
            if user.name == name:
                return user
        return None

    def __find_role(self, name):
        if not name:
            return None
        for role in self.keystone.roles.list():
            if name.lower() in role.name.lower():
                return role
        return None

    def __find_project(self, name):
        for tenant in self.keystone.tenants.list():
            if tenant.name == name:
                return tenant
        return None

    def __find_sec_group(self, nova, name):
        for group in nova.security_groups.list():
            if group.name == name:
                return group.id
        return None

    def __find_valid_project(self, user):
        if not user:
            return None
        for tenant in self.keystone.tenants.list():
            user_roles = self.keystone.users.list_roles(user.id,
                                                        tenant=tenant.id)
            for _ in user_roles:
                return tenant
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

    def create_user(self, **args):
        log.debug('Creating user:%s' % args)
        try:
            user = self.keystone.users.create(**args)
        except keystone_exceptions.Conflict:
            # User allready exists
            user = self.__find_user(args['name'])
        log.info('User created:%s' % user)
        return user

    def create_project(self, **args):
        log.debug('Creating project:%s' % args)
        role = self.__find_role(args.pop('role', None))
        args['tenant_name'] = args.pop('name', None)
        user = self.__find_user(args.pop('user', None))

        try:
            project = self.keystone.tenants.create(**args)
        except keystone_exceptions.Conflict:
            project = self.__find_project(args['tenant_name'] or None)
        if user and role:
            try:
                project.add_user(user.id, role.id)
                log.debug('Added user:%s to project:%s with role:%s' %
                          (user.id, project.id, role.id))
            except keystone_exceptions.Conflict:
                # Role already exists
                log.debug('Role exits user:%s to project:%s with role:%s' %
                          (user.id, project.id, role.id))
        log.info('Project created:%s' % project.id)

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
        project = self.__find_project(tenant_name)
        if not project:
            log.error('Cannot find project:%s' % tenant_name)
            return
        try:
            self.nova.quotas.update(project.id, **args)
        except nova_exceptions.BadRequest, e:
            log.error('Cannot set quotas:%s' % e)

    def set_cinder_quota(self, **args):
        log.info('Setting cinder quotas:%s' % args)
        project = self.__find_project(args.pop('tenant_name', None))
        self.cinder.quotas.update(project.id, **args)

    def create_security_group(self, **args):
        log.debug('Creating security group:%s' % args)
        tenant = self.__find_project(args.pop('tenant_name', None))
        rules = args.pop('rules', None)
        with self.__temp_user(tenant) as (user, user_password):
            nova = nova_v1.Client(user.name,
                                  user_password,
                                  tenant.name,
                                  self.os_auth_url)
            try:
                group = nova.security_groups.create(**args)
                group_id = group.id # pylint: disable=no-member
            except nova_exceptions.BadRequest:
                # Group already exists
                group_id = self.__find_sec_group(nova, args.pop('name', None))
            except nova_exceptions.ClientException, e:
                log.error('Cannot create security group:%s' % e)
                return
            log.info("Created security group:%s" % group_id)
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
        user = self.__find_user(args.pop('user', None))
        tenant = self.__find_valid_project(user)
        nova = self.nova
        if user:
            nova = nova_v1.Client(user['name'],
                                  user['password'],
                                  tenant.name,
                                  self.os_auth_url)
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
        tenant = self.__find_project(args.pop('tenant_name', None))
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
        with open(file_name, 'w') as f:
            f.write(stringy)
        log.debug('Created source file:%s' % file_name)

    def create_image(self, **args):
        log.debug('Creating image:%s' % args)
        tenant = self.__find_project(args.pop('tenant_name', None))
        wait = args.pop('wait', None)
        timeout = args.pop('timeout', None)
        interval = args.pop('wait_interval', None)
        with self.__temp_user(tenant) as (user, user_password):
            keystone = key_v2.Client(username=user.name,
                                     password=user_password,
                                     tenant_name=tenant.name,
                                     auth_url=self.os_auth_url)
            token = keystone.auth_token
            image_endpoint = keystone.service_catalog.url_for(service_type='image')
            glance = glance_client('1', endpoint=image_endpoint, token=token)
            image_name = args.get('name', None)
            image = self.__find_image(glance, image_name)
            if image:
                log.info('Image exists:%s' % image.id)
                return
            file_location = args.pop('file', None)
            image = glance.images.create(**args)
            if file_location:
                image.update(data=open(file_location, 'rb'))
            log.info('Created image:%s' % image.id)
            if wait:
                log.info('Waiting for image:%s' % image.id)
                self.__wait_status(glance.images.get, image.id, ['active'],
                                   ['error'], interval, timeout)

    def create_network(self, **args):
        log.debug('Creating network:%s' % args)
        tenant = self.__find_project(args.pop('tenant_name', None))
        net = self.__find_network(self.neutron, args['name'], tenant.id)
        if net:
            log.debug('Network already exists:%s' % net['id'])
            return
        if tenant:
            args['tenant_id'] = tenant.id
        network = self.neutron.create_network({'network' : args})
        log.debug('Created network:%s' % network['network']['id'])

    def create_subnet(self, **args):
        log.debug('Creating subnet:%s' % args)
        tenant = self.__find_project(args.pop('tenant_name', None))
        network = self.__find_network(self.neutron, args.pop('network', None),
                                      tenant.id)
        args['network_id'] = network['id']
        sub = self.__find_subnet(self.neutron, args['name'], tenant.id,
                                 network['id'])
        if sub:
            log.debug('Subnet already exists:%s' % sub['id'])
            return
        if tenant:
            args['tenant_id'] = tenant.id
        try:
            subnet = self.neutron.create_subnet({"subnet" : args})
        except neutron_exceptions.BadRequest, e:
            log.error('Cannot create subnet:%s' % str(e))
            return
        log.debug('Created subnet:%s' % subnet['subnet']['id'])

    def setup_config(self, config):
        log.debug('Checking schema')
        validate(config, schema.SCHEMA)
        for section in config.keys():
            for item in config[section]:
                method = getattr(self, SECTION_SCHEMA[section])
                method(**item)
