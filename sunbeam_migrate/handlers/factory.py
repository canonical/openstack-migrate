# SPDX-FileCopyrightText: 2025 - Canonical Ltd
# SPDX-License-Identifier: Apache-2.0

import importlib

from sunbeam_migrate import exception
from sunbeam_migrate.handlers import base

MIGRATION_HANDLERS = {
    "image": "GlanceImageMigrationHandler",
}


def get_migration_handler(resource_type: str) -> base.BaseMigrationHandler:
    if not resource_type:
        raise exception.InvalidInput("No resource type specified.")
    if resource_type not in MIGRATION_HANDLERS:
        raise exception.InvalidInput("Unsupported resource type: %s" % resource_type)

    class_name = MIGRATION_HANDLERS[resource_type]
    module = importlib.import_module(f"sunbeam_migrate.handlers.{resource_type}")
    cls = getattr(module, class_name)
    return cls()
