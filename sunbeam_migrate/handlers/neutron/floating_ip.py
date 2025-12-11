# SPDX-FileCopyrightText: 2025 - Canonical Ltd
# SPDX-License-Identifier: Apache-2.0

import ipaddress
import logging

from sunbeam_migrate import config, exception
from sunbeam_migrate.handlers import base

CONF = config.get_config()
LOG = logging.getLogger()


class FloatingIPHandler(base.BaseMigrationHandler):
    """Handle Neutron floating IP migrations."""

    def get_service_type(self) -> str:
        """Get the service type for this type of resource."""
        return "neutron"

    def get_supported_resource_filters(self) -> list[str]:
        """Get a list of supported resource filters.

        These filters can be specified when initiating batch migrations.
        """
        return ["owner_id"]

    def get_associated_resource_types(self) -> list[str]:
        """Get a list of associated resource types.

        Associated resources must be migrated first.
        """
        return ["network", "subnet"]

    def get_associated_resources(self, resource_id: str) -> list[tuple[str, str]]:
        """Return the network and subnet this floating IP depends on."""
        source_fip = self._source_session.network.get_ip(resource_id)
        if not source_fip:
            raise exception.NotFound(f"Floating IP not found: {resource_id}")

        associated_resources = []
        floating_network_id = source_fip.floating_network_id
        if floating_network_id:
            associated_resources.append(("network", floating_network_id))

        subnet_ids = set()
        if getattr(source_fip, "subnet_id", None):
            subnet_ids.add(source_fip.subnet_id)

        floating_ip = getattr(source_fip, "floating_ip_address", None)
        if floating_ip:
            try:
                floating_ip_addr = ipaddress.ip_address(floating_ip)
            except ValueError:
                LOG.error("Unable to parse FIP address: %s", floating_ip)
                floating_ip_addr = None

        if floating_ip_addr:
            for subnet in self._source_session.network.subnets(
                network_id=floating_network_id
            ):
                cidr = getattr(subnet, "cidr", None)
                if not cidr:
                    continue
                try:
                    network = ipaddress.ip_network(cidr, strict=False)
                except ValueError:
                    continue

                if floating_ip_addr in network:
                    # The Floating IP might not have a subnet_id set,
                    # but requires a subnet based on the IP address.
                    subnet_ids.add(subnet.id)
                    break
                else:
                    LOG.warning(
                        "Unable to find subnet for floating IP %s in network %s",
                        floating_ip,
                        floating_network_id,
                    )

        for subnet_id in sorted(subnet_ids):
            associated_resources.append(("subnet", subnet_id))
        return associated_resources

    def get_member_resource_types(self) -> list[str]:
        """Get a list of member (contained) resource types.

        The migrations can cascade to contained resources.
        """
        return []

    def perform_individual_migration(
        self,
        resource_id: str,
        migrated_associated_resources: list[tuple[str, str, str]],
    ) -> str:
        """Migrate the specified floating IP.

        :param resource_id: the resource to be migrated
        :param migrated_associated_resources: a list of tuples describing
            associated resources that have already been migrated.
            Format: (resource_type, source_id, destination_id)

        Return the resulting resource id.
        """
        source_fip = self._source_session.network.get_ip(resource_id)
        if not source_fip:
            raise exception.NotFound(f"Floating IP not found: {resource_id}")

        destination_network_id = self._get_associated_resource_destination_id(
            "network",
            source_fip.floating_network_id,
            migrated_associated_resources,
        )

        dest_subnet_id = None
        if source_fip.subnet_id:
            dest_subnet_id = self._get_associated_resource_destination_id(
                "subnet",
                source_fip.subnet_id,
                migrated_associated_resources,
            )

        fields = [
            "description",
            "dns_domain",
            "dns_name",
            "floating_ip_address",
        ]
        kwargs = {}
        for field in fields:
            value = getattr(source_fip, field, None)
            if value is not None:
                kwargs[field] = value

        kwargs["floating_network_id"] = destination_network_id
        if dest_subnet_id:
            kwargs["subnet_id"] = dest_subnet_id

        destination_fip = self._destination_session.network.create_ip(**kwargs)
        return destination_fip.id

    def get_source_resource_ids(self, resource_filters: dict[str, str]) -> list[str]:
        """Returns a list of resource ids based on the specified filters.

        Raises an exception if any of the filters are unsupported.
        """
        self._validate_resource_filters(resource_filters)

        query_filters = {}
        if "owner_id" in resource_filters:
            query_filters["project_id"] = resource_filters["owner_id"]

        resource_ids = []
        for resource in self._source_session.network.ips(**query_filters):
            resource_ids.append(resource.id)

        return resource_ids

    def _delete_resource(self, resource_id: str, openstack_session):
        openstack_session.network.delete_ip(resource_id, ignore_missing=True)
