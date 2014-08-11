from cinderclient.v1 import client as cinder_v1
from keystoneclient.v2_0 import client as key_v2
from keystoneclient.openstack.common.apiclient import exceptions as keystone_exceptions
from novaclient.v1_1 import client as nova_v1
from novaclient import exceptions as nova_exceptions

class AccountSetup(object):
    def __init__(self, username, password, tenant_name, auth_url):
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

    def create_user(self, **args):
        try:
            user = self.keystone.users.create(**args)
        except keystone_exceptions.Conflict:
            # User allready exists
            user = self.__find_user(args['name'])
        return user

    def create_project(self, user, **args):
        role = self.__find_role(args.pop('role', None))
        args['tenant_name'] = args.pop('name', None)
        try:
            self.keystone.tenants.create(**args)
            project = self.__find_project(args['tenant_name'] or  None)
        except keystone_exceptions.Conflict:
            project = self.__find_project(args['tenant_name'] or None)
        try:
            project.add_user(user.id, role.id)
        except keystone_exceptions.Conflict:
            # Role already exists
            pass

    def create_flavor(self, **args):
        try:
            self.nova.flavors.create(**args)
        except nova_exceptions.Conflict:
            # Flavor already exists
            pass

    def set_nova_quota(self, **args):
        project = self.__find_project(args.pop('tenant_name', None))
        self.nova.quotas.update(project.id, **args)

    def set_cinder_quota(self, **args):
        project = self.__find_project(args.pop('tenant_name', None))
        self.cinder.quotas.update(project.id, **args)

    def create_security_group(self, user, user_password, **args):
        tenant_name = args.pop('tenant_name', None)
        rules = args.pop('rules', None)
        nova = nova_v1.Client(user.name,
                              user_password,
                              tenant_name,
                              self.os_auth_url)
        try:
            group = nova.security_groups.create(**args)
        except nova_exceptions.BadRequest:
            # Group already exists
            group = self.__find_sec_group(nova, args.pop('name', None))
        for rule in rules:
            try:
                nova.security_group_rules.create(group, **rule)
            except nova_exceptions.BadRequest:
                # Rule already exits
                pass

    def create_keypair(self, user, user_password, **args):
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
            # Keypair already exists
            pass

    def setup_config(self, config):
        print config
        user = self.create_user(**config['user'])
        user_password = config['user']['password']
        for project in config['projects']:
            self.create_project(user, **project)
        for flavor in config['flavors']:
            self.create_flavor(**flavor)
        for quota in config['nova_quotas']:
            self.set_nova_quota(**quota)
        for quota in config['cinder_quotas']:
            self.set_cinder_quota(**quota)
        for group in config['security_groups']:
            self.create_security_group(user, user_password, **group)
        for key in config['keypairs']:
            self.create_keypair(user, user_password, **key)
