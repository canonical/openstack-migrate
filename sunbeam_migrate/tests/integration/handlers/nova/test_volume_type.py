# SPDX-FileCopyrightText: 2025 - Canonical Ltd
# SPDX-License-Identifier: Apache-2.0

from sunbeam_migrate.tests.integration import utils as test_utils


def _create_test_volume_type(
    session,
    *,
    name: str | None = None,
    extra_specs: dict[str, str] | None = None,
    **overrides,
):
    volume_type_kwargs = {
        "name": name or test_utils.get_test_resource_name(),
        "is_public": True,
        "description": "sunbeam-migrate volume type test",
    }
    volume_type_kwargs.update(overrides)
    if not extra_specs:
        extra_specs = {"read_only": "false"}

    volume_type = session.block_storage.create_type(**volume_type_kwargs)
    session.block_storage.update_type_extra_specs(volume_type, **extra_specs)

    # Refresh the volume type information.
    return session.block_storage.get_type(volume_type.id)


def _check_migrated_volume_type(
    source_volume_type, destination_volume_type, destination_session
):
    fields = [
        "name",
        "is_public",
        "description",
        "extra_specs",
    ]
    for field in fields:
        assert getattr(source_volume_type, field, None) == getattr(
            destination_volume_type, field, None
        ), f"{field} attribute mismatch"


def _delete_volume_type(session, volume_type_id: str):
    session.block_storage.delete_type(volume_type_id, ignore_missing=True)


def test_migrate_volume_type_with_cleanup(
    request,
    test_config_path,
    test_credentials,
    test_source_session,
    test_destination_session,
):
    volume_type = _create_test_volume_type(test_source_session)
    request.addfinalizer(
        lambda: _delete_volume_type(test_source_session, volume_type.id)
    )

    test_utils.call_migrate(
        test_config_path,
        ["start", "--resource-type=volume-type", "--cleanup-source", volume_type.id],
    )

    dest_volume_type = test_destination_session.block_storage.find_type(
        volume_type.name
    )
    assert dest_volume_type, "couldn't find migrated resource"
    request.addfinalizer(
        lambda: _delete_volume_type(test_destination_session, dest_volume_type.id)
    )

    _check_migrated_volume_type(volume_type, dest_volume_type, test_destination_session)

    assert not test_source_session.block_storage.find_type(volume_type.id), (
        "cleanup-source didn't remove the resource"
    )
