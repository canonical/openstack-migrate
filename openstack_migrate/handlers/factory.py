# SPDX-FileCopyrightText: 2025 - Canonical Ltd
# SPDX-License-Identifier: Apache-2.0

import importlib

from openstack_migrate import exception
from openstack_migrate.handlers import base

MIGRATION_HANDLERS = {
    # Barbican handlers
    "secret": "openstack_migrate.handlers.barbican.secret.SecretHandler",
    "secret-container": "openstack_migrate.handlers.barbican.secret_container.SecretContainerHandler",
    # Cinder handles
    "volume": "openstack_migrate.handlers.cinder.volume.VolumeHandler",
    "volume-type": "openstack_migrate.handlers.cinder.volume_type.VolumeTypeHandler",
    # Designate handlers
    "dns-zone": "openstack_migrate.handlers.designate.zone.ZoneHandler",
    # Glance handlers
    "image": "openstack_migrate.handlers.glance.image.ImageHandler",
    # Keystone handlers
    "domain": "openstack_migrate.handlers.keystone.domain.DomainHandler",
    "project": "openstack_migrate.handlers.keystone.project.ProjectHandler",
    "role": "openstack_migrate.handlers.keystone.role.RoleHandler",
    "user": "openstack_migrate.handlers.keystone.user.UserHandler",
    # Manila handlers
    "share": "openstack_migrate.handlers.manila.share.ShareHandler",
    "share-type": "openstack_migrate.handlers.manila.share_type.ShareTypeHandler",
    # Nova handlers
    "flavor": "openstack_migrate.handlers.nova.flavor.FlavorHandler",
    "instance": "openstack_migrate.handlers.nova.instance.InstanceHandler",
    "keypair": "openstack_migrate.handlers.nova.keypair.KeypairHandler",
    # Neutron handlers
    "floating-ip": "openstack_migrate.handlers.neutron.floating_ip.FloatingIPHandler",
    "router": "openstack_migrate.handlers.neutron.router.RouterHandler",
    "network": "openstack_migrate.handlers.neutron.network.NetworkHandler",
    "subnet": "openstack_migrate.handlers.neutron.subnet.SubnetHandler",
    "port": "openstack_migrate.handlers.neutron.port.PortHandler",
    "security-group": "openstack_migrate.handlers.neutron.security_group.SecurityGroupHandler",
    "security-group-rule": "openstack_migrate.handlers.neutron.security_group_rule.SecurityGroupRuleHandler",
    # Octavia handlers
    "load-balancer": "openstack_migrate.handlers.octavia.load_balancer.LoadBalancerHandler",
}


def get_migration_handler(resource_type: str | None) -> base.BaseMigrationHandler:
    """Get the migration handler for the given resource type."""
    if not resource_type:
        raise exception.InvalidInput("No resource type specified.")
    if resource_type not in MIGRATION_HANDLERS:
        raise exception.InvalidInput("Unsupported resource type: %s" % resource_type)

    module_name, class_name = MIGRATION_HANDLERS[resource_type].rsplit(".", 1)
    module = importlib.import_module(module_name)
    cls = getattr(module, class_name)
    return cls()


def get_all_handlers() -> dict[str, base.BaseMigrationHandler]:
    """Get instances of all the supported resource handlers."""
    handlers: dict[str, base.BaseMigrationHandler] = {}
    for resource_type in MIGRATION_HANDLERS:
        handlers[resource_type] = get_migration_handler(resource_type)
    return handlers
