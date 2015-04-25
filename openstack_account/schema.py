SCHEMA = {
    "title": "accounts",
    "type": "array",
    "items": {
        "title": "account",
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
            "flavors": {
                "title": "flavors",
                "type": "array",
                "items": {
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
                }
            },
            "nova_quotas": {
                "title": "nova_quotas",
                "type": "array",
                "items": {
                    "title": "nova_quota",
                    "type": "object",
                    "properties": {
                        "tenant_name": {
                            "type": "string"
                        }
                    },
                    "required": ["tenant_name"],
                    "additionalProperties" : True
                }
            },
            "keypairs": {
                "title": "keypairs",
                "type": "array",
                "items": {
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
                }
            },
            "cinder_quotas": {
                "title": "cinder_quotas",
                "type": "array",
                "items": {
                    "title": "cinder_quota",
                    "type": "object",
                    "properties": {
                        "tenant_name": {
                            "type": "string"
                        }
                    },
                    "required": ["tenant_name"],
                    "additionalProperties" : True
                }
            },
            "security_groups": {
                "title": "security_groups",
                "type": "array",
                "items": {
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
                        "tenant_name": {
                            "type": "string"
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
                }
            },
            "users": {
                "title": "users",
                "type": "array",
                "items": {
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
                }
            },
            "source_files": {
                "title": "source_files",
                "type": "array",
                "items": {
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
                }
            },
            "images": {
                "type": "array",
                "title": "images",
                "items": {
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
                            "type": "boolean"
                        },
                        "timeout": {
                            "type": "integer"
                        },
                        "wait_interval": {
                            "type": "integer"
                        }
                    },
                    "required": [
                        "disk_format",
                        "container_format",
                        "name"
                    ],
                    "additionalProperties" : True
                },
            },
            "projects": {
                "title": "projects",
                "type": "array",
                "items": {
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
                }
            },
            "networks": {
                "title": "networks",
                "type": "array",
                "items": {
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
                }
            },
            "subnets": {
                "title": "subnets",
                "type": "array",
                "items": {
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
                }
            },
            "routers": {
                "title": "routers",
                "type": "array",
                "items": {
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
                    "requires": ["name"],
                    "additionalProperties" : True
                }
            }
        },
        "routers": {
            "title": "routers",
            "type": "array",
            "items": {
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
                "requires": ["name"]
            }
        }
    }
}
