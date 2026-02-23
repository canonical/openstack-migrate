# SPDX-FileCopyrightText: 2025 - Canonical Ltd
# SPDX-License-Identifier: Apache-2.0

import logging

from sqlalchemy.sql.expression import asc, desc

from openstack_migrate import config
from openstack_migrate.db import models, session_utils

CONFIG = config.get_config()
LOG = logging.getLogger()


def initialize():
    """Initialize the database."""
    db_dir = CONFIG.database_file.parents[0]
    db_dir.mkdir(mode=0o750, exist_ok=True)

    db_url = "sqlite:////%s" % str(CONFIG.database_file)

    LOG.debug("Initializing db: %s", db_url)
    session_utils.initialize(db_url)


def create_tables():
    """Create the tables, if missing."""
    models.BaseModel.metadata.create_all(session_utils.engine)


@session_utils.ensure_session
def get_migrations(
    order_by="created_at",
    ascending=False,
    session=None,
    include_archived=False,
    **filters,
) -> list[models.Migration]:
    """Retrieve migrations."""
    order_type = asc if ascending else desc
    if not include_archived:
        filters["archived"] = False

    return (
        session.query(models.Migration)
        .filter_by(**filters)
        .order_by(order_type(order_by))
        .all()
    )


@session_utils.ensure_session
def delete_migrations(session=None, soft_delete=True, **filters):
    """Delete migrations.

    For soft deletion, we'll simply set the "archived" flag.
    """
    LOG.debug("Deleting migrations. Soft delete: %s, filters: %s", soft_delete, filters)
    if soft_delete:
        session.query(models.Migration).filter_by(**filters).update(
            {"archived": True},
        )
    else:
        session.query(models.Migration).filter_by(**filters).delete()


@session_utils.ensure_session
def restore_migrations(session=None, soft_delete=True, **filters):
    """Restore soft deleted migrations."""
    filters["archived"] = True

    LOG.debug("Restoring soft deleted migrations, filters: %s", filters)
    session.query(models.Migration).filter_by(**filters).update(
        {"archived": False},
    )
