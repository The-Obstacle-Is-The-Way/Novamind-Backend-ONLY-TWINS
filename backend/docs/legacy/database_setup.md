# Database Setup for Local Development and Testing

This document outlines the canonical setup for the PostgreSQL database used for local development and integration testing of the NovaMind backend.

## Overview

The project utilizes Docker Compose to manage the local development environment, including the PostgreSQL database.

- **File:** `deployment/docker-compose.yml`
- **Service Name:** `db`
- **Database:** PostgreSQL
- **Version:** 14

## Configuration

The `db` service in `deployment/docker-compose.yml` is configured as follows:

- **Image:** `postgres:14`
- **Environment Variables:**
    - `POSTGRES_USER=postgres` (Database username)
    - `POSTGRES_PASSWORD=postgres` (Database password)
    - `POSTGRES_DB=novamind` (Database name)
- **Port Mapping:** Host `5432` -> Container `5432`
- **Data Persistence:** Uses a named Docker volume `postgres_data` to persist data across container restarts.
- **Network:** Part of the `novamind-network` Docker network, allowing the `backend` service to connect using the hostname `db`.

## Backend Connection

The `backend` service in `docker-compose.yml` is configured with the following environment variable for database connection:

```
DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/novamind
```

- This URL uses the `asyncpg` driver suitable for asyncio applications.
- It connects to the `db` service hostname.
- It uses the credentials (`postgres`/`postgres`) and database name (`novamind`) defined for the `db` service.

## Running the Database

To start the PostgreSQL database service for local development or before running integration tests:

1.  Ensure Docker Desktop (or Docker Engine with Compose plugin) is installed and running.
2.  Navigate to the project's root directory (`Novamind-Backend-ONLY-TWINS`) in your terminal.
3.  Run the following command:

    ```bash
    docker compose -f deployment/docker-compose.yml up -d db
    ```

    This command starts *only* the `db` service in detached mode (`-d`).

## Running Tests

Before running integration tests (like `pytest app/tests/integration`), **ensure the `db` service is running** using the command above. This guarantees that the test runner can connect to the database using the expected credentials (`postgres`/`postgres`) and database name (`novamind`), resolving `InvalidAuthorizationSpecificationError` errors.

## Local Development without Docker

If running the backend directly on the host machine (outside Docker) for development, ensure you have a local PostgreSQL instance running and configured with:

- **Host:** `localhost`
- **Port:** `5432`
- **User:** `postgres`
- **Password:** `postgres`
- **Database:** `novamind`

You might need to create the `postgres` user and the `novamind` database manually in your local PostgreSQL instance. The application can also read these settings from a `.env` file in the `backend` directory if the `DATABASE_URL` environment variable is not set (see `backend/app/core/database_settings.py`):

```dotenv
# backend/.env (Example)
DB_HOST=localhost
DB_PORT=5432
DB_USERNAME=postgres
DB_PASSWORD=postgres
DB_DATABASE=novamind
```

However, using the Docker Compose setup is the recommended and canonical approach for consistency.
