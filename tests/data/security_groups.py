DATA = [
    {
        "projects": [
            {
                "name": "winterfell",
            },
        ],
    },
    {
        "security_groups": [
            {
                "rules": [
                    {
                        "to_port": 22,
                        "cidr": "0.0.0.0/0",
                        "from_port": 22,
                        "ip_protocol": "tcp"
                    }
                ],
                "tenant_name": "winterfell",
                "name": "ssh",
                "description": "Simply ssh port group"
            }
        ]
    },
]
