from openstack_account import settings
from openstack_account import utils
from openstack_account.exceptions import OpenStackAccountError
from openstack_account.openstack import keystone as os_keystone
from openstack_account.openstack import neutron as os_neutron

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
    log.debug('Creating flavor:%s' % kwargs)
    try:
        flavor = nova.flavors.create(**kwargs)
        log.info("Created flavor:%s" % flavor.id)
        return flavor.id
    except nova_exceptions.Conflict:
        # Flavor already exists
        flavor_id = find_flavor(nova, kwargs.pop('name', None))
        log.info('Flavor already exists:%s' % flavor_id)
        return flavor_id

def set_nova_quota(nova, keystone, **kwargs):
    log.debug('Setting nova quotas:%s' % kwargs)
    tenant_name = kwargs.pop('tenant_name', None)
    project = os_keystone.find_project(tenant_name, keystone)
    if not project:
        raise OpenStackAccountError("Cannot find project:%s" % tenant_name)
    try:
        nova.quotas.update(project.id, **kwargs)
        log.info("Set quotas for project:%s" % project.id)
    except nova_exceptions.BadRequest as e:
        log.error('Cannot set quotas:%s' % str(e))
    return project.id

def create_security_group(nova, keystone, auth_url, **kwargs):
    log.debug('Creating security group:%s' % kwargs)
    tenant = os_keystone.find_project(kwargs.pop('tenant_name', None),
                                      keystone)
    # if no tenant given, use regular nova auth
    # if teant given, create temp user to add security group
    if not tenant:
        return __create_security_group(nova, **kwargs)
    with os_keystone.temp_user(tenant, keystone) as (user, user_password):
        nova = nova_v1.Client(user.name,
                              user_password,
                              tenant.name,
                              auth_url)
        return __create_security_group(nova, **kwargs)

def __create_security_group(nova, **kwargs):
    rules = kwargs.pop('rules', None)
    group_id = find_sec_group(nova, kwargs['name'])
    if group_id:
        log.debug('Group already exists:%s' % group_id)
    else:
        try:
            group = nova.security_groups.create(**kwargs)
            group_id = group.id # pylint: disable=no-member
            log.info('Created security group:%s' % group_id)
        except nova_exceptions.BadRequest:
            # Group already exists
            group_id = find_sec_group(nova, kwargs.pop('name', None))
            log.info('Group already exists:%s' % group_id)
        except nova_exceptions.ClientException, e:
            log.error('Cannot create security group:%s' % e)
            return
    for rule in rules:
        try:
            r = nova.security_group_rules.create(group_id, **rule)
            log.info("Created new rule:%s" % str(r))
        except nova_exceptions.BadRequest:
            log.info('Cannot create rule, already exists:%s' % rule)
            continue
        except nova_exceptions.CommandError, e:
            log.error('Cannot create rule:%s' % e)
            continue
    return group_id

def create_keypair(nova, **kwargs):
    log.debug('Creating keypair:%s' % kwargs)
    if kwargs['file']:
        with open(kwargs.pop('file'), 'r') as f:
            kwargs['public_key'] = f.read()
    try:
        nova.keypairs.create(**kwargs)
        log.info('Created keypair:%s' % kwargs['name'])
    except nova_exceptions.Conflict:
        log.info('Keypair already exists:%s' % kwargs['name'])
    return kwargs['name']

def create_server(nova, neutron, **kwargs):
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
    # build nic with correct network uuid if needed
    nics = kwargs.pop('nics', None)
    kwargs['nics'] = []
    for nic in nics:
        name = nic.pop('network_name')
        network = os_neutron.find_network(neutron, name, None)
        nic['net-id'] = network['id']
        kwargs['nics'].append(nic)
    # Check for and build server
    server = find_server(nova, name)
    if server:
        log.info('Server already exists:%s' % server.id)
    else:
        server = nova.servers.create(**kwargs)
        log.info('Server created:%s' % server.id)
    if wait:
        log.info("Waiting for server:%s, timeout:%s" % (server.id, timeout))
        utils.wait_status(nova.servers.get, server.id,
                          ['ACTIVE'], ['ERROR'], interval, timeout)
    return server.id
