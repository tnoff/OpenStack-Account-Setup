from openstack_portation import settings
from openstack_portation import utils

import logging
import os

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
    return {'image' : image.id}

def save_image_meta(glance, keystone, image):
    log.info("Saving image:%s metadata" % image.id)
    image = glance.images.get(image.id)
    image_dict = vars(image)
    for key in settings.EXPORT_KEYS_IGNORE:
        image_dict.pop(key, None)
    # identify owner as tenant id
    owner = '%s' % image_dict.pop('owner')
    tenant = keystone.tenants.get(owner)
    image_dict['tenant_name'] = tenant.name
    return {'image' : image_dict}

def save_image_data(glance, image, save_directory):
    log.info("Saving image:%s data to dir:%s" % (image.id, save_directory))
    image_name = 'image-%s-%s' % (image.name, image.id)
    image_path = os.path.join(save_directory, image_name)
    with open(image_path, 'wb') as write_file:
        for chunk in glance.images.data(image.id):
            write_file.write(chunk)
