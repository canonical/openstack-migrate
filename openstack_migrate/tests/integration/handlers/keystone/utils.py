# SPDX-FileCopyrightText: 2025 - Canonical Ltd
# SPDX-License-Identifier: Apache-2.0

from openstack import exceptions as openstack_exc

from openstack_migrate.tests.integration import utils as test_utils


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
        "description": description or "openstack-migrate domain test",
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


def create_test_project(
    session,
    *,
    name: str | None = None,
    description: str | None = None,
    enabled: bool = True,
    domain_id: str | None = None,
    **overrides,
):
    project_kwargs = {
        "name": name or test_utils.get_test_resource_name(),
        "description": description or "openstack-migrate project test",
        "enabled": enabled,
    }
    if domain_id:
        project_kwargs["domain_id"] = domain_id
    project_kwargs.update(overrides)
    project = session.identity.create_project(**project_kwargs)

    # Refresh the project information.
    return session.identity.get_project(project.id)


def check_migrated_project(
    source_session,
    destination_session,
    source_project,
    destination_project,
):
    fields = [
        "name",
        "description",
        "enabled",
    ]
    for field in fields:
        assert getattr(source_project, field, None) == getattr(
            destination_project, field, None
        ), f"{field} attribute mismatch"

    assert source_project.domain_id
    source_domain = source_session.identity.get_domain(source_project.domain_id)

    assert destination_project.domain_id
    destination_domain = destination_session.identity.get_domain(
        destination_project.domain_id
    )

    assert source_domain.name == destination_domain.name


def delete_project(session, project_id: str):
    try:
        project = session.identity.get_project(project_id)
        if project and project.is_enabled:
            # Projects must be disabled before deletion.
            session.identity.update_project(project, enabled=False)
    except openstack_exc.NotFoundException:
        pass

    session.identity.delete_project(project_id, ignore_missing=True)


def create_test_user(
    session,
    *,
    name: str | None = None,
    description: str | None = None,
    enabled: bool = True,
    email: str | None = None,
    domain_id: str | None = None,
    password: str | None = None,
    **overrides,
):
    user_kwargs = {
        "name": name or test_utils.get_test_resource_name(),
        "description": description or "openstack-migrate user test",
        "enabled": enabled,
    }
    if email:
        user_kwargs["email"] = email
    if domain_id:
        user_kwargs["domain_id"] = domain_id
    if password:
        user_kwargs["password"] = password
    user_kwargs.update(overrides)
    user = session.identity.create_user(**user_kwargs)

    # Refresh the user information.
    return session.identity.get_user(user.id)


def check_migrated_user(
    source_session,
    destination_session,
    source_user,
    destination_user,
):
    fields = [
        "name",
        "description",
        "enabled",
        "email",
    ]
    for field in fields:
        assert getattr(source_user, field, None) == getattr(
            destination_user, field, None
        ), f"{field} attribute mismatch"

    assert source_user.domain_id
    source_domain = source_session.identity.get_domain(source_user.domain_id)

    assert destination_user.domain_id
    destination_domain = destination_session.identity.get_domain(
        destination_user.domain_id
    )

    assert source_domain.name == destination_domain.name


def delete_user(session, user_id: str):
    try:
        user = session.identity.get_user(user_id)
        if user and user.is_enabled:
            # Users must be disabled before deletion.
            session.identity.update_user(user, enabled=False)
    except openstack_exc.NotFoundException:
        pass

    session.identity.delete_user(user_id, ignore_missing=True)


def create_test_role(
    session,
    *,
    name: str | None = None,
    description: str | None = None,
    domain_id: str | None = None,
    **overrides,
):
    role_kwargs = {
        "name": name or test_utils.get_test_resource_name(),
        "description": description or "openstack-migrate role test",
    }
    if domain_id:
        role_kwargs["domain_id"] = domain_id
    role_kwargs.update(overrides)
    role = session.identity.create_role(**role_kwargs)

    # Refresh the role information.
    return session.identity.get_role(role.id)


def check_migrated_role(
    source_session,
    destination_session,
    source_role,
    destination_role,
):
    fields = [
        "name",
        "description",
    ]
    for field in fields:
        assert getattr(source_role, field, None) == getattr(
            destination_role, field, None
        ), f"{field} attribute mismatch"

    # Check domain preservation if the role is domain-specific
    if source_role.domain_id:
        assert destination_role.domain_id
        source_domain = source_session.identity.get_domain(source_role.domain_id)
        destination_domain = destination_session.identity.get_domain(
            destination_role.domain_id
        )
        assert source_domain.name == destination_domain.name


def delete_role(session, role_id: str):
    session.identity.delete_role(role_id, ignore_missing=True)
