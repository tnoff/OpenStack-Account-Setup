DATA = [
    {
        "project": {
            "name": "winterfell",
        }
    },
    {
        "network": {
            "tenant_name": "winterfell",
            "name": "the north",
            "shared": True,
        }
    },
    {
        "subnet": {
            "ip_version": "4",
            "tenant_name": "winterfell",
            "cidr": "192.168.0.0/24",
            "name": "moat cailin",
            "network": "the north"
        }
    },
    {
        "router": {
            "tenant_name": "winterfell",
            "external_network": "external",
            "name": "the kingsroad",
            "internal_subnet": "moat cailin"
        }
    },
]
