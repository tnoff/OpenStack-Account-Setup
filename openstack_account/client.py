from openstack_account import schema

from cinderclient.v1 import client as cinder_v1
from glanceclient import Client as glance_client
from keystoneclient.v2_0 import client as key_v2
from keystoneclient.openstack.common.apiclient import exceptions as keystone_exceptions
from novaclient.v1_1 import client as nova_v1
from novaclient import exceptions as nova_exceptions

from jsonschema import validate
import logging
import os

log = logging.getLogger(__name__)
dir_path = os.path.dirname(__file__)

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

    def __find_user(self, name):
        for user in self.keystone.users.list():
            if user.name == name:
                return user
        return None

    def __find_role(self, name):
        for role in self.keystone.roles.list():
            if role.name == name:
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

    def __find_valid_tenant(self, user):
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

    def create_user(self, **args):
        log.debug('Creating user:%s' % args)
        try:
            user = self.keystone.users.create(**args)
        except keystone_exceptions.Conflict:
            # User allready exists
            user = self.__find_user(args['name'])
        log.info('User created:%s' % user)
        return user

    def create_project(self, user, **args):
        log.debug('Creating project:%s' % args)
        role = self.__find_role(args.pop('role', None))
        args['tenant_name'] = args.pop('name', None)
        try:
            self.keystone.tenants.create(**args)
            project = self.__find_project(args['tenant_name'] or  None)
        except keystone_exceptions.Conflict:
            project = self.__find_project(args['tenant_name'] or None)
        if role:
            try:
                project.add_user(user.id, role.id)
                log.debug('Added user:%s to project:%s with role:%s' %
                          (user.id, project.id, role.id))
            except keystone_exceptions.Conflict:
                # Role already exists
                log.debug('Role exits user:%s to project:%s with role:%s' %
                          (user.id, project.id, role.id))
        log.info('Projected created:%s' % project)

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
        project = self.__find_project(args.pop('tenant_name', None))
        try:
            self.nova.quotas.update(project.id, **args)
        except nova_exceptions.BadRequest, e:
            log.error('Cannot set quotas:%s' % e)

    def set_cinder_quota(self, **args):
        log.info('Setting cinder quotas:%s' % args)
        project = self.__find_project(args.pop('tenant_name', None))
        self.cinder.quotas.update(project.id, **args)

    def create_security_group(self, user, user_password, **args):
        log.debug('Creating security group:%s' % args)
        tenant_name = args.pop('tenant_name', None)
        rules = args.pop('rules', None)
        nova = nova_v1.Client(user.name,
                              user_password,
                              tenant_name,
                              self.os_auth_url)
        try:
            group = nova.security_groups.create(**args)
            group_id = group.id
        except nova_exceptions.BadRequest:
            # Group already exists
            group_id = self.__find_sec_group(nova, args.pop('name', None))
        except nova_exceptions.ClientException, e:
            log.error('Cannot create security group:%s' % e)
            return
        log.info("Created security group:%s" % group_id)
        for rule in rules:
            try:
                nova.security_group_rules.create(group_id, **rule)
            except nova_exceptions.BadRequest:
                log.debug('Cannot create rule, already exists')
            except nova_exceptions.CommandError, e:
                log.error('Cannot create rule:%s' % e)
            log.info('Created security group rule:%s' % rule)

    def create_keypair(self, user, user_password, **args):
        log.info('Creating keypair:%s' % args)
        tenant = self.__find_valid_tenant(user)
        nova = nova_v1.Client(user.name,
                              user_password,
                              tenant.name,
                              self.os_auth_url)
        if args['file']:
            with open(args.pop('file'), 'r') as f:
                args['public_key'] = f.read()
        try:
            nova.keypairs.create(**args)
        except nova_exceptions.Conflict:
            log.debug('Keypair already exists')

    def create_source_file(self, user, **args):
        log.info('Creating source file:%s' % args)
        tenant = self.__find_project(args.pop('tenant_name', None))
        stringy = '#!/bin/bash\n'
        stringy += 'export OS_USERNAME="%s"\n' % user.name
        stringy += 'export OS_TENANT_ID="%s"\n' % tenant.id
        stringy += 'export OS_TENANT_NAME="%s"\n' % tenant.name
        stringy += 'export OS_AUTH_URL="%s"\n' % self.os_auth_url
        stringy += 'echo "Please enter your OpenStack Password:"\n'
        stringy += 'read -s OS_PASSWORD_INPUT\n'
        stringy += 'export OS_PASSWORD=$OS_PASSWORD_INPUT\n'
        with open(args.pop('file', None), 'w+') as f:
            f.write(stringy)

    def create_image(self, user, user_password, **args):
        log.debug('Creating image:%s' % args)
        tenant = self.__find_project(args.pop('tenant_name', None))
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
            log.info('Image exists:%s' % image)
            return
        file_location = args.pop('file', None)
        image = glance.images.create(**args)
        if file_location:
            image.update(data=open(file_location, 'rb'))
        log.info('Created image:%s' % image)

    def setup_config(self, config):
        log.debug('Checking schema')
        validate(config, schema.SCHEMA)
        try:
            user = self.create_user(**config['user'])
            user_password = config['user']['password']
        except KeyError:
            log.error('No user in config, exiting')
            return
        try:
            for project in config['projects']:
                self.create_project(user, **project)
        except KeyError:
            log.debug('No projects in config')
        try:
            for flavor in config['flavors']:
                self.create_flavor(**flavor)
        except KeyError:
            log.debug('No flavors in config')
        try:
            for quota in config['nova_quotas']:
                self.set_nova_quota(**quota)
        except KeyError:
            log.debug('No nova quotas in config')
        try:
            for quota in config['cinder_quotas']:
                self.set_cinder_quota(**quota)
        except KeyError:
            log.debug('No cinder quotas in config')
        try:
            for group in config['security_groups']:
                self.create_security_group(user, user_password, **group)
        except KeyError:
            log.debug('No security group in config')
        try:
            for key in config['keypairs']:
                self.create_keypair(user, user_password, **key)
        except KeyError:
            log.debug('No keypairs in config')
        try:
            for source in config['source_files']:
                self.create_source_file(user, **source)
        except KeyError:
            log.debug('No source file in config')
        try:
            for image in config['images']:
                self.create_image(user, user_password, **image)
        except KeyError:
            log.debug('No images in config')
