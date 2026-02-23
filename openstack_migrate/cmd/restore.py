# SPDX-FileCopyrightText: 2025 - Canonical Ltd
# SPDX-License-Identifier: Apache-2.0

import click

from openstack_migrate.db import api


@click.command("restore")
@click.option("--service", help="Filter by service name")
@click.option("--resource-type", help="Filter by resource type")
@click.option("--id", "migration_uuid", help="Filter by migration id.")
@click.option("--status", help="Filter by migration status.")
@click.option("--source-id", help="Filter by source resource id.")
def restore_migrations(
    service: str,
    resource_type: str,
    migration_uuid: str,
    status: str,
    source_id: str,
):
    """Restore soft-deleted migrations.

    Receives optional filters that are joined using "AND" logical operators.
    """
    filters = {}
    if service:
        filters["service"] = service
    if resource_type:
        filters["resource_type"] = resource_type
    if migration_uuid:
        filters["uuid"] = migration_uuid
    if status:
        filters["status"] = status
    if source_id:
        filters["source_id"] = source_id

    api.restore_migrations(**filters)
