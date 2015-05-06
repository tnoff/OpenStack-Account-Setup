#######################
OPENSTACK ACCOUNT SETUP
#######################
Deploy resources on an OpenStack cluster based on a config file.

Current supported modules:

- Keystone users
- Keystone projects
- Keystone roles
- Glance images
- Nova security groups
- Nova keypairs
- OpenStack source RC files
- Nova quotas
- Cinder quotas
- Neutron networks
- Neutron subnets
- Neutron routers
- Cinder volumes
- Nova instances

=======
Install
=======
.. code::

    $ git clone https://github.com/tylernorth/OpenStack-Account-Setup.git
    $ pip install OpenStack-Account-Setup

============
Command Line
============
.. code::

    $ os-account --help
    usage: os-account [-h] [--username USERNAME] [--password PASSWORD]
                      [--tenant-name TENANT_NAME] [--auth-url AUTH_URL]
                      config_file

    Create & Setup OpenStack Accounts

    positional arguments:
      config_file           Config file to use

    optional arguments:
      -h, --help            show this help message and exit
      --username USERNAME   OpenStack Auth username
      --password PASSWORD   OpenStack Auth password
      --tenant-name TENANT_NAME
                            OpenStack Auth tenant name
      --auth-url AUTH_URL   OpenStack Auth keystone url

================
Python Scripting
================
.. code::

    >>> from openstack_account.client import AccountSetup
    >>> help(AccountSetup)

=============
Sample Config
=============
See sample config YAML file
