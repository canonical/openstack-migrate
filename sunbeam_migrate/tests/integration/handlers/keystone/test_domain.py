# SPDX-FileCopyrightText: 2025 - Canonical Ltd
# SPDX-License-Identifier: Apache-2.0

import pytest
from openstack import exceptions as openstack_exc

from sunbeam_migrate.tests.integration import utils as test_utils
from sunbeam_migrate.tests.integration.handlers.keystone import (
    utils as keystone_test_utils,
)


def test_migrate_domain_with_cleanup(
    request,
    test_config_path,
    test_credentials,
    test_source_session,
    test_destination_session,
):
    domain = keystone_test_utils.create_test_domain(test_source_session)
    request.addfinalizer(
        lambda: keystone_test_utils.delete_domain(test_source_session, domain.id)
    )

    test_utils.call_migrate(
        test_config_path,
        ["start", "--resource-type=domain", "--cleanup-source", domain.id],
    )

    dest_domain = test_destination_session.identity.find_domain(domain.name)
    assert dest_domain, "couldn't find migrated resource"
    request.addfinalizer(
        lambda: keystone_test_utils.delete_domain(
            test_destination_session, dest_domain.id
        )
    )

    keystone_test_utils.check_migrated_domain(domain, dest_domain)

    with pytest.raises(openstack_exc.ResourceNotFound):
        test_source_session.identity.get_domain(domain.id)
