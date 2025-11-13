# SPDX-FileCopyrightText: 2025 - Canonical Ltd
# SPDX-License-Identifier: Apache-2.0

import abc
import os

import openstack
from openstack import exceptions as openstack_exc

from sunbeam_migrate import config, exception

CONF = config.get_config()


class BaseMigrationHandler(abc.ABC):
    """Base migration class."""

    _SUPPORTED_RESOURCE_FILTERS: list[str] = []

    @abc.abstractmethod
    def get_service_type(self) -> str:
        """Get the service type for this type of resource."""
        pass

    @abc.abstractmethod
    def perform_individual_migration(self, resource_id: str) -> str:
        """Migrate the specified resource.

        Return the resulting resource id.
        """
        pass

    @abc.abstractmethod
    def get_source_resource_ids(self, resource_filters: dict[str, str]) -> list[str]:
        """Returns a list of resource ids based on the specified filters.

        Raises an exception if any of the filters are unsupported.
        """
        pass

    def delete_source_resource(self, resource_id: str):
        """Delete the specified resource on the source cloud side."""
        self._delete_resource(resource_id, self._source_session)

    def delete_destination_resource(self, resource_id: str):
        """Delete the specified resource on the destination cloud side."""
        self._delete_resource(resource_id, self._destination_session)

    def _delete_resource(self, resource_id: str, openstack_session):
        raise NotImplementedError()

    def _get_openstack_session(self, cloud_name: str):
        if not CONF.cloud_config_file:
            raise exception.InvalidInput("No cloud config provided.")

        os.environ["OS_CLIENT_CONFIG_FILE"] = str(CONF.cloud_config_file)
        return openstack.connect(cloud=cloud_name)

    @property
    def _source_session(self):
        if not CONF.source_cloud_name:
            raise exception.InvalidInput("No source cloud specified.")

        if not getattr(self, "_cached_source_session", None):
            self._cached_source_session = self._get_openstack_session(
                CONF.source_cloud_name
            )

        return self._cached_source_session

    @property
    def _destination_session(self):
        if not CONF.destination_cloud_name:
            raise exception.InvalidInput("No destination cloud specified.")

        if not getattr(self, "_cached_destinaton_session", None):
            self._cached_destinaton_session = self._get_openstack_session(
                CONF.destination_cloud_name
            )

        return self._cached_destinaton_session

    def _get_explicit_destination_project(self, source_project_name) -> str | None:
        """Get an explicit destination project name.

        Admin users may create resources for other tenants. If the source project
        name matches the session project name, we'll avoid passing a tenant name,
        using the current tenant instead. This allows non-admin users to migrate
        resources, using the same tenant name on the destination side.
        """
        dest_session_project = self._destination_session.auth.get("project_name")
        if source_project_name == dest_session_project:
            return None

        try:
            destination_project = self._destination_session.get_project(
                source_project_name
            )
        except openstack_exc.NotFoundException:
            raise exception.InvalidInput(
                f"The {source_project_name} tenant does not exist on "
                "the destination side."
            )
        return destination_project

    def _validate_resource_filters(self, resource_filters: dict[str, str]):
        for key in resource_filters:
            if key not in self._SUPPORTED_RESOURCE_FILTERS:
                raise exception.InvalidInput(
                    f"Invalid resource filter: {key}, "
                    f"supported filters {self._SUPPORTED_RESOURCE_FILTERS}"
                )
