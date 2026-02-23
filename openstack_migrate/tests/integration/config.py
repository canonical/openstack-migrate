# SPDX-FileCopyrightText: 2025 - Canonical Ltd
# SPDX-License-Identifier: Apache-2.0

from openstack_migrate import config


class OpenstackMigrateTestConfig(config.OpenstackMigrateConfig):
    # We're using the "project_cleanup" method of the Openstack SDK
    # to wipe any remaining resources owned by the temporary tenants.
    # It can take about ~30 seconds since it queries all supported services.
    # Use the following setting to disable this step.
    skip_project_purge: bool = False
    # The ID of an image used for instance migration tests.
    image_id: str | None = None
    # The ID of a flavor used for instance migration tests.
    flavor_id: str | None = None
