Multi-tenant mode
-----------------

``openstack-migrate`` allows migrating resources owned by other projects (tenants)
and preserving the owner information. This requires admin privileges.

The ``multitenant_mode`` setting is enabled by default. As a result, the owner
project and user resources are reported as dependencies and migrated
automatically.

Not all Openstack services allow specifying a different owner when creating
resources. As such, ``openstack-migrate`` needs to use project scoped sessions,
assigning itself as a member of the migrated tenant.

At the moment, this feature does not support Nova keypairs and Barbican secrets.
The keypairs will be skipped when migrating instances if the multi-tenant mode
is enabled. However, the keypair information shouldn't be mandatory for
already provisioned instances.
