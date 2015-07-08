from openstack_account import utils

from keystoneclient.openstack.common.apiclient import exceptions as keystone_exceptions

from contextlib import contextmanager
import logging

log = logging.getLogger(__name__)

@contextmanager
def temp_user(tenant, keystone):
    created_user = False
    # If tenant given is None, return None
    if not tenant:
        user = None
        password = None
    else:
        # Create temp user that is authorized to tenant
        log.debug('Creating temp user for tenant:%s' % tenant.id)
        username = utils.random_string(prefix='user-')
        password = utils.random_string(length=30)
        user = keystone.users.create(name=username,
                                     password=password,
                                     email=None)
        created_user = True
        log.debug('Created temp user:%s for tenant:%s' % (user.id, tenant.id))
        member_role = find_role('_member_', keystone)
        # stupid keystone is stupid
        if not member_role:
            member_role = find_role('member', keystone)
        tenant.add_user(user.id, member_role.id)
    try:
        yield user, password
    finally:
        if created_user:
            log.debug('Deleting temp user:%s' % user.id)
            keystone.users.delete(user.id)

def find_user(name, keystone):
    if not name:
        return None
    for user in keystone.users.list():
        if user.name == name:
            return user
    return None

def find_role(name, keystone):
    if not name:
        return None
    for role in keystone.roles.list():
        if name.lower() == role.name.lower():
            return role
    return None

def find_project(name, keystone):
    if not name:
        return None
    for tenant in keystone.tenants.list():
        if tenant.name == name:
            return tenant
    return None

def create_user(keystone, **kwargs):
    log.debug('Creating user:%s' % kwargs)
    try:
        user = keystone.users.create(**kwargs)
    except keystone_exceptions.Conflict:
        # User allready exists
        user = find_user(kwargs['name'], keystone)
    log.info('User created:%s' % user)
    return user

def create_project(keystone, **kwargs):
    log.debug('Creating project:%s' % kwargs)
    role = find_role(kwargs.pop('role', None), keystone)
    kwargs['tenant_name'] = kwargs.pop('name', None)
    user = find_user(kwargs.pop('user', None), keystone)

    try:
        project = keystone.tenants.create(**kwargs)
    except keystone_exceptions.Conflict:
        project = find_project(kwargs['tenant_name'] or None, keystone)
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
