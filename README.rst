###################
OpenStack Portation
###################
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
- OpenStack source RC files ( import only )
- Nova quotas
- Cinder quotas
- Neutron networks
- Neutron subnets
- Neutron routers
- Cinder volumes ( import only )
- Nova instances ( import only )

=======
Install
=======
.. code::

    $ git clone https://github.com/tnoff/OpenStack-Portation.git
    $ pip install OpenStack-Portaiton/

============
Command Line
============
.. code::

    usage: openstack-portation [-h] [--username USERNAME] [--password PASSWORD]
                               [--tenant-name TENANT_NAME] [--auth-url AUTH_URL]
                               [--debug]
                               {import,export} ...

    Import and export Openstack resources

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

    >>> from openstack_portation.client import PortationClient
    >>> help(PortationClient)

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

Also support resource data:

- images

=======
Testing
=======
Functional tests for import/export of basic configs.

Options for tests are defined in ``tests/settings.py`` and can be overriden
with the ``tests/override_settings.py`` file.
