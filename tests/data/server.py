DATA = [
    {
        "networks": [
            {
                "name": "test-network",
            }
        ]
    },
    {
        "subnets": [
            {
                "ip_version": "4",
                "cidr": "10.10.0.1/24",
                "name": "test-subnet",
                "network": "test-network"
            }
        ]
    },
    {
        "images": [
            {
                "name": "cirros test",
                "container_format": "bare",
                "disk_format": "qcow2",
                "copy_from": "http://cloudhyd.com/openstack/images/cirros-0.3.0-x86_64-disk.img",
                "is_public": False,
                "wait": True,
            }
        ]
    },
    {
        "flavors": [
            {
                "vcpus": 4,
                "disk": 0,
                "ram": 4096,
                "name": "kraken"
            }
        ]
    },
    {
        "servers": [
            {
                "flavor_name": "kraken",
                "timeout": 1200,
                "image_name": "cirros test",
                "name": "ice",
                "wait": False,
                "nics": [{
                    "network_name": "test-network",
                }]
            }
        ]
    }
]
