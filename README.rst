OPENSTACK ACCOUNT SETUP
========================
Easily create projects, quotas, security groups, images and keypairs for users using a config file.

Install
-------

.. code::

    $ git clone https://github.com/tylernorth/OpenStack-Account-Setup.git
    $ pip install OpenStack-Account-Setup

Command Line
-------------

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

Python Scripting
----------------

.. code::

    >>> from openstack_account import AccountSetup
    >>> help(AccountSetup)
