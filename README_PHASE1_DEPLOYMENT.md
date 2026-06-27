# SAIVEX Phase 1 — Production Ready Files

These files make your original Flask SAIVEX deployment-ready without changing the UI or removing features.

## Copy these files into your original `D:\saivex`

- `app.py`
- `Dockerfile`
- `docker-compose.yml`
- `Procfile`
- `gunicorn.conf.py`
- `runtime.txt`
- `.env.example`
- `.dockerignore`
- `.gitignore`
- `utils/security.py`
- `utils/logging_config.py`
- `templates/404.html`
- `templates/500.html`

## Before running

Create your real `.env` file from `.env.example`:

```powershell
copy .env.example .env
```

Then put your real OpenRouter key inside `.env`.

## Local test

```powershell
cd D:\saivex
py app.py
```

Open:

```text
http://127.0.0.1:5000/health
```

It should return status ok.

## Docker test

```powershell
cd D:\saivex
docker compose up --build
```

Open:

```text
http://127.0.0.1:5000
```

## Production command

```text
gunicorn -c gunicorn.conf.py app:app
```

## Notes

- Your original backend still comes from `legacy_app.py`.
- SQLite is kept for now.
- Uploads and generated files are kept as persistent folders.
- Do not upload your real `.env` to GitHub.
