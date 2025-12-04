# SPDX-FileCopyrightText: 2025 - Canonical Ltd
# SPDX-License-Identifier: Apache-2.0

import logging
from typing import Any

from sunbeam_migrate import exception
from sunbeam_migrate.handlers import base

LOG = logging.getLogger()


class ShareTypeHandler(base.BaseMigrationHandler):
    """Handle Manila share type migrations."""

    def get_service_type(self) -> str:
        """Get the service type for this type of resource."""
        return "manila"

    def get_supported_resource_filters(self) -> list[str]:
        """Get a list of supported resource filters.

        These filters can be specified when initiating batch migrations.
        """
        return []

    def perform_individual_migration(
        self,
        resource_id: str,
        migrated_associated_resources: list[tuple[str, str, str]],
    ) -> str:
        """Migrate the specified resource.

        :param resource_id: the resource to be migrated
        :param migrated_associated_resources: a list of tuples describing
            associated resources that have already been migrated.
            Format: (resource_type, source_id, destination_id)

        Return the resulting resource id.
        """
        source_type = self._source_session.shared_file_system.get_share_type(
            resource_id
        )
        if not source_type:
            raise exception.NotFound(f"Share type not found: {resource_id}")

        existing_type = self._destination_session.shared_file_system.find_share_type(
            source_type.name, ignore_missing=True
        )
        if existing_type:
            # TODO: we might consider moving those checks on the manager side
            # and have a consistent approach across handlers.
            LOG.warning(
                "Share type already exists: %s %s",
                existing_type.id,
                existing_type.name,
            )
            return existing_type.id

        type_kwargs = self._build_type_kwargs(source_type)
        destination_type = (
            self._destination_session.shared_file_system.create_share_type(
                **type_kwargs
            )
        )

        extra_specs = getattr(source_type, "extra_specs", None)
        if extra_specs:
            self._destination_session.shared_file_system.update_share_type_extra_specs(
                destination_type, **extra_specs
            )

        # TODO: handle type access
        return destination_type.id

    def _build_type_kwargs(self, source_type: Any) -> dict[str, Any]:
        kwargs: dict[str, Any] = {}

        fields = [
            "is_public",
            "description",
            "name",
        ]
        for field in fields:
            value = getattr(source_type, field, None)
            if value not in (None, {}):
                kwargs[field] = value

        return kwargs

    def get_source_resource_ids(self, resource_filters: dict[str, str]) -> list[str]:
        """Returns a list of resource ids based on the specified filters.

        Raises an exception if any of the filters are unsupported.
        """
        self._validate_resource_filters(resource_filters)

        resource_ids: list[str] = []
        for share_type in self._source_session.shared_file_system.share_types():
            resource_ids.append(share_type.id)
        return resource_ids

    def _delete_resource(self, resource_id: str, openstack_session):
        try:
            openstack_session.shared_file_system.delete_share_type(
                resource_id, ignore_missing=True
            )
        except Exception:
            # TODO: stop suppressing this once we include a flag along with
            # the resource dependencies, specifying which ones can be deleted.
            LOG.warning("Unable to delete share type, it's probably still in use.")
