from openstack_account import settings
from openstack_account import utils

from openstack_account.openstack import keystone as os_keystone

from novaclient.v1_1 import client as nova_v1 #pylint: disable=no-name-in-module
from novaclient import exceptions as nova_exceptions

import logging

log = logging.getLogger(__name__)

def find_sec_group(nova, name):
    for group in nova.security_groups.list():
        if group.name == name:
            return group.id
    return None

def find_flavor(nova, name):
    for flavor in nova.flavors.list():
        if flavor.name == name:
            return flavor.id
    return None

def find_server(nova, name):
    for server in nova.servers.list():
        if server.name == name:
            return server
    return None

def find_image(nova, name):
    for image in nova.images.list():
        if image.name == name:
            return image.id
    return None

def create_flavor(nova, **kwargs):
    log.info('Creating flavor:%s' % kwargs)
    try:
        nova.flavors.create(**kwargs)
    except nova_exceptions.Conflict:
        # Flavor already exists
        log.debug('Flavor already exists')
    except TypeError, e:
        log.error('Cannot create flavor:%s', e)

def set_nova_quota(nova, keystone, **kwargs):
    log.info('Setting nova quotas:%s' % kwargs)
    tenant_name = kwargs.pop('tenant_name', None)
    project = os_keystone.find_project(tenant_name, keystone)
    if not project:
        log.error('Cannot find project:%s' % tenant_name)
        return
    try:
        nova.quotas.update(project.id, **kwargs)
    except nova_exceptions.BadRequest, e:
        log.error('Cannot set quotas:%s' % e)


def create_security_group(nova, keystone, auth_url, **kwargs):
    log.debug('Creating security group:%s' % kwargs)
    tenant = os_keystone.find_project(kwargs.pop('tenant_name', None),
                                      keystone)
    rules = kwargs.pop('rules', None)
    # By default use self.nova
    # If another user returned, use that nova
    with os_keystone.temp_user(tenant, keystone) as (user, user_password):
        # If user is None, just use regular nova
        if user:
            nova = nova_v1.Client(user.name,
                                  user_password,
                                  tenant.name,
                                  auth_url)
        group_id = find_sec_group(nova, kwargs['name'])
        if group_id:
            log.debug('Group already exists:%s' % group_id)
        else:
            try:
                group = nova.security_groups.create(**kwargs)
                group_id = group.id # pylint: disable=no-member
                log.debug('Created security group:%s' % group_id)
            except nova_exceptions.BadRequest:
                # Group already exists
                group_id = find_sec_group(nova, kwargs.pop('name', None))
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

def create_keypair(nova, **kwargs):
    log.info('Creating keypair:%s' % kwargs)
    if kwargs['file']:
        with open(kwargs.pop('file'), 'r') as f:
            kwargs['public_key'] = f.read()
    try:
        nova.keypairs.create(**kwargs)
        log.debug('Created keypair:%s' % kwargs['name'])
    except nova_exceptions.Conflict:
        log.debug('Keypair already exists')

def create_server(nova, **kwargs):
    log.debug('Create server:%s' % kwargs)
    name = kwargs.get('name')
    wait = kwargs.pop('wait', settings.SERVER_WAIT)
    timeout = kwargs.pop('timeout', settings.SERVER_WAIT_TIMEOUT)
    interval = kwargs.pop('interval', settings.SERVER_WAIT_INTERVAL)
    server = find_server(nova, name)
    flavor_name = kwargs.pop('flavor_name', None)
    if flavor_name:
        kwargs['flavor'] = find_flavor(nova, flavor_name)
    image_name = kwargs.pop('image_name', None)
    if image_name:
        kwargs['image'] = find_image(nova, image_name)
    # Check for and build server
    server = find_server(nova, name)
    if server:
        log.info('Server already exists:%s' % server.id)
    else:
        server = nova.servers.create(**kwargs)
        log.info('Server created:%s' % server.id)
    if wait:
        log.info("Waiting for server:%s" % server.id)
        utils.wait_status(nova.servers.get, server.id,
                          ['ACTIVE'], ['ERROR'], interval, timeout)
