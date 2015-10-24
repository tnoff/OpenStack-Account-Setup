#######################
OPENSTACK ACCOUNT SETUP
#######################
Import or export resources from an OpenStack cluster. Client allows passing
of any valid JSON (validity based on schema) into the python client, all CLI
calls use YAML.

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

    usage: openstack-account [-h] [--username USERNAME] [--password PASSWORD]
                             [--tenant-name TENANT_NAME] [--auth-url AUTH_URL]
                             [--debug]
                             {import,export} ...

    Create & Setup OpenStack Accounts

    positional arguments:
      {import,export}       Command
        import              Import config
        export              Export config

    optional arguments:
      -h, --help            show this help message and exit
      --username USERNAME   OpenStack Auth username
      --password PASSWORD   OpenStack Auth password
      --tenant-name TENANT_NAME
                            OpenStack Auth tenant name
      --auth-url AUTH_URL   OpenStack Auth keystone url
      --debug               Show debug output

================
Python Scripting
================
.. code::

    >>> from openstack_account.client import AccountSetup
    >>> help(AccountSetup)

====================
Sample Import Config
====================
See sample config YAML file

=============
Export Config
=============
Exported configs will be JSON objects, with CLI this will be written to a
YAML file.

Currently only supports "metadata" such as:

- users
- projects
- roles
- flavors
- quotas
- security groups

=======
Testing
=======
Functional tests for import/export of basic configs.

Use ``tests/settings.py`` to specify which cluster to use. Neutron should
be installed on the cluster for tests to pass.
