# SPDX-FileCopyrightText: 2025 - Canonical Ltd
# SPDX-License-Identifier: Apache-2.0

import logging
from typing import Any

from sunbeam_migrate import config, exception
from sunbeam_migrate.handlers import base

CONF = config.get_config()
LOG = logging.getLogger(__name__)


class ZoneHandler(base.BaseMigrationHandler):
    """Handle Designate DNS zone migrations."""

    def get_service_type(self) -> str:
        """Get the service type for this type of resource."""
        return "designate"

    def get_supported_resource_filters(self) -> list[str]:
        """Get a list of supported resource filters.

        These filters can be specified when initiating batch migrations.
        """
        return ["project_id"]

    def get_associated_resource_types(self) -> list[str]:
        """DNS zones have no prerequisite resources."""
        types = []
        if CONF.multitenant_mode:
            types.append("project")
        return types

    def get_associated_resources(self, resource_id: str):
        """Get associated resources for the specified DNS zone."""
        source_zone = self._get_zone_all_projects(resource_id)
        if not source_zone:
            raise exception.NotFound(f"Zone not found: {resource_id}")

        associated_resources: list[base.Resource] = []
        self._report_identity_dependencies(
            associated_resources, project_id=source_zone.project_id
        )

        return associated_resources

    def get_member_resource_types(self) -> list[str]:
        """DNS zones do not expose member resources via the migration manager."""
        return []

    def perform_individual_migration(
        self,
        resource_id: str,
        migrated_associated_resources: list[base.MigratedResource],
    ) -> str:
        """Migrate the specified DNS zone by copying zone and recordsets."""
        source_zone = self._get_zone_all_projects(resource_id)
        if not source_zone:
            raise exception.NotFound(f"Zone not found: {resource_id}")

        # Check for existing zone using owner-scoped session if in multi-tenant mode
        identity_kwargs = self._get_identity_build_kwargs(
            migrated_associated_resources,
            source_project_id=source_zone.project_id,
        )
        if CONF.multitenant_mode:
            owner_destination_session = self._owner_scoped_session(
                self._destination_session,
                [CONF.member_role_name],
                identity_kwargs["project_id"],
            )
        else:
            owner_destination_session = self._destination_session

        existing = owner_destination_session.dns.find_zone(
            source_zone.name, ignore_missing=True
        )
        if existing:
            LOG.info(
                "Zone %s already exists on destination (id: %s), skipping migration",
                source_zone.name,
                existing.id,
            )
            return existing.id

        # Create zone on destination
        dest_zone = self._create_destination_zone(
            source_zone, migrated_associated_resources
        )

        # Copy all recordsets from source to destination
        self._copy_recordsets(
            resource_id,
            dest_zone.id,
            migrated_associated_resources,
            source_zone.project_id,
        )

        return dest_zone.id

    def get_source_resource_ids(self, resource_filters: dict[str, str]) -> list[str]:
        """Returns a list of resource ids based on the specified filters.

        Raises an exception if any of the filters are unsupported.
        """
        self._validate_resource_filters(resource_filters)

        query_filters: dict[str, str | bool] = {}
        if "project_id" in resource_filters:
            query_filters["project_id"] = resource_filters["project_id"]
            # Designate uses all_projects instead of all_tenants
            query_filters["all_projects"] = True

        resource_ids = []
        for resource in self._source_session.dns.zones(**query_filters):
            resource_ids.append(resource.id)

        return resource_ids

    def _get_zone_all_projects(self, zone_id: str):
        """Get a zone by ID across all projects.

        The get_zone() method is project-scoped and won't find zones
        belonging to other projects, even with an admin session.
        The zones() list method doesn't support filtering by ID, so we
        need to list all zones and filter in Python.

        Note: Designate uses 'all_projects=True' (not 'all_tenants') when
        listing zones across projects.
        """
        for zone in self._source_session.dns.zones(all_projects=True):
            if zone.id == zone_id:
                return zone
        return None

    def delete_source_resource(self, resource_id: str):
        """Delete the specified zone on the source cloud side.

        In multi-tenant mode, we need to use a project-scoped session
        to delete zones belonging to other projects.
        """
        if CONF.multitenant_mode:
            # Get the zone to find its project
            source_zone = self._get_zone_all_projects(resource_id)
            if not source_zone:
                LOG.warning("Zone %s not found, cannot delete", resource_id)
                return

            # Create owner-scoped session for deletion
            source_session = self._owner_scoped_session(
                self._source_session,
                [CONF.member_role_name],
                source_zone.project_id,
            )
            source_session.dns.delete_zone(resource_id, ignore_missing=True)
        else:
            self._delete_resource(resource_id, self._source_session)

    def _delete_resource(self, resource_id: str, openstack_session):
        openstack_session.dns.delete_zone(resource_id, ignore_missing=True)

    def _create_destination_zone(
        self,
        source_zone: Any,
        migrated_associated_resources: list[base.MigratedResource],
    ) -> Any:
        """Create a zone on the destination cloud based on source zone properties."""
        LOG.info("Creating zone %s on destination", source_zone.name)

        fields = [
            "description",
            "email",
            "name",
            "ttl",
            "type",
            "is_shared",
        ]

        zone_attrs = {}
        for field in fields:
            value = getattr(source_zone, field, None)
            if value:
                zone_attrs[field] = value

        # Use owner-scoped session if in multi-tenant mode
        # The session scope determines ownership, not project_id in kwargs
        if CONF.multitenant_mode:
            identity_kwargs = self._get_identity_build_kwargs(
                migrated_associated_resources,
                source_project_id=source_zone.project_id,
            )
            dest_session = self._owner_scoped_session(
                self._destination_session,
                [CONF.member_role_name],
                identity_kwargs["project_id"],
            )
        else:
            dest_session = self._destination_session

        dest_zone = dest_session.dns.create_zone(**zone_attrs)
        LOG.info(
            "Created zone %s on destination (id: %s)", dest_zone.name, dest_zone.id
        )
        return dest_zone

    def _copy_recordsets(
        self,
        source_zone_id: str,
        dest_zone_id: str,
        migrated_associated_resources: list[base.MigratedResource],
        source_project_id: str,
    ):
        """Copy all recordsets from source zone to destination zone."""
        LOG.info(
            "Copying recordsets from source zone %s to destination zone %s",
            source_zone_id,
            dest_zone_id,
        )

        # All recordsets in a zone belong to the same project
        if CONF.multitenant_mode:
            identity_kwargs = self._get_identity_build_kwargs(
                migrated_associated_resources,
                source_project_id=source_project_id,
            )

            source_session = self._owner_scoped_session(
                self._source_session,
                [CONF.member_role_name],
                source_project_id,
            )
            dest_session = self._owner_scoped_session(
                self._destination_session,
                [CONF.member_role_name],
                identity_kwargs["project_id"],
            )
        else:
            source_session = self._source_session
            dest_session = self._destination_session

        source_recordsets = list(source_session.dns.recordsets(zone=source_zone_id))

        for recordset in source_recordsets:
            # Skip NS and SOA records at the zone apex - these are created automatically
            if recordset.type in ["NS", "SOA"]:
                LOG.debug(
                    "Skipping auto-created recordset: %s (%s)",
                    recordset.name,
                    recordset.type,
                )
                continue

            LOG.info("Copying recordset: %s (%s)", recordset.name, recordset.type)

            fields = [
                "description",
                "name",
                "records",
                "ttl",
                "type",
            ]
            recordset_attrs = {}
            for field in fields:
                value = getattr(recordset, field, None)
                if value:
                    recordset_attrs[field] = value

            try:
                dest_recordset = dest_session.dns.create_recordset(
                    zone=dest_zone_id, **recordset_attrs
                )
                LOG.info(
                    "Created recordset: %s (%s)",
                    dest_recordset.name,
                    dest_recordset.type,
                )
            except Exception as e:
                LOG.warning(
                    "Failed to create recordset %s (%s): %s",
                    recordset.name,
                    recordset.type,
                    e,
                )
                continue
