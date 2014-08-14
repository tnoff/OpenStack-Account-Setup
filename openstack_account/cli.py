#!/usr/bin/env python
from __init__ import AccountSetup
import argparse
import logging
import os
import sys
import yaml

log_format = '%(asctime)s-%(levelname)s-%(message)s'
log = logging.getLogger('openstack_account')
log.setLevel(logging.DEBUG)
handle = logging.StreamHandler()
handle.setLevel(logging.DEBUG)
form = logging.Formatter(log_format)
handle.setFormatter(form)
log.addHandler(handle)

def parse_args():
    p = argparse.ArgumentParser(description='Create & Setup OpenStack Accounts')
    p.add_argument('--username', help='OpenStack Auth username')
    p.add_argument('--password', help='OpenStack Auth password')
    p.add_argument('--tenant-name', help='OpenStack Auth tenant name')
    p.add_argument('--auth-url', help='OpenStack Auth keystone url')
    p.add_argument('config_file', help='Config file to use')
    return p.parse_args()

def get_env_args(args):
    # Check environment for variables if not set on command line
    if not args['username']:
        args['username'] = os.getenv('OS_USERNAME', None)
    if not args['password']:
        args['password'] = os.getenv('OS_PASSWORD', None)
    if not args['tenant_name']:
        args['tenant_name'] = os.getenv('OS_TENANT_NAME', None)
    if not args['auth_url']:
        args['auth_url'] = os.getenv('OS_AUTH_URL', None)
    must_have = ['username', 'password', 'tenant_name', 'auth_url']
    for item in must_have:
        if args[item] == None:
            log.error('Need arg:%s' % item)
            sys.exit('')
    return args

def main():
    args = vars(parse_args())
    log.debug('Reading CLI args')
    args = get_env_args(args)
    log.debug('Initialzing Account Setup')
    a = AccountSetup(args['username'],
                     args['password'],
                     args['tenant_name'],
                     args['auth_url'])
    with open(args['config_file'], 'r') as f:
        log.debug('Loading config from:%s' % args['config_file'])
        data = yaml.load(f)
        for account in data:
            a.setup_config(account)

if __name__ == '__main__':
    main()
