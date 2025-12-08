# SPDX-FileCopyrightText: 2025 - Canonical Ltd
# SPDX-License-Identifier: Apache-2.0

from openstack import exceptions as openstack_exc

from sunbeam_migrate.tests.integration import utils as test_utils


def create_test_domain(
    session,
    *,
    name: str | None = None,
    description: str | None = None,
    enabled: bool = True,
    **overrides,
):
    domain_kwargs = {
        "name": name or test_utils.get_test_resource_name(),
        "description": description or "sunbeam-migrate domain test",
        "enabled": enabled,
    }
    domain_kwargs.update(overrides)
    domain = session.identity.create_domain(**domain_kwargs)

    # Refresh the domain information.
    return session.identity.get_domain(domain.id)


def check_migrated_domain(source_domain, destination_domain):
    fields = [
        "name",
        "description",
        "enabled",
    ]
    for field in fields:
        assert getattr(source_domain, field, None) == getattr(
            destination_domain, field, None
        ), f"{field} attribute mismatch"


def delete_domain(session, domain_id: str):
    try:
        domain = session.identity.get_domain(domain_id)
        if domain and domain.is_enabled:
            # Domains must be disabled before deletion.
            session.identity.update_domain(domain, enabled=False)
    except openstack_exc.NotFoundException:
        pass

    session.identity.delete_domain(domain_id, ignore_missing=True)
