# SPDX-FileCopyrightText: 2025 - Canonical Ltd
# SPDX-License-Identifier: Apache-2.0

from sunbeam_migrate.tests.integration import utils as test_utils
from sunbeam_migrate.tests.integration.handlers.manila import utils as manila_test_utils


def test_migrate_share_type_with_cleanup(
    request,
    test_config_path,
    test_credentials,
    test_source_session,
    test_destination_session,
):
    extra_specs = {"driver_handles_share_servers": "false"}
    share_type = manila_test_utils.create_test_share_type(
        test_source_session, extra_specs=extra_specs
    )
    request.addfinalizer(
        lambda: manila_test_utils.delete_share_type(
            test_source_session, share_type.id
        )
    )

    test_utils.call_migrate(
        test_config_path,
        ["start", "--resource-type=share-type", "--cleanup-source", share_type.id],
    )

    dest_share_type = test_destination_session.shared_file_system.find_share_type(
        share_type.name
    )
    assert dest_share_type, "couldn't find migrated resource"
    request.addfinalizer(
        lambda: manila_test_utils.delete_share_type(
            test_destination_session, dest_share_type.id
        )
    )

    manila_test_utils.check_migrated_share_type(share_type, dest_share_type)

    assert not test_source_session.shared_file_system.find_share_type(share_type.id), (
        "cleanup-source didn't remove the resource"
    )

