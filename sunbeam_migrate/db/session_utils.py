# SPDX-FileCopyrightText: 2025 - Canonical Ltd
# SPDX-License-Identifier: Apache-2.0

import contextlib
import functools

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = None
SessionClass = None


def initialize(db_url, echo=False):
    """Initialize database connection."""
    global engine
    global SessionClass

    engine = create_engine(db_url, echo=echo)
    SessionClass = sessionmaker(bind=engine, expire_on_commit=False)


def get_new_session():
    """Create a new database session."""
    return SessionClass()


@contextlib.contextmanager
def get_temp_session():
    """Get a temporary database session.

    The session is committed and closed when exiting the context.
    """
    session = None
    try:
        session = get_new_session()
        yield session
    finally:
        if session:
            session.commit()
            session.close()


def ensure_session(f):
    """Pass a session the decorated function if none was provided."""

    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        session = kwargs.pop("session", None)
        if not session:
            with get_temp_session() as session:
                kwargs["session"] = session
                return f(*args, **kwargs)
        else:
            kwargs["session"] = session
            return f(*args, **kwargs)

    return wrapper
