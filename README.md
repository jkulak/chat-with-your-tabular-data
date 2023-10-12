# Chat with your tabular data

## Usage

1. `cp .env-template .env` and edit environment variables
1. `docker network create network_cwytd`
1. `docker run --rm -d --network network_cwytd -p 8080:8080 adminer`
1. `docker run -d --rm --network network_cwytd --env-file .env --name cwytd_db -v $(pwd)/pgdata:/pgdata postgres:14.1-alpine`
1. Access Admnier: <http://localhost:8080/?pgsql=db&username=postgres>

## Working with PostgreSQL

* Backup: `docker exec -ti spotify-grabtrack_db_1 pg_dump -U postgres -W -F c spotify -f /pg_backup/2022-03-31-backup.psql`
* Restore: `docker exec -ti spotify-grabtrack_db_1 pg_restore -U postgres -d spotify /pg_backup/2022-03-30-backup.psql`

Or

* Login to db Docker: `docker exec -ti spotify-grabtrack_db_1 bash --login`
* Backup database: `pg_dump -U postgres -W -F c spotify > /pgdata/2022-03-31-backup.psql`
* Restore: `pg_restore -U postgres -d pg_import_test /pgdata/2022-03-31-backup.psql`

## Work with alembic (database migrations)

1. Have the stack working (you need a running database) `docker-compose -f stack.yml up -d`
1. `docker build -t alembic-image ./db`
1. `docker run -ti -v $(pwd)/db:/db --rm --network smartplaylist_network alembic-image alembic revision -m "Create indexes on tracks"`
1. Run migrations `docker run -ti -v $(pwd)/db:/db --rm --network smartplaylist_network alembic-image alembic upgrade head`
1. Undo last migration `docker run -ti -v $(pwd)/db:/db --rm --network smartplaylist_network alembic-image alembic downgrade -1`

