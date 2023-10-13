# Chat with your tabular data

## Usage

1. `cp .env-template .env` and edit environment variables
1. `docker network create network_cwytd`
1. `docker run -d --rm --network network_cwytd --env-file .env --name cwytd_db -v $(pwd)/pgdata:/pgdata postgres:14.1-alpine`
1. `docker run -d --rm --network network_cwytd -p 8080:8080 adminer`
1. Access Admnier: <http://localhost:8080/?pgsql=db&username=postgres>
