from openstack_account import utils

from neutronclient.common import exceptions as neutron_exceptions

import logging

log = logging.getLogger(__name__)

def create_network(neutron, keystone, **args):
    log.debug('Creating network:%s' % args)
    tenant = utils.find_project(keystone,
                                args.pop('tenant_name', None))
    if not tenant:
        tenant_id = None
    else:
        tenant_id = tenant.id
    net = utils.find_network(neutron, args['name'], tenant_id)
    if net:
        log.info('Network already exists:%s' % net['id'])
        return
    if tenant:
        args['tenant_id'] = tenant.id
    network = neutron.create_network({'network' : args})
    log.info('Created network:%s' % network['network']['id'])
    return {'network' : network['network']['id']}

def create_subnet(neutron, keystone, **args):
    log.debug('Creating subnet:%s' % args)
    tenant = utils.find_project(keystone,
                                args.pop('tenant_name', None))
    if not tenant:
        tenant_id = None
    else:
        tenant_id = tenant.id
    network = utils.find_network(neutron, args.pop('network', None), tenant_id)
    args['network_id'] = network['id']
    sub = utils.find_subnet(neutron, args['name'], tenant_id, network['id'])
    if sub:
        log.info('Subnet already exists:%s' % sub['id'])
        return
    if tenant:
        args['tenant_id'] = tenant.id
    try:
        subnet = neutron.create_subnet({"subnet" : args})
    except neutron_exceptions.BadRequest as e:
        log.error('Cannot create subnet:%s' % str(e))
        return
    log.info('Created subnet:%s' % subnet['subnet']['id'])
    return {'subnet' : subnet['subnet']['id']}

def create_router(neutron, keystone, **args):
    log.debug('Create router:%s' % args)
    tenant = utils.find_project(keystone,
                                args.pop('tenant_name', None))
    if tenant:
        args['tenant_id'] = tenant.id
    router = utils.find_router(neutron, args['name'], None)
    external = utils.find_network(neutron, args.pop('external_network', None),
                                  None)
    internal = utils.find_subnet(neutron,
                                 args.pop('internal_subnet', None),
                                 None, None)
    if router:
        log.info('Router already exists:%s' % router['id'])
    else:
        router = neutron.create_router({'router' : args})['router']
        log.info('Created router:%s' % router['id'])

    if external:
        data = {'network_id' : external['id']}
        neutron.add_gateway_router(router['id'],
                                   data)
        log.info('Set external network:%s for router:%s' % (external['id'],
                                                            router['id']))
    if internal:
        data = {'subnet_id' : internal['id']}
        try:
            neutron.add_interface_router(router['id'], data)
            log.info('Set internal subnet:%s for router:%s' % (internal['id'],
                                                               router['id']))
        except neutron_exceptions.BadRequest as e:
            log.error('Cannot add internal subnet:%s' % str(e))
    return {'router' : router['id']}
