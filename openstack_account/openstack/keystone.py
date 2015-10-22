from openstack_account import settings
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
    return {'user' : user.id}

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
    return {'project' : project.id}

def save_users(keystone):
    log.info('Saving all user data')
    return_data = []
    for user in keystone.users.list():
        if user.name in settings.EXPORT_SKIP_USERS:
            continue
        user_data = vars(user)
        ignore_keys = settings.EXPORT_KEYS_IGNORE + ['tenantId', 'username']
        for key in ignore_keys:
            user_data.pop(key, None)
        log.debug('Saving user data:%s' % user_data)
        return_data.append({'user' : utils.pretty_dict(user_data)})
    return return_data

def save_projects(keystone):
    log.info('Saving all project data')
    return_data = []
    for project in keystone.tenants.list():
        if project.name in settings.EXPORT_SKIP_PROJECTS:
            continue
        project_data = vars(project)
        for key in settings.EXPORT_KEYS_IGNORE:
            project_data.pop(key, None)
        log.debug('Saving project data:%s' % project_data)
        return_data.append({'project' : utils.pretty_dict(project_data)})
    return return_data

def save_roles(keystone):
    log.info('Saving all role data')
    return_data = []
    for project in keystone.tenants.list():
        if project.name in settings.EXPORT_SKIP_PROJECTS:
            continue
        for user in keystone.tenants.list_users(project.id):
            for role in keystone.users.list_roles(user.id, tenant=project.id):
                data = dict()
                data['name'] = project.name
                data['user'] = user.name
                data['role'] = role.name
                data = utils.pretty_dict(data)
                log.debug("Saving role data:%s" % data)
                return_data.append({'project' : data})
    return return_data
