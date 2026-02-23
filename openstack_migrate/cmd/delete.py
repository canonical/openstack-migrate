# SPDX-FileCopyrightText: 2025 - Canonical Ltd
# SPDX-License-Identifier: Apache-2.0

import typing

import click

from openstack_migrate.db import api


@click.command("delete")
@click.option("--service", help="Filter by service name")
@click.option("--resource-type", help="Filter by resource type")
@click.option("--id", "migration_uuid", help="Filter by migration id.")
@click.option("--status", help="Filter by migration status.")
@click.option("--source-id", help="Filter by source resource id.")
@click.option("--archived", is_flag=True, help="Delete archived migrations.")
@click.option("--hard", is_flag=True, help="Perform hard deletion.")
@click.option("--all", "all_migrations", is_flag=True, help="Delete all migrations.")
def delete_migrations(
    service: str,
    resource_type: str,
    migration_uuid: str,
    status: str,
    source_id: str,
    archived: bool,
    hard: bool,
    all_migrations: bool,
):
    """Remove migrations from the openstack-migrate database.

    Receives optional filters that are joined using "AND" logical operators.
    Performs a soft deletion unless "--hard" is specified.
    """
    filters: dict[str, typing.Any] = {}
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
    if archived:
        filters["archived"] = True

    if not filters and not all_migrations:
        raise click.ClickException(
            "No filters specified. Pass '--all' to remove all migrations."
        )

    api.delete_migrations(soft_delete=(not hard), **filters)
