from openstack_account import settings
from openstack_account import utils
from openstack_account.exceptions import OpenStackAccountError

import logging

log = logging.getLogger(__name__)

def set_cinder_quota(cinder, keystone, **args):
    log.debug('Setting cinder quotas:%s' % args)
    tenant_name = args.pop('tenant_name', None)
    project = utils.find_project(keystone, tenant_name)
    if not project:
        raise OpenStackAccountError("Cannot find project:%s" % tenant_name)
    cinder.quotas.update(project.id, **args)
    log.info("Updated cinder quotas for project:%s" % project.id)
    return {'cinder_quota' : project.id}

def create_volume(cinder, nova, **args):
    log.debug('Create volume:%s' % args)
    name = args.pop('name', None)
    wait = args.pop('wait', settings.VOLUME_WAIT)
    timeout = args.pop('timeout', settings.VOLUME_WAIT_TIMEOUT)
    interval = args.pop('interval', settings.VOLUME_WAIT_INTERVAL)
    volume = utils.find_volume(cinder, name)
    # Cinder uses 'display_name' for some dumb reason
    args['display_name'] = name

    image_name = args.pop('image_name', None)
    if image_name:
        image = utils.find_image(nova, image_name)
        args['imageRef'] = image.id
    if volume:
        log.info('Volume already exists:%s' % volume.id)
    else:
        volume = cinder.volumes.create(**args)
        log.info('Volume created:%s' % volume.id)
    if wait:
        log.info('Waiting for volume:%s, timeout:%s' % (volume.id, timeout))
        utils.wait_status(cinder.volumes.get, volume.id,
                          ['available'], ['error'], interval, timeout)
    return {'volume' : volume.id}

def save_quotas(cinder, tenant):
    quotas = cinder.quotas.get(tenant.id)
    quota_args = vars(quotas)
    for key in quota_args.keys():
        if key in settings.EXPORT_KEYS_IGNORE:
            quota_args.pop(key)
    quota_args['tenant_name'] = str(tenant.name)
    return {'cinder_quota' : quota_args}
