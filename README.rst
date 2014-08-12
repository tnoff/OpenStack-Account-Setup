OPENSTACK ACCOUNT SETUP
========================

Easily create projects, quotas, security groups, images and keypairs for users using a config file.

The command line tools requires a yml file, but the python script module only requires a json object.

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

Sample Config
--------------

.. code::

    - user:
            name: 'arya'
            password: 'joffrey_sucks'
            email: None
      projects:
        - name: 'winterfell'
          description: 'winter is coming'
          role: '_member_'
      flavors:
        - name: 'biggie smalls'
          ram: 4096
          vcpus: 4
          disk: 0
      nova_quotas:
        - tenant_name: 'winterfell'
          instances: 20
      cinder_quotas:
        - tenant_name: 'winterfell'
          volumes: 20
      security_groups:
        - name: 'ssh port'
          description: Simply ssh port group
          tenant_name: 'winterfell'
          rules:
            - from_port: 22
              to_port: 22
              ip_protocol: 'tcp'
              cidr: '0.0.0.0/0'
      keypairs:
        - name: 'my-public-key'
          file: '/home/user/.ssh/id_rsa.pub'
      source_files:
        - tenant_name: 'winterfell'
          file: '/home/user/arya_openrc.sh'
      images:
        - tenant_name: 'winterfell'
          copy_from: 'http://www.change-me.org/debian-7.3.img'
          container_format: 'bare'
          disk_format: 'qcow2'
          is_public: False
