# SPDX-FileCopyrightText: 2025 - Canonical Ltd
# SPDX-License-Identifier: Apache-2.0

from sunbeam_migrate.tests.integration import utils as test_utils


def create_test_share_type(
    session,
    *,
    name: str | None = None,
    extra_specs: dict[str, str] | None = None,
    **overrides,
):
    share_type_kwargs = {
        "name": name or test_utils.get_test_resource_name(),
        "is_public": True,
        "description": "sunbeam-migrate share type test",
    }
    share_type_kwargs.update(overrides)
    share_type = session.shared_file_system.create_share_type(**share_type_kwargs)
    if extra_specs:
        session.shared_file_system.update_share_type_extra_specs(
            share_type, **extra_specs
        )

    # Refresh the share type information.
    return session.shared_file_system.get_share_type(share_type.id)


def check_migrated_share_type(source_share_type, destination_share_type):
    fields = [
        "name",
        "is_public",
        "description",
        "extra_specs",
    ]
    for field in fields:
        assert getattr(source_share_type, field, None) == getattr(
            destination_share_type, field, None
        ), f"{field} attribute mismatch"


def delete_share_type(session, share_type_id: str):
    session.shared_file_system.delete_share_type(share_type_id, ignore_missing=True)

