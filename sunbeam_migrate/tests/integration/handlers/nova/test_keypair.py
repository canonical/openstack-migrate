# SPDX-FileCopyrightText: 2025 - Canonical Ltd
# SPDX-License-Identifier: Apache-2.0

from sunbeam_migrate.tests.integration import utils as test_utils

DEFAULT_PUB_KEY = (
    "ssh-ed25519 "
    "AAAAC3NzaC1lZDI1NTE5AAAAIOLZbMVQx28rALdZaYO55X+hY1osb9zCEd5AoAzHoJj0 "
    "cloudbase@testnode"
)


def _create_test_keypair(
    session,
    *,
    name: str | None = None,
    public_key: str | None = None,
    **overrides,
):
    keypair_name = name or test_utils.get_test_resource_name()
    keypair_kwargs = {"name": keypair_name, "public_key": public_key or DEFAULT_PUB_KEY}
    keypair_kwargs.update(overrides)

    # If no public_key is provided, OpenStack will generate one
    keypair = session.compute.create_keypair(**keypair_kwargs)

    # Refresh the keypair information.
    return session.compute.get_keypair(keypair.id)


def _check_migrated_keypair(source_keypair, destination_keypair, destination_session):
    """Check that the migrated keypair matches the source keypair."""
    for field in ["name", "type", "fingerprint"]:
        source_val = getattr(source_keypair, field, None)
        dest_val = getattr(destination_keypair, field, None)
        assert source_val == dest_val, f"{field} mismatch, {source_val} != {dest_val}"


def _delete_keypair(session, keypair_id: str):
    session.compute.delete_keypair(keypair_id, ignore_missing=True)


def test_migrate_keypair_with_cleanup(
    request,
    test_config_path,
    test_credentials,
    test_source_session,
    test_destination_session,
):
    keypair = _create_test_keypair(test_source_session)
    request.addfinalizer(lambda: _delete_keypair(test_source_session, keypair.id))

    test_utils.call_migrate(
        test_config_path,
        ["start", "--resource-type=keypair", "--cleanup-source", keypair.id],
    )

    dest_keypair = test_destination_session.compute.find_keypair(keypair.name)
    assert dest_keypair, "couldn't find migrated resource"
    request.addfinalizer(
        lambda: _delete_keypair(test_destination_session, dest_keypair.id)
    )

    _check_migrated_keypair(keypair, dest_keypair, test_destination_session)

    # Check that the keypair was removed from source
    assert not test_source_session.compute.find_keypair(
        keypair.name, ignore_missing=True
    ), "cleanup-source didn't remove the resource"


def test_migrate_keypair_skips_existing_destination(
    request,
    test_config_path,
    test_credentials,
    test_source_session,
    test_destination_session,
):
    shared_name = test_utils.get_test_resource_name()

    source_keypair = _create_test_keypair(
        test_source_session,
        name=shared_name,
    )
    request.addfinalizer(
        lambda: _delete_keypair(test_source_session, source_keypair.id)
    )

    destination_keypair = _create_test_keypair(
        test_destination_session,
        name=shared_name,
    )
    request.addfinalizer(
        lambda: _delete_keypair(test_destination_session, destination_keypair.id)
    )

    test_utils.call_migrate(
        test_config_path,
        ["start", "--resource-type=keypair", source_keypair.id],
    )

    migrated_dest_id = test_utils.get_destination_resource_id(
        test_config_path, "keypair", source_keypair.id
    )
    assert migrated_dest_id == destination_keypair.id, (
        "migration should reuse the existing destination keypair"
    )
