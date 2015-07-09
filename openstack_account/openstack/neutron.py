from openstack_account.openstack import keystone as os_keystone

from neutronclient.common import exceptions as neutron_exceptions

import logging

log = logging.getLogger(__name__)

def find_network(neutron, name, tenant_id):
    for net in neutron.list_networks()['networks']:
        if net['name'] == name:
            if tenant_id:
                if tenant_id == net['tenant_id']:
                    return net
            else:
                return net
    return None

def find_subnet(neutron, name, tenant_id, network_id):
    for sub in neutron.list_subnets()['subnets']:
        if sub['name'] == name:
            if network_id:
                if sub['network_id'] == network_id:
                    return sub
            elif tenant_id:
                if tenant_id == sub['tenant_id']:
                    return sub
            else:
                return sub
    return None

def find_router(neutron, name, tenant_id):
    for router in neutron.list_routers()['routers']:
        if router['name'] == name:
            if tenant_id:
                if tenant_id == router['tenant_id']:
                    return router
            else:
                return router
    return None

def create_network(neutron, keystone, **args):
    log.debug('Creating network:%s' % args)
    tenant = os_keystone.find_project(args.pop('tenant_name', None),
                                      keystone)
    net = find_network(neutron, args['name'], tenant.id)
    if net:
        log.info('Network already exists:%s' % net['id'])
        return
    if tenant:
        args['tenant_id'] = tenant.id
    network = neutron.create_network({'network' : args})
    log.info('Created network:%s' % network['network']['id'])

def create_subnet(neutron, keystone, **args):
    log.debug('Creating subnet:%s' % args)
    tenant = os_keystone.find_project(args.pop('tenant_name', None),
                                      keystone)
    network = find_network(neutron, args.pop('network', None), tenant.id)
    args['network_id'] = network['id']
    sub = find_subnet(neutron, args['name'], tenant.id, network['id'])
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

def create_router(neutron, keystone, **args):
    log.debug('Create router:%s' % args)
    tenant = os_keystone.find_project(args.pop('tenant_name', None),
                                      keystone)
    if tenant:
        args['tenant_id'] = tenant.id
    router = find_router(neutron, args['name'], None)
    external = find_network(neutron, args.pop('external_network', None),
                            None)
    internal = find_subnet(neutron,
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
