# SPDX-FileCopyrightText: 2025 - Canonical Ltd
# SPDX-License-Identifier: Apache-2.0

import json

import click
import prettytable

from sunbeam_migrate.db import api, models


@click.command("list")
@click.option("--service", help="List migrations for the specified service.")
@click.option(
    "--format",
    "-f",
    "output_format",
    type=click.Choice(["json", "table"]),
    default="table",
    help="Set the output format.",
)
def list_migrations(output_format: str, service: str):
    filters = {}
    if service:
        filters["service"] = service
    migrations = api.get_migrations(**filters)

    if output_format == "table":
        _table_format(migrations)
    else:
        _json_format(migrations)


def _table_format(migrations: list[models.Migration]):
    table = prettytable.PrettyTable()
    table.title = "Migrations"
    table.field_names = [
        "UUID",
        "Service",
        "Resource type",
        "Status",
        "Source ID",
        "Destination ID",
    ]
    for entry in migrations:
        table.add_row(
            [
                entry.uuid,
                entry.service,
                entry.resource_type,
                entry.status,
                entry.source_id,
                entry.destination_id,
            ]
        )
    print(table)


def _json_format(migrations: list[models.Migration]):
    migration_dict_list = [migration.to_dict() for migration in migrations]
    print(json.dumps(migration_dict_list))
