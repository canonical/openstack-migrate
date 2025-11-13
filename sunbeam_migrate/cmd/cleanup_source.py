# SPDX-FileCopyrightText: 2025 - Canonical Ltd
# SPDX-License-Identifier: Apache-2.0

import logging
import typing

import click

from sunbeam_migrate import constants, manager
from sunbeam_migrate.db import api

LOG = logging.getLogger()


@click.command("cleanup-source")
@click.option("--service", help="Filter by service name")
@click.option("--resource-type", help="Filter by resource type")
@click.option("--source-id", help="Filter by source resource id.")
@click.option(
    "--all", "all_migrations", is_flag=True, help="Cleanup all succeeded migrations."
)
@click.option(
    "--dry-run", is_flag=True, help="Dry run: only log the resources to be deleted."
)
def cleanup_migration_sources(
    service: str,
    resource_type: str,
    source_id: str,
    all_migrations: bool,
    dry_run: bool,
):
    """Cleanup the source after successful migrations.

    Receives optional filters that specify which resources to clean up.
    """
    filters: dict[str, typing.Any] = {}
    if service:
        filters["service"] = service
    if resource_type:
        filters["resource_type"] = resource_type
    if source_id:
        filters["source_id"] = source_id

    if not filters and not all_migrations and not dry_run:
        raise click.ClickException(
            "No filters specified. Use '--all' to clean up all successful migrations."
        )

    filters["status"] = constants.STATUS_COMPLETED
    filters["source_removed"] = False

    LOG.debug("Cleaning up sources for the successful migrations. Filters: %s", filters)

    migrations = api.get_migrations(**filters)
    mgr = manager.SunbeamMigrationManager()

    for migration in migrations:
        if dry_run:
            LOG.info(
                "DRY-RUN: migration succeeded, cleaning up source %s: %s ",
                migration.resource_type,
                migration.source_id,
            )
        else:
            mgr.cleanup_migration_source(migration)
