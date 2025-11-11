# SPDX-FileCopyrightText: 2025 - Canonical Ltd
# SPDX-License-Identifier: Apache-2.0

import logging

from sqlalchemy.sql.expression import asc, desc

from sunbeam_migrate import config
from sunbeam_migrate.db import models, session_utils

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
    order_by="created_at", ascending=True, session=None, **filters
) -> list[models.Migration]:
    """Retrieve migrations."""
    order_type = asc if ascending else desc

    return (
        session.query(models.Migration)
        .filter_by(**filters)
        .order_by(order_type(order_by))
        .all()
    )
