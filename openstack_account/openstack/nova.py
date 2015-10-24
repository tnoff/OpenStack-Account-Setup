from openstack_account import settings
from openstack_account import utils
from openstack_account.exceptions import OpenStackAccountError

from novaclient import exceptions as nova_exceptions

import logging

log = logging.getLogger(__name__)

def create_flavor(nova, **kwargs):
    log.debug('Creating flavor:%s' % kwargs)
    try:
        flavor = nova.flavors.create(**kwargs)
        log.info("Created flavor:%s" % flavor.id)
        return {'flavor' : flavor.id}
    except nova_exceptions.Conflict:
        # Flavor already exists
        flavor_id = utils.find_flavor(nova, kwargs.pop('name', None))
        log.info('Flavor already exists:%s' % flavor_id)
        return {'flavor' : flavor_id}

def set_nova_quota(nova, keystone, **kwargs):
    log.debug('Setting nova quotas:%s' % kwargs)
    tenant_name = kwargs.pop('tenant_name', None)
    project = utils.find_project(keystone, tenant_name)
    if not project:
        raise OpenStackAccountError("Cannot find project:%s" % tenant_name)
    try:
        nova.quotas.update(project.id, **kwargs)
        log.info("Set quotas for project:%s" % project.id)
    except nova_exceptions.BadRequest as e:
        log.error('Cannot set quotas:%s' % str(e))
    return {'nova_quota' : project.id}

def create_security_group(nova, **kwargs):
    log.debug('Creating security group:%s' % kwargs)
    rules = kwargs.pop('rules', None)
    group_id = utils.find_sec_group(nova, kwargs['name'])
    if group_id:
        log.debug('Group already exists:%s' % group_id)
    else:
        try:
            group = nova.security_groups.create(**kwargs)
            group_id = group.id # pylint: disable=no-member
            log.info('Created security group:%s' % group_id)
        except nova_exceptions.BadRequest:
            # Group already exists
            group_id = utils.find_sec_group(nova, kwargs.pop('name', None))
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
    return {
        'security_group' : group_id,
        # projectid means tenant name, nova is dumb
        'os_tenant_name' : nova.projectid,
    }

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
    return {'keypair' : kwargs['name']}

def create_server(nova, neutron, cinder, **kwargs):
    log.debug('Create server:%s' % kwargs)
    name = kwargs.get('name')
    wait = kwargs.pop('wait', settings.SERVER_WAIT)
    timeout = kwargs.pop('timeout', settings.SERVER_WAIT_TIMEOUT)
    interval = kwargs.pop('interval', settings.SERVER_WAIT_INTERVAL)
    server = utils.find_server(nova, name)
    flavor_name = kwargs.pop('flavor_name', None)
    if flavor_name:
        kwargs['flavor'] = utils.find_flavor(nova, flavor_name)
    image_name = kwargs.pop('image_name', None)
    if image_name:
        kwargs['image'] = utils.find_image(nova, image_name).id
    # build nic with correct network uuid if needed
    nics = kwargs.pop('nics', [])
    kwargs['nics'] = []
    for nic in nics:
        name = nic.pop('network_name')
        network = utils.find_network(neutron, name, None)
        nic['net-id'] = network['id']
        kwargs['nics'].append(nic)
    # Check for and build server
    volumes = kwargs.pop('volumes', [])
    kwargs['block_device_mapping'] = {}
    for volume in volumes:
        vol = utils.find_volume(cinder, volume['volume_name'])
        terminate = int(volume.pop('terminate_on_delete', False))
        device = volume.pop('device_name', None)
        kwargs['block_device_mapping'][device] = \
            '%s:::%d' % (vol.id, terminate)

    server = utils.find_server(nova, name)
    if server:
        log.info('Server already exists:%s' % server.id)
    else:
        server = nova.servers.create(**kwargs)
        log.info('Server created:%s' % server.id)
    if wait:
        log.info("Waiting for server:%s, timeout:%s" % (server.id, timeout))
        utils.wait_status(nova.servers.get, server.id,
                          ['ACTIVE'], ['ERROR'], interval, timeout)
    return {'server' : server.id}

def save_flavors(nova):
    log.info('Saving flavor data')
    flavors = nova.flavors.list() + nova.flavors.list(is_public=False)
    skips = settings.EXPORT_KEYS_IGNORE + settings.EXPORT_SKIP_FLAVORS
    flavor_data = []
    for flavor in flavors:
        flavor_args = vars(flavor)
        for key in flavor_args.keys():
            if key in skips:
                flavor_args.pop(key)
        # special to flavors
        flavor_args['ephemeral'] = flavor_args.pop('OS-FLV-EXT-DATA:ephemeral', 0)
        flavor_args['is_public'] = flavor_args.pop('os-flavor-access:is_public', True)
        if flavor_args['swap'] == '':
            flavor_args['swap'] = 0
        else:
            flavor_args['swap'] = int(flavor_args.pop('swap', 0))
        flavor_args['name'] = str(flavor_args.pop('name'))
        flavor_data.append({'flavor' : flavor_args})
    return flavor_data

def save_quotas(nova, tenant):
    quotas = nova.quotas.get(tenant.id)
    quota_args = vars(quotas)
    for key in quota_args.keys():
        if key in settings.EXPORT_KEYS_IGNORE:
            quota_args.pop(key)
    quota_args['tenant_name'] = str(tenant.name)
    return {'nova_quota' : quota_args}

def save_security_groups(nova, tenant):
    group_data = []
    groups = nova.security_groups.list()
    rule_skip = settings.EXPORT_SKIP_RULES + settings.EXPORT_KEYS_IGNORE
    for group in groups:
        group_args = vars(group)
        group_args['name'] = str(group_args.pop('name'))
        group_args['description'] = str(group_args.pop('description'))
        for key in group_args.keys():
            if key in settings.EXPORT_KEYS_IGNORE + ['tenant_id']:
                group_args.pop(key)
        for rule in group_args['rules']:
            for key in rule.keys():
                if key in rule_skip:
                    rule.pop(key)
            rule['ip_protocol'] = str(rule.pop('ip_protocol'))
            rule['from_port'] = rule.pop('from_port')
            rule['to_port'] = rule.pop('to_port')
            ip_range = rule.pop('ip_range')
            try:
                rule['cidr'] = str(ip_range.pop('cidr'))
            except KeyError:
                rule['cidr'] = None
        new_data = {'security_group' : group_args,
                    'os_tenant_name' : str(tenant.name)}
        group_data.append(new_data)
    return group_data
