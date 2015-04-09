SCHEMA = {
    "type": "object",
    "properties": {
        "flavors": {
            "items": {
                "required": [
                    "name",
                    "disk",
                    "vcpus",
                    "ram"
                ],
                "type": "object",
                "properties": {
                    "vcpus": {
                        "type": "number"
                    },
                    "disk": {
                        "type": "number"
                    },
                    "ram": {
                        "type": "number"
                    },
                    "name": {
                        "type": "string"
                    }
                },
                "title": "flavor"
            },
            "type": "array",
            "title": "flavors"
        },
        "nova_quotas": {
            "items": {
                "required": [
                    "tenant_name"
                ],
                "type": "object",
                "properties": {
                    "tenant_name": {
                        "type": "string"
                    }
                },
                "title": "nova_quota"
            },
            "type": "array",
            "title": "nova_quotas"
        },
        "keypairs": {
            "items": {
                "required": [
                    "name"
                ],
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string"
                    },
                    "user": {
                        "type": "string"
                    },
                    "user_password": {
                        "type": "string"
                    },
                    "file": {
                        "type": "string"
                    }
                },
                "title": "keypair"
            },
            "type": "array",
            "title": "keypairs"
        },
        "cinder_quotas": {
            "items": {
                "required": [
                    "tenant_name"
                ],
                "type": "object",
                "properties": {
                    "tenant_name": {
                        "type": "string"
                    }
                },
                "title": "cinder_quota"
            },
            "type": "array",
            "title": "cinder_quotas"
        },
        "security_groups": {
            "items": {
                "required": [
                    "name",
                    "description",
                    "tenant_name"
                ],
                "type": "object",
                "properties": {
                    "rules": {
                        "items": {
                            "type": "object",
                            "properties": {
                                "to_port": {
                                    "type": "number"
                                },
                                "cidr": {
                                    "type": "string"
                                },
                                "from_port": {
                                    "type": "number"
                                },
                                "ip_protocol": {
                                    "type": "string"
                                }
                            },
                            "title": "rule"
                        },
                        "type": "array"
                    },
                    "tenant_name": {
                        "type": "string"
                    },
                    "name": {
                        "type": "string"
                    },
                    "description": {
                        "type": [
                            "string",
                            "null"
                        ]
                    }
                },
                "title": "security_group"
            },
            "type": "array",
            "title": "security_groups"
        },
        "users": {
            "items": {
                "required": [
                    "name",
                    "password"
                ],
                "type": "object",
                "properties": {
                    "password": {
                        "type": "string"
                    },
                    "name": {
                        "type": "string"
                    },
                    "email": {
                        "type": [
                            "string",
                            "null"
                        ]
                    }
                },
            },
            "type": "array",
            "title": "user"
        },
        "source_files": {
            "items": {
                "required": [
                    "tenant_name",
                    "file",
                    "user"
                ],
                "type": "object",
                "properties": {
                    "user": {
                        "type": "string"
                    },
                    "tenant_name": {
                        "type": "string"
                    },
                    "file": {
                        "type": "string"
                    }
                },
                "title": "source_file"
            },
            "type": "array",
            "title": "source_files"
        },
        "images": {
            "items": {
                "required": [
                    "tenant_name",
                    "disk_format",
                    "container_format",
                    "name"
                ],
                "type": "object",
                "properties": {
                    "tenant_name": {
                        "type": "string"
                    },
                    "disk_format": {
                        "type": "string"
                    },
                    "name": {
                        "type": "string"
                    },
                    "container_format": {
                        "type": "string"
                    },
                    "wait": {
                        "type": "boolean"
                    },
                    "timeout": {
                        "type": "integer"
                    },
                    "wait_interval": {
                        "type": "integer"
                    }
                },
                "title": "image"
            },
            "type": "array",
            "title": "images"
        },
        "projects": {
            "items": {
                "required": [
                    "name"
                ],
                "type": "object",
                "properties": {
                    "role": {
                        "type": "string"
                    },
                    "user": {
                        "type": "string"
                    },
                    "name": {
                        "type": "string"
                    },
                    "description": {
                        "type": "string"
                    }
                },
                "title": "project"
            },
            "type": "array",
            "title": "projects"
        }
    },
    "additionalProperties": False,
    "title": "Account Setup Schema"
}
