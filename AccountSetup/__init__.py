from keystoneclient.v2_0 import client as key_v2
from keystoneclient.openstack.common.apiclient import exceptions as keystone_exceptions
class AccountSetup(object):
    def __init__(self, username, password, tenant_name, auth_url):
        self.keystone = key_v2.Client(username=username,
                                      password=password,
                                      tenant_name=tenant_name,
                                      auth_url=auth_url)

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
            project = self.keystone.tenants.create(**args)
        except keystone_exceptions.Conflict:
            project = self.__find_project(args.pop('name', None))
        project.add_user(user.id, role.id)

    def setup_config(self, config):
        print config
        user = self.create_user(**config['user'])
        for project in config['projects']:
            self.create_project(user, **project)
