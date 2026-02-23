# SPDX-FileCopyrightText: 2025 - Canonical Ltd
# SPDX-License-Identifier: Apache-2.0

STATUS_IN_PROGRESS = "in-progress"
STATUS_FAILED = "failed"
STATUS_COMPLETED = "completed"
STATUS_SOURCE_CLEANUP_FAILED = "source-cleanup-failed"
STATUS_PENDING_MEMBERS = "pending-members"
STATUS_PENDING_CLEANUP = "pending-cleanup"

# If the resource is in any of the following states, it has been
# migrated to the destination cloud and we've obtained a destination
# resource id that can be consumed by member (dependent) resources.
LIST_STATUS_MIGRATED: list[str] = [
    STATUS_COMPLETED,
    STATUS_SOURCE_CLEANUP_FAILED,
    STATUS_PENDING_MEMBERS,
    STATUS_PENDING_CLEANUP,
]

MANILA_MICROVERSION = "2.45"
NOVA_MICROVERSION = "2.93"  # Zed
