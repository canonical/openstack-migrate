# SPDX-FileCopyrightText: 2025 - Canonical Ltd
# SPDX-License-Identifier: Apache-2.0

from sunbeam_migrate import config, constants, exception
from sunbeam_migrate.handlers import base

CONF = config.get_config()


class SecretHandler(base.BaseMigrationHandler):
    """Handle Barbican secret migrations."""

    def get_service_type(self) -> str:
        """Get the service type for this type of resource."""
        return "barbican"

    def get_supported_resource_filters(self) -> list[str]:
        """Get a list of supported resource filters.

        These filters can be specified when initiating batch migrations.
        """
        return ["owner_id"]

    def get_implementation_status(self) -> str:
        """Describe the implementation status."""
        return constants.IMPL_PARTIAL

    def _parse_barbican_url(self, secret_url) -> str:
        return (secret_url or "").split("/")[-1]

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
        source_secret = self._source_session.key_manager.get_secret(resource_id)
        if not source_secret:
            raise exception.NotFound(f"Secret not found: {resource_id}")

        # TODO: pass the project name if needed.
        fields = [
            "algorithm",
            "bit_length",
            "content_types",
            "expires_at",
            "mode",
            "name",
            "secret_type",
            "payload",
            "payload_content_type",
            "payload_content_encoding",
        ]
        kwargs = {}
        for field in fields:
            value = getattr(source_secret, field, None)
            if value:
                kwargs[field] = value

        destination_secret = self._destination_session.key_manager.create_secret(
            **kwargs
        )

        return destination_secret.id

    def get_source_resource_ids(self, resource_filters: dict[str, str]) -> list[str]:
        """Returns a list of resource ids based on the specified filters.

        Raises an exception if any of the filters are unsupported.
        """
        self._validate_resource_filters(resource_filters)

        query_filters = {}
        if "owner_id" in resource_filters:
            query_filters["owner"] = resource_filters["owner_id"]

        resource_ids = []
        for resource in self._source_session.key_manager.secrets(**query_filters):
            resource_ids.append(resource.id)

        return resource_ids

    def _delete_resource(self, resource_id: str, openstack_session):
        secret_id = self._parse_barbican_url(resource_id)
        openstack_session.key_manager.delete_secret(secret_id)
