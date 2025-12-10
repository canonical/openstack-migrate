# SPDX-FileCopyrightText: 2025 - Canonical Ltd
# SPDX-License-Identifier: Apache-2.0

from sunbeam_migrate.tests.integration import utils as test_utils

DEFAULT_PUB_KEY = (
    "ssh-ed25519 "
    "AAAAC3NzaC1lZDI1NTE5AAAAIOLZbMVQx28rALdZaYO55X+hY1osb9zCEd5AoAzHoJj0 "
    "cloudbase@testnode"
)


def create_test_keypair(
    session,
    *,
    name: str | None = None,
    public_key: str | None = None,
    **overrides,
):
    """Create a test keypair."""
    keypair_name = name or test_utils.get_test_resource_name()
    keypair_kwargs = {"name": keypair_name, "public_key": public_key or DEFAULT_PUB_KEY}
    keypair_kwargs.update(overrides)

    # If no public_key is provided, OpenStack will generate one
    keypair = session.compute.create_keypair(**keypair_kwargs)

    # Refresh the keypair information.
    return session.compute.get_keypair(keypair.id)


def check_migrated_flavor(source_flavor, destination_flavor):
    """Check that the migrated flavor matches the source flavor."""
    fields = [
        "name",
        "ram",
        "vcpus",
        "disk",
        "swap",
        "ephemeral",
        "rxtx_factor",
        "is_public",
        "description",
    ]
    for field in fields:
        assert getattr(source_flavor, field, None) == getattr(
            destination_flavor, field, None
        ), f"{field} attribute mismatch"

    source_specs = getattr(source_flavor, "extra_specs", {})
    dest_specs = getattr(destination_flavor, "extra_specs", {})
    assert dest_specs == source_specs
