#!/usr/bin/env python
import setuptools

VERSION = '0.14'

setuptools.setup(
    author='Tyler Daniel North',
    author_email='tylernorth18@gmail.com',
    description='OpenStack Account Setup Script',
    install_requires=[
        'python-cinderclient >= 1.0.9',
        'python-glanceclient >= 0.13.1',
        'python-keystoneclient >= 0.10.1',
        'python-neutronclient>=2.3.11',
        'python-novaclient >= 2.18.1',

        'nose >= 1.3.7',
        'pycrypto >= 2.6.1',
        'PyYAML >= 3.11',
    ],
    entry_points={
        'console_scripts' : [
            'openstack-account = scripts.cli:main',
        ]
    },
    packages=setuptools.find_packages(),
    name='openstack_account',
    version=VERSION,
)
