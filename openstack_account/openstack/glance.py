from openstack_account import settings
from openstack_account import utils

import logging

log = logging.getLogger(__name__)

def find_image(glance, name):
    for im in glance.images.list():
        if im.name == name:
            return im
    return None

def create_image(glance, **args):
    log.debug('Creating image:%s' % args)
    wait = args.pop('wait', settings.IMAGE_WAIT)
    timeout = args.pop('timeout', settings.IMAGE_WAIT_TIMEOUT)
    interval = args.pop('wait_interval', settings.IMAGE_WAIT_INTERVAL)
    # By default use glance that already exists
    image_name = args.get('name', None)
    image = find_image(glance, image_name)
    if image:
        log.info('Image exists:%s' % image.id)
        return
    file_location = args.pop('file', None)
    image = glance.images.create(**args)
    if file_location:
        image.update(data=open(file_location, 'rb'))
    log.info('Created image:%s' % image.id)
    if wait:
        log.info('Waiting for image:%s' % image.id)
        utils.wait_status(glance.images.get, image.id, ['active'],
                          ['error'], interval, timeout)
