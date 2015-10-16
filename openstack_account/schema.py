from openstack_account import settings

SCHEMA = {
    "title": "actions",
    "type": "array",
    "items": {
        "title": "action",
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "os_username": {
                "type": "string"
            },
            "os_password": {
                "type": "string"
            },
            "os_tenant_name": {
                "type": "string"
            },
            "os_auth_url": {
                "type": "string"
            },
            "flavor": {
                "title": "flavor",
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
                "required": [
                    "name",
                    "disk",
                    "vcpus",
                    "ram"
                ],
                "additionalProperties" : True
            },
            "nova_quota": {
                "title": "nova_quota",
                "type": "object",
                "properties": {
                    "tenant_name": {
                        "type": "string"
                    }
                },
                "required": ["tenant_name"],
                "additionalProperties" : True
            },
            "keypair": {
                "title": "keypair",
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string"
                    },
                    "user": {
                        "title": "user",
                        "type": "object",
                        "properties": {
                            "name": {
                                "type" : "string"
                            },
                            "password": {
                                "type" : "string"
                            }
                        },
                        "required": ["name", "password"]
                    },
                    "file": {
                        "type": "string"
                    }
                },
                "required": ["name"]
            },
            "cinder_quota": {
                "title": "cinder_quota",
                "type": "object",
                "properties": {
                    "tenant_name": {
                        "type": "string"
                    }
                },
                "required": ["tenant_name"],
                "additionalProperties" : True
            },
            "security_group": {
                "title": "security_group",
                "type": "object",
                "properties": {
                    "rules": {
                        "title": "rules",
                        "type": "array",
                        "items": {
                            "title": "rule",
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
                        },
                    },
                    "name": {
                        "type": "string"
                    },
                    "description": {
                        "type": ["string", "null"]
                    }
                },
                "required": ["name", "description"],
                "additionalProperties" : True
            },
            "user": {
                "title": "user",
                "type": "object",
                "properties": {
                    "password": {
                        "type": "string"
                    },
                    "name": {
                        "type": "string"
                    },
                    "email": {
                        "type": ["string", "null"]
                    }
                },
                "required": ["name", "password"]
            },
            "source_file": {
                "title": "source_file",
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
                "required": ["tenant_name", "file", "user"]
            },
            "image": {
                "title": "image",
                "type": "object",
                "properties": {
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
                        "type": "boolean",
                        "default": settings.IMAGE_WAIT
                    },
                    "timeout": {
                        "type": "integer",
                        "default": settings.IMAGE_WAIT_TIMEOUT
                    },
                    "wait_interval": {
                        "type": "integer",
                        "default": settings.IMAGE_WAIT_INTERVAL
                    }
                },
                "required": [
                    "disk_format",
                    "container_format",
                    "name"
                ],
                "additionalProperties" : True
            },
            "project": {
                "title": "project",
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
                "required": ["name"]
            },
            "network": {
                "title": "network",
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string"
                    },
                    "tenant_name": {
                        "type": "string"
                    }
                },
                "required": ["name"],
                "additionalProperties" : True
            },
            "subnet": {
                "title": "subnet",
                "type": "object",
                "properties": {
                    "name" : {
                        "type": "string"
                    },
                    "network": {
                        "type": "string"
                    },
                    "cidr": {
                        "type": "string"
                    },
                    "ip_version": {
                        "type": "string"
                    },
                    "tenant_name": {
                        "type": "string"
                    }
                },
                "required": ["name", "network", "cidr", "ip_version"],
                "additionalProperties" : True
            },
            "router": {
                "title": "router",
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string"
                    },
                    "external_network": {
                        "type": "string"
                    },
                    "internal_subnet": {
                        "type": "string"
                    },
                    "tenant_name": {
                        "type": "string"
                    }
                },
                "required": ["name"],
                "additionalProperties" : True
            },
            "volume": {
                "title": "volume",
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string"
                    },
                    "size": {
                        "type": "integer"
                    },
                    "image_name": {
                        "type": "string"
                    },
                    "wait": {
                        "type": "boolean",
                        "default": settings.VOLUME_WAIT
                    },
                    "timeout": {
                        "type": "integer",
                        "default": settings.VOLUME_WAIT_TIMEOUT
                    },
                    "wait_interval": {
                        "type": "integer",
                        "default": settings.VOLUME_WAIT_INTERVAL
                    }
                },
                "required": ["name", "size"],
                "additionalProperties": True
            },
            "server": {
                "title": "server",
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string"
                    },
                    "flavor_name": {
                        "type": "string"
                    },
                    "flavor": {
                        "type": "string"
                    },
                    "image_name": {
                        "type": "string"
                    },
                    "image": {
                        "type": "string"
                    },
                    "nics": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "network_name": {
                                    "type": "string"
                                }
                            },
                            "required": ["network_name"],
                            "additionalProperties": True
                        }
                    },
                    "volumes": {
                        "type" : "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "volume_name": {
                                    "type": "string"
                                },
                                "device_name": {
                                    "type": "string"
                                },
                                "terminate_on_delete": {
                                    "type": "boolean"
                                }
                            },
                            "required": ["volume_name", "device_name"],
                            "additionalProperties": False
                        }
                    },
                    "wait": {
                        "type": "boolean",
                        "default": settings.SERVER_WAIT
                    },
                    "timeout": {
                        "type": "integer",
                        "default": settings.SERVER_WAIT_TIMEOUT
                    },
                    "wait_interval": {
                        "type": "integer",
                        "default": settings.SERVER_WAIT_INTERVAL
                    }
                },
                "required": ["name"],
                "additionalProperties": True
            }
        }
    }
}
