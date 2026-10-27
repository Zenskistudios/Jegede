# Jegede

Backend for Yoruba-language applications.

## Run locally

Set `DATABASE_URL` to a PostgreSQL database, then run:

```text
pip install -e ".[api,test]"
uvicorn jegede.api.app:app --reload
```

The database schema is applied automatically on startup when `DATABASE_URL` is set.

## Run with Docker

```text
docker compose up --build
```

The API is available at `http://localhost:8000`.
