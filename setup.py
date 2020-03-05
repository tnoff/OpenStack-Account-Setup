#!/usr/bin/env python
import setuptools

VERSION = '1.2'

setuptools.setup(
    author='Tyler Daniel North',
    author_email='ty_north@yahoo.com',
    description='OpenStack Account Setup Script',
    install_requires=[
        'python-cinderclient',
        'python-glanceclient',
        'python-keystoneclient',
        'python-neutronclient',
        'python-novaclient',

        'nose >= 1.3.7',
        'pycrypto >= 2.6.1',
        'PyYAML >= 3.11',
    ],
    entry_points={
        'console_scripts' : [
            'openstack-portation= scripts.cli:main',
        ]
    },
    packages=setuptools.find_packages(),
    name='openstack_portation',
    version=VERSION,
)
