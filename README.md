# sunbeam-migrate
A tool that facilitates the migration from Charmed Openstack to Sunbeam.

## Examples

Prepare the sunbeam-migrate configuration:

```
$ export SUNBEAM_MIGRATE_CONFIG=~/migrate-config.yaml
$ cat > $SUNBEAM_MIGRATE_CONFIG <<EOF
log_level: info
cloud_config_file: /home/ubuntu/cloud-config.yaml
source_cloud_name: source-admin
destination_cloud_name: destination-admin
database_file: /home/ubuntu/.local/share/sunbeam-migrate/sqlite.db
EOF
```

Prepare the clouds.yaml file:

```
$ cat > /home/ubuntu/cloud-config.yaml <<EOF
clouds:
  source-admin:
    auth:
      auth_url: https://public.source.local/openstack-keystone/v3
      password: ***
      project_domain_name: admin_domain
      project_name: admin
      user_domain_name: admin_domain
      username: admin
      cacert: /home/ubuntu/sunbeam-ca/sunbeam-source-ca.pem
  destination-admin:
    auth:
      auth_url: https://public.destination.local/openstack-keystone/v3
      password: ***
      project_domain_name: admin_domain
      project_name: admin
      user_domain_name: admin_domain
      username: admin
    cacert: /home/ubuntu/sunbeam-ca/sunbeam-destination-ca.pem
EOF
```

Migrate a single image:

```
$ sunbeam-migrate start --resource-type=image 041ea0f1-93e8-4073-bfc1-ca961beec725
2025-11-12 14:29:43,482 INFO Initiating image migration, resource id: 041ea0f1-93e8-4073-bfc1-ca961beec725
2025-11-12 14:29:50,454 INFO Successfully migrated resource, destination id: aa83c834-3872-437e-9266-02b6eb4d4ff8
```

Migrate all images that match the specified filters, trying a dry-run first:

```
$ sunbeam-migrate start-batch --resource-type=image  --dry-run --filter "owner-id:516ddfe184c84f77889b33f027716e89"
2025-11-12 14:30:28,299 INFO DRY-RUN: image migration, resource id: 01c58135-8330-4792-a1ec-2277ec56eec9
2025-11-12 14:30:28,300 INFO Resource already migrated, skipping: 041ea0f1-93e8-4073-bfc1-ca961beec725. Migration: 1ab1d02c-f8f6-49df-bcd5-91e374e264ff

$ sunbeam-migrate start-batch --resource-type=image --filter "owner-id:516ddfe184c84f77889b33f027716e89"
2025-11-12 14:32:26,574 INFO Initiating image migration, resource id: 01c58135-8330-4792-a1ec-2277ec56eec9
2025-11-12 14:32:28,965 INFO Successfully migrated resource, destination id: 52d30bf9-0782-4244-beab-20065a5ce090
2025-11-12 14:32:28,970 INFO Resource already migrated, skipping: 041ea0f1-93e8-4073-bfc1-ca961beec725. Migration: 1ab1d02c-f8f6-49df-bcd5-91e374e264ff.

$ sunbeam-migrate start-batch --resource-type=image --filter "owner-id:516ddfe184c84f77889b33f027716e89"
2025-11-12 14:32:58,658 INFO Resource already migrated, skipping: 01c58135-8330-4792-a1ec-2277ec56eec9. Migration: 678a340a-f812-4aa2-acef-3d1aca2f4830.
2025-11-12 14:32:58,659 INFO Resource already migrated, skipping: 041ea0f1-93e8-4073-bfc1-ca961beec725. Migration: 1ab1d02c-f8f6-49df-bcd5-91e374e264ff
```

Listing migrations:

```
$ sunbeam-migrate list
+----------------------------------------------------------------------------------------------------------------------------------------------------------+
|                                                                        Migrations                                                                        |
+--------------------------------------+---------+---------------+-----------+--------------------------------------+--------------------------------------+
|                 UUID                 | Service | Resource type |   Status  |              Source ID               |            Destination ID            |
+--------------------------------------+---------+---------------+-----------+--------------------------------------+--------------------------------------+
| 1ab1d02c-f8f6-49df-bcd5-91e374e264ff |  glance |     image     | completed | 041ea0f1-93e8-4073-bfc1-ca961beec725 | aa83c834-3872-437e-9266-02b6eb4d4ff8 |
| 678a340a-f812-4aa2-acef-3d1aca2f4830 |  glance |     image     | completed | 01c58135-8330-4792-a1ec-2277ec56eec9 | 52d30bf9-0782-4244-beab-20065a5ce090 |
+--------------------------------------+---------+---------------+-----------+--------------------------------------+--------------------------------------+
```

Showing migration details:

```
$ sunbeam-migrate show 1ab1d02c-f8f6-49df-bcd5-91e374e264ff
+----------------------------------------------------------+
|                        Migration                         |
+-------------------+--------------------------------------+
|       Field       |                Value                 |
+-------------------+--------------------------------------+
|        Uuid       | 1ab1d02c-f8f6-49df-bcd5-91e374e264ff |
|     Created at    |      2025-11-12 14:29:43.486869      |
|     Updated at    |      2025-11-12 14:29:50.458527      |
|      Service      |                glance                |
|   Resource type   |                image                 |
|    Source cloud   |             source-admin             |
| Destination cloud |          destination-admin           |
|     Source id     | 041ea0f1-93e8-4073-bfc1-ca961beec725 |
|   Destination id  | aa83c834-3872-437e-9266-02b6eb4d4ff8 |
|       Status      |              completed               |
|   Error message   |                 None                 |
+-------------------+--------------------------------------+
```

## TODOs

* `sunbeam-migrate clear` command, removing one or more entries from the db
