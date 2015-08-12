from openstack_account import settings
from openstack_account import utils

import logging

log = logging.getLogger(__name__)

def create_image(glance, **args):
    log.debug('Creating image:%s' % args)
    wait = args.pop('wait', settings.IMAGE_WAIT)
    timeout = args.pop('timeout', settings.IMAGE_WAIT_TIMEOUT)
    interval = args.pop('wait_interval', settings.IMAGE_WAIT_INTERVAL)
    # By default use glance that already exists
    image_name = args.get('name', None)
    file_location = args.pop('file', None)
    image = utils.find_image(glance, image_name)
    if image:
        # update image data
        args.pop('copy_from', None)
        glance.images.update(image.id, **args)
        log.info('Updated image:%s' % image.id)
    else:
        image = glance.images.create(**args)
        log.info('Created image:%s' % image.id)
        if file_location:
            log.info('Updating data for image:%s' % image.id)
            image.update(data=open(file_location, 'rb'))
    if wait:
        log.info('Waiting for image:%s, timeout:%s' % (image.id, timeout))
        utils.wait_status(glance.images.get, image.id, ['active'],
                          ['error'], interval, timeout)
    return image.id
