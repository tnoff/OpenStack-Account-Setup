from openstack_account import settings
from openstack_account import utils

from openstack_account.openstack import keystone as os_keystone

import logging

log = logging.getLogger(__name__)

def find_volume(cinder, name):
    for volume in cinder.volumes.list():
        if volume.name == name:
            return volume
    return None

def set_cinder_quota(cinder, keystone, **args):
    log.info('Setting cinder quotas:%s' % args)
    project = os_keystone.find_project(args.pop('tenant_name', None),
                                       keystone)
    cinder.quotas.update(project.id, **args)

def create_volume(cinder, **args):
    log.debug('Create volume:%s' % args)
    name = args.pop('name', None)
    wait = args.pop('wait', settings.VOLUME_WAIT)
    timeout = args.pop('timeout', settings.VOLUME_WAIT_TIMEOUT)
    interval = args.pop('interval', settings.VOLUME_WAIT_INTERVAL)
    volume = find_volume(cinder, name)
    # Cinder uses 'display name' because fuck convention i suppose
    args['display_name'] = name
    if volume:
        log.info('Volume already exists:%s' % volume.id)
    else:
        volume = cinder.volumes.create(**args)
        log.info('Volume created:%s' % volume.id)
    if wait:
        log.info('Waiting for volume:%s' % volume.id)
        utils.wait_status(cinder.volumes.get, volume.id,
                          ['available'], ['error'], interval, timeout)
