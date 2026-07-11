# fin

A small FastAPI backend for splitting shared expenses (rent, groceries, trips, ...)
between people, and tracking personal expenses along the way.

## Model

- **Space** — a group (e.g. "Household") containing users and persons.
- **User** — an account holder who can log in; users own spaces.
- **Person** — someone expenses are tracked for; not every person needs a login.
- **Account** — belongs to a person, holds their side of contributions.
- **Transaction** — a single expense (title, date, description) in a space.
- **Contribution** (`AccountTransaction`) — one account's share of a transaction:
  `amount_requested` (what they owe) vs `amount_paid` (what they actually paid).
  A transaction with one contribution where both amounts match is a plain
  personal expense; multiple contributions with mismatched amounts is a
  shared/split expense with a balance owed.
- **Category** — a tag (e.g. "Rent", "Groceries") linkable to transactions.

A person can belong to multiple spaces; a user only sees a person's
transactions, balance, and counts for spaces they share with that person.

## Setup

```bash
uv sync
```

Configure via `.env` (see `src/app/config.py` for defaults):

```
DATABASE_URI=sqlite:///data/fin.db
AUTH_SECRET_KEY=change-me
AUTH_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

## Run

```bash
uv run python src/main.py
```

Or with auto-reload during development:

```bash
uv run uvicorn app.api:app --reload --app-dir src
```

API docs are served at `/docs` once running.

### Docker

```bash
docker build -t fin .
docker run -d --name fin -p 8000:8000 \
  -e AUTH_SECRET_KEY="$(openssl rand -hex 32)" \
  -e DATABASE_URI="sqlite:////app/data/sqlite3.db" \
  -v fin-data:/app/data \
  fin
```

`DATABASE_URI` must point at a file (not the `sqlite:///:memory:` default) —
each pooled connection to an in-memory sqlite DB is a separate empty
database, so requests would randomly fail with "no such table". Mount a
volume at `/app/data` (as above) so the sqlite file survives container
restarts.

## Test

```bash
uv run pytest
```

## API overview

All routes except `/auth/*` require a Bearer token (`POST /auth/register`,
`POST /auth/login`). Everything else lives under `/split`:

- `/split/spaces` — create/list/update/delete spaces; manage users and persons
  in a space; space transactions, overview, and balances.
- `/split/persons` — create/list/update/delete persons; a person's
  transactions, accounts, and summary (scoped to shared spaces).
- `/split/accounts` — create/list/update/delete accounts.
- `/split/transactions` — create/list/update/delete transactions; manage
  contributions and category links.
- `/split/categories` — create/list/update/delete categories.
