# Persistent Volume and Postgres Runtime Manifest

## Railway volume policy

- Use Railway Volumes UI for durable storage.
- Hermes runtime data lives under `/opt/data` inside the container.
- Bind `/opt/data` to a Railway volume; do not rely on Dockerfile `VOLUME` directives.
- Never store secrets in the volume mount.

## Postgres policy

- Use Railway Postgres as the durable backing store.
- Record connection string, database name, expected max connections, and volume retention policy.
- Validate connection from both Hermes gateway and Hatchet worker.
- Create a database user with least privilege for each service role.
- Confirm TLS and backup retention with Railway.

## Evidence format

```text
volume_name=<name>
volume_path=/opt/data
pg_connection=<host>:<port>
pg_database=<name>
pg_user=<role>
harness_test=<result>
backup_test=<result>
retry_test=<result>
rollback=<result>
```

## Rollback plan

- Stop services writing to Postgres and volume.
- Export volume contents if required.
- Restore prior service configuration.
- Re-validate Hermes health and Telegram delivery.
