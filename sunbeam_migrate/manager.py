# SPDX-FileCopyrightText: 2025 - Canonical Ltd
# SPDX-License-Identifier: Apache-2.0

import logging

from sunbeam_migrate import config, constants, exception
from sunbeam_migrate.db import api as db_api
from sunbeam_migrate.db import models
from sunbeam_migrate.handlers import factory

CONFIG = config.get_config()
LOG = logging.getLogger()


class SunbeamMigrationManager:
    def perform_individual_migration(
        self,
        resource_type: str,
        resource_id: str,
        cleanup_source: bool = False,
    ):
        """Migrate the specified resource."""
        handler = factory.get_migration_handler(resource_type)

        if not resource_id:
            raise exception.InvalidInput("No resource id specified.")

        LOG.info("Initiating %s migration, resource id: %s", resource_type, resource_id)

        migration = models.Migration(
            service=handler.get_service_type(),
            source_cloud=CONFIG.source_cloud_name,
            destination_cloud=CONFIG.destination_cloud_name,
            source_id=resource_id,
            resource_type=resource_type,
            status=constants.STATUS_IN_PROGRESS,
        )
        migration.save()

        try:
            # TODO: save the destination id even in case of failures and consider
            # performing cleanups.
            destination_id = handler.perform_individual_migration(resource_id)
        except Exception as ex:
            migration.status = constants.STATUS_FAILED
            migration.error_message = "Migration failed, error: %r" % ex
            migration.save()
            raise

        if cleanup_source:
            self.cleanup_migration_source(migration)

        LOG.info("Successfully migrated resource, destination id: %s", destination_id)
        migration.status = constants.STATUS_COMPLETED
        migration.destination_id = destination_id
        migration.save()

    def perform_batch_migration(
        self,
        resource_type: str,
        resource_filters: dict[str, str],
        dry_run: bool,
        cleanup_source: bool = False,
    ):
        """Migrate multiple resources that match the specified filters."""
        handler = factory.get_migration_handler(resource_type)

        resource_ids = handler.get_source_resource_ids(resource_filters)

        for resource_id in resource_ids:
            migrations = db_api.get_migrations(
                source_id=resource_id, status=constants.STATUS_COMPLETED
            )
            if migrations:
                LOG.info(
                    "Resource already migrated, skipping: %s. Migration: %s.",
                    resource_id,
                    migrations[-1].uuid,
                )
                continue

            if dry_run:
                LOG.info(
                    "DRY-RUN: %s migration, resource id: %s, cleanup source: %s",
                    resource_type,
                    resource_id,
                    cleanup_source,
                )
            else:
                self.perform_individual_migration(
                    resource_type, resource_id, cleanup_source=cleanup_source
                )

    def cleanup_migration_source(self, migration: models.Migration):
        """Cleanup the migration source."""
        LOG.info(
            "Migration succeeded, cleaning up source %s: %s",
            migration.resource_type,
            migration.source_id,
        )
        if not migration.source_id:
            raise exception.InvalidInput("Missing source id.")

        try:
            handler = factory.get_migration_handler(migration.resource_type)
            handler.delete_source_resource(migration.source_id)
            migration.source_removed = True
            migration.save()
        except Exception as ex:
            migration.status = constants.STATUS_SOURCE_CLEANUP_FAILED
            migration.error_message = "Source cleanup failed, error: %r" % ex
            migration.save()
            raise
