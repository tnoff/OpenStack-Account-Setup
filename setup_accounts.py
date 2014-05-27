import argparse
from cinderclient.v1 import client as cinder_v1
from configobj import ConfigObj
from glanceclient import Client as glance_client
from keystoneclient.v2_0 import client as key_v2
from keystoneclient.apiclient.exceptions import Conflict as keystone_conflict
import logging
from novaclient.v1_1 import client as nova_v1
from novaclient.exceptions import BadRequest as nova_bad_request
from novaclient.exceptions import Conflict as nova_conflict
from novaclient.exceptions import ClientException as nova_client_exception

LOGGING_FORMAT = '%(asctime)s--%(levelname)s--%(message)s'
logging.basicConfig(format=LOGGING_FORMAT)
LOG = logging.getLogger(__name__)
LOG.setLevel(logging.DEBUG)

class AccountSetUp(object):
    def __init__(self, config_file, admin_password, auth_url):
        LOG.debug('Starting Account Setup')
        self.auth_url = auth_url
        self.keystone = key_v2.Client(username='admin',
                                      password=admin_password,
                                      tenant_name='admin',
                                      auth_url=auth_url)
        self.nova = nova_v1.Client('admin',
                                   admin_password,
                                   'admin',
                                   auth_url)
        self.cinder = cinder_v1.Client('admin',
                                       admin_password,
                                       'admin',
                                       auth_url)
        LOG.debug('Reading from config:%s' % config_file)
        account_dict = ConfigObj(config_file)
        for account in account_dict:
            LOG.debug('Setting up account:%s' % account)
            self.setup_account(**account_dict[account])

    def __setup_glance(self, keystone):
        token = keystone.auth_token
        service_catalog = keystone.service_catalog
        catalog = service_catalog.catalog['serviceCatalog']
        glance_ip = None
        for endpoint in catalog:
            if 'image' == endpoint['type']:
                glance_ip = endpoint['endpoints'][0]['publicURL']
                break
        return token, glance_ip

    def setup_account(self, **args):
        project = self.__project_create(args['project_name'],
                                        args['project_description'])
        user = self.__user_create(args['user_name'],
                                  args['user_password'],
                                  args['user_email'])
        self.__tenant_add_user(project, user, args['user_role'])
        if 'FLAVORS' in args.keys():
            for flavor in args['FLAVORS']:
                a = args['FLAVORS'][flavor]
                a['name'] = flavor
                self.__create_flavor(**a)
        if 'NOVA_QUOTAS' in args.keys():
            self.__nova_quotas(project.id, **args['NOVA_QUOTAS'])
        if 'CINDER_QUOTAS' in args.keys():
            self.__cinder_quotas(project.id, **args['CINDER_QUOTAS'])
        nova = nova_v1.Client(args['user_name'], args['user_password'],
                              project.name, self.auth_url)
        if 'SECURITY_GROUPS' in args.keys():
            for group, rules in args['SECURITY_GROUPS'].iteritems():
                self.__security_group(nova, group, **rules)
        if 'KEYPAIRS' in args.keys():
            self.__create_keypairs(nova, **args['KEYPAIRS'])
        if 'SOURCE_FILE' in args.keys():
            self.__create_source_file(args['SOURCE_FILE']['file'], self.auth_url, project, user)
        if 'IMAGES' in args.keys():
            keystone = key_v2.Client(username=args['user_name'],
                                     password=args['user_password'],
                                     tenant_name=project.name, auth_url=self.auth_url)
            token, glance_ep = self.__setup_glance(keystone)
            glance = glance_client('1', token=token, endpoint=glance_ep)
            self.__create_images(glance, **args['IMAGES'])

    def __project_create(self, name, description):
        LOG.debug('Creating project:%s' % name)
        try:
            return self.keystone.tenants.create(name, description=description)
        except keystone_conflict as kc:
            LOG.error('Cannot create project:%s' % kc)
            for tenant in self.keystone.tenants.list():
                if tenant.name == name:
                    return tenant

    def __user_create(self, name, password, email):
        LOG.debug('Creating user:%s' % name)
        try:
            return self.keystone.users.create(name, password, email)
        except keystone_conflict as kc:
            LOG.error('Cannot create user:%s' % kc)
            for user in self.keystone.users.list():
                if user.name == name:
                    return user
    def __tenant_add_user(self, project, user, role_name):
        role_id = None
        for role in self.keystone.roles.list():
            if role_name.lower() in role.name.lower():
                role_id = role.id
        LOG.debug("Granting user role:%s" % role_name)
        try:
            self.keystone.tenants.add_user(project.id, user.id, role_id)
        except keystone_conflict:
            LOG.error("User already has role")

    def __create_flavor(self, **args):
        LOG.debug('Creating flavors')
        try:
            self.nova.flavors.create(**args)
        except TypeError as te:
            LOG.error('Cannot create flavor:%s' % te)
        except nova_conflict as nc:
            LOG.error('Cannot create flavor:%s' % nc)

    def __nova_quotas(self, project_id, **args):
        LOG.debug('Updating nova quotas')
        try:
            self.nova.quotas.update(project_id, **args)
        except TypeError as te:
            LOG.error('Cannot update nova quotas:%s' % te)

    def __cinder_quotas(self, project_id, **args):
        LOG.debug('Updating cinder quotas')
        try:
            self.cinder.quotas.update(project_id, **args)
        except TypeError as te:
            LOG.error("Cannot update cinder quotas:%s" % te)

    def __security_group(self, nova_client, group, **rules):
        group_info = group.split(':')
        LOG.debug('Creating security group:%s' % group_info[0])
        try:
            group = vars(nova_client.security_groups.create(group_info[0], group_info[1]))['_info']
        except (nova_bad_request, nova_client_exception):
            LOG.debug('Group already exists')
            for g in nova_client.security_groups.list():
                group = vars(nova_client.security_groups.get(g))['_info']
        for rule_name, rule_data in rules.iteritems():
            LOG.debug("Creating rule:%s" % rule_name)
            try:
                nova_client.security_group_rules.create(group['id'], **rule_data)
            except nova_bad_request:
                LOG.error("Rule already exists, skipping")

    def __create_keypairs(self, nova_client, **keypair_args):
        for key_name, key_data in keypair_args.iteritems():
            LOG.debug("Creating keypair:%s" % key_name)
            f = open(key_data['file'], 'r')
            key_file = f.read()
            try:
                nova_client.keypairs.create(key_name, public_key=key_file)
            except nova_conflict:
                LOG.error("Keypair already exists, skipping")

    def __create_source_file(self, file_dir, auth_url, project, user):
        file_location = file_dir + user.name + '.sh'
        text = '#!/bin/bash\n'
        text += 'export OS_AUTH_URL=' + auth_url + '\n'
        text += 'export OS_TENANT_ID=' + project.id + '\n'
        text += 'export OS_TENANT_NAME=' + project.name + '\n'
        text += 'export OS_USERNAME=' + user.name + '\n'
        text += 'echo "Please enter your OpenStack Password:"\n'
        text += 'read -s OS_PASSWORD_INPUT\n'
        text += 'export OS_PASSWORD=$OS_PASSWORD_INPUT\n'
        f = open(file_location, 'w+')
        f.write(text)

    def __create_images(self, glance, **image_data):
        for image_name, image_info in image_data.iteritems():
            LOG.debug('Creating image:%s' % image_name)
            image_info['name'] = image_name
            file_location = image_info.pop('file', None)
            new_image = glance.images.create(**image_info)
            if file_location is not None:
                new_image.update(data=open(file_location, 'rb'))

def parse_args():
    a = argparse.ArgumentParser(description='Setup accounts on an OpenStack cluster')
    a.add_argument('config_file', help='Config File')
    a.add_argument('admin_password', help='Admin password for cluster')
    a.add_argument('auth_url', help='Keystone Auth URL for cluster')
    return a.parse_args()

def main():
    args = parse_args()
    AccountSetUp(args.config_file, args.admin_password, args.auth_url)

if __name__ == '__main__':
    main()
