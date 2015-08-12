from openstack_account import utils

from keystoneclient.openstack.common.apiclient import exceptions as keystone_exceptions

import logging

log = logging.getLogger(__name__)

def create_user(keystone, **kwargs):
    log.debug('Creating user:%s' % kwargs)
    try:
        user = keystone.users.create(**kwargs)
        log.info('User created:%s' % user)
    except keystone_exceptions.Forbidden as error:
        log.error('Admin credentials required for user creation:%s' % str(error))
        return None
    except keystone_exceptions.Conflict:
        # User allready exists
        user = utils.find_user(keystone, kwargs['name'])
        log.debug("User with name already exists:%s" % user)
        # Update data with whats in args
        # Password is a seperate function
        password = kwargs.pop('password', None)
        if password:
            keystone.users.update_password(user.id, password)
        user = keystone.users.update(user.id, **kwargs)
        log.info("Updated user:%s" % user.id)
    return user.id

def create_project(keystone, **kwargs):
    log.debug('Creating project:%s' % kwargs)
    role = utils.find_role(keystone, kwargs.pop('role', None))
    kwargs['tenant_name'] = kwargs.pop('name', None)
    user = utils.find_user(keystone, kwargs.pop('user', None))

    try:
        project = keystone.tenants.create(**kwargs)
        log.info('Project created:%s' % project.id)
    except keystone_exceptions.Conflict:
        project = utils.find_project(keystone, kwargs['tenant_name'] or None)
        log.debug('Project already exists:%s' % project.id)
        # Update data with whats in args
        project = keystone.tenants.update(project.id, **kwargs)
        log.info("Project updated:%s" % project.id)
    if user and role:
        try:
            project.add_user(user.id, role.id)
            log.info('Added user:%s to project:%s with role:%s' %
                     (user.id, project.id, role.id))
        except keystone_exceptions.Conflict:
            # Role already exists
            log.info('Role exits user:%s to project:%s with role:%s' %
                     (user.id, project.id, role.id))
    return project.id
