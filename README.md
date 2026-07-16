# AdPilot v1

AdPilot is a production-oriented SaaS foundation for monitoring Meta Ads creatives. It imports ad-level performance, evaluates configurable deterioration rules, recommends action, and notifies users through Slack. It never pauses or edits campaigns.

## Included applications

- `backend/`: FastAPI, async SQLAlchemy, PostgreSQL, JWT authentication, Meta Marketing API, APScheduler, Slack outbox delivery, Alembic, tests, and structured logging.
- `frontend/`: responsive Flutter application for web, Android, iOS, and Windows with secure token storage, dashboard, creative monitoring, product grouping, alerts, Meta OAuth, manual sync, and settings.
- `docs/ARCHITECTURE.md`: system boundaries, data model, analyzer semantics, API contract, and scaling path.

## Start everything with Docker

1. Copy `.env.example` to `.env`.
2. Replace `SECRET_KEY` with at least 32 random characters.
3. Generate `TOKEN_ENCRYPTION_KEY` with:

   ```powershell
   python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
   ```

4. Until the Meta app is configured, set `SYNC_SCHEDULER_ENABLED=false`.
5. Start the stack and migrate the database:

   ```powershell
   docker compose up --build -d
   docker compose exec api alembic upgrade head
   docker compose exec api python -m app.cli create-user --email you@example.com
   ```

6. Open the Flutter app at `http://localhost:8080` and API documentation at `http://localhost:8000/docs`.

## Run Flutter from VS Code

Windows plugin builds require **Developer Mode** so Flutter can create package symlinks. Enable it under Windows Settings → System → For developers.

From `frontend/`:

```powershell
flutter pub get
flutter run -d chrome --web-port 8080 `
  --dart-define=API_BASE_URL=http://localhost:8000/api/v1 `
  --dart-define=META_APP_ID=your-meta-app-id `
  --dart-define=META_API_VERSION=v23.0 `
  --dart-define=META_REDIRECT_URI=http://localhost:8080/#/meta
```

## Meta app configuration

Configure the exact OAuth redirect URI `http://localhost:8080/#/meta` in the Meta developer app for local development. Set `META_APP_ID` and `META_APP_SECRET` in `.env`. The Flutter app initiates OAuth, the backend exchanges the authorization code, encrypts the resulting token, returns accessible ad-account choices, and consumes the selection through a 15-minute connection session.

Requested scopes are limited to `ads_read` and `business_management`. There is no campaign delivery mutation API.

## Quality checks

Backend, from `backend/`:

```powershell
ruff check app tests alembic
mypy app
pytest
```

Frontend, from `frontend/`:

```powershell
dart format --output=none --set-exit-if-changed lib test
flutter analyze --no-pub
flutter test --no-pub
```

## Production considerations

- Run the scheduler in only one API replica. Before horizontally scaling scheduled work, move synchronization to a durable queue with a per-account lock.
- Serve Flutter over HTTPS; secure browser token storage and OAuth require a secure production origin.
- Use a managed secret store for application keys and provider credentials.
- Validate Meta action mappings and attribution settings against the production ad account before relying on purchase and revenue figures.
