# FastAPI Calculator: Users + Calculation BREAD

![CI/CD](https://github.com/hptankeu1/fastapi-calculator/actions/workflows/ci.yml/badge.svg)

A FastAPI back end with user registration and login (bcrypt password hashing and JWT tokens). Logged-in users get calculation BREAD endpoints: Browse, Read, Edit, Add and Delete. Data lives in PostgreSQL through SQLAlchemy and is validated with Pydantic. GitHub Actions runs the integration tests on every push and then publishes the Docker image to Docker Hub.

**Docker Hub:** https://hub.docker.com/r/htankeu/fastapi-calculator

```bash
docker pull htankeu/fastapi-calculator:latest
```

## Endpoints

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/users/register` | – | Create a user (`UserCreate`). Returns `UserRead`, status 201 |
| POST | `/users/login` | – | Log in with username **or** email. Returns a JWT `access_token` |
| GET | `/users/me` | Bearer | Current user |
| GET | `/calculations` | Bearer | **Browse** your calculations |
| GET | `/calculations/{id}` | Bearer | **Read** one calculation |
| PUT / PATCH | `/calculations/{id}` | Bearer | **Edit** (partial update; the result is recomputed) |
| POST | `/calculations` | Bearer | **Add** (`CalculationCreate`). Returns `CalculationRead`, status 201 |
| DELETE | `/calculations/{id}` | Bearer | **Delete** (204) |

Calculation types are `add`, `subtract`, `multiply` and `divide`. Each user can only see and change their own calculations. Another user's calculation returns 404.

**Validation and errors:** bad input returns `422`, for example an invalid email, a weak password, dividing by zero, an unknown operation or a non-numeric operand. A duplicate username or email returns `409`, wrong credentials or a missing token returns `401`, and a missing calculation returns `404`.

## Project structure

```
app/
  main.py              # FastAPI app; creates tables on startup
  database.py          # engine, SessionLocal, get_db
  security.py          # bcrypt hashing + JWT
  dependencies.py      # get_current_user (Bearer token)
  operations.py        # add/subtract/multiply/divide
  models/              # SQLAlchemy User, Calculation (one-to-many)
  schemas/             # UserCreate, UserLogin, UserRead, Token,
                       # CalculationCreate, CalculationUpdate, CalculationRead
  routers/             # users.py, calculations.py
tests/                 # pytest integration + unit tests
.github/workflows/ci.yml
Dockerfile, docker-compose.yml, init-test-db.sql
docs/REFLECTION.md
```

## Run the app with Docker Compose

```bash
docker compose up --build
```

- API docs (Swagger): http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- pgAdmin: http://localhost:5050 (`admin@example.com` / `admin`; server host `db`, password `postgres`)

## Manual checks with OpenAPI (`/docs`)

1. **POST `/users/register`**: click *Try it out*, send `{"username": "alice", "email": "alice@example.com", "password": "Secret123"}`, and expect **201**.
2. **POST `/users/login`**: send `{"username_or_email": "alice", "password": "Secret123"}`, then copy the `access_token` from the response.
3. Click **Authorize** (top right), paste the token, then click *Authorize* and *Close*.
4. **POST `/calculations`**: send `{"type": "add", "a": 10, "b": 5}` and expect **201** with `"result": 15`.
5. **GET `/calculations`**: the list should contain that calculation.
6. **GET `/calculations/1`**: returns the single calculation.
7. **PATCH `/calculations/1`**: send `{"type": "multiply"}`. The result becomes `50`.
8. **DELETE `/calculations/1`**: expect **204**. A GET on the same id now returns **404**.
9. Error checks:
   - POST `{"type": "divide", "a": 1, "b": 0}` returns **422**.
   - Logging in with a wrong password returns **401**.

## Run the integration tests locally

The tests use a real PostgreSQL database, `fastapi_test_db`, which they create, empty between tests and drop at the end.

**Option A: Postgres from Docker Compose (simplest)**

```bash
docker compose up -d db          # also creates fastapi_test_db (init-test-db.sql)
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
pytest --cov=app
```

**Option B: any Postgres.** Point `DATABASE_URL` at an empty database:

```bash
export DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/fastapi_test_db
pytest
```

What the tests cover (41 tests):

- `tests/test_users.py`
  - Registration works, and the database stores a bcrypt hash rather than the plain password.
  - A duplicate username or email returns 409.
  - Invalid payloads return 422.
  - Login works with a username or an email.
  - A wrong password or unknown user returns 401.
  - `/users/me` requires a token.
- `tests/test_calculations.py`
  - Each operation is created with the correct result.
  - A full Add → Read → Browse → Edit (PUT and PATCH) → Delete lifecycle, checked against the database.
  - Invalid data returns 422, missing ids return 404 and missing tokens return 401.
  - One user can't touch another user's calculations.
- `tests/test_operations.py`: unit tests for the arithmetic, the schemas, hashing and JWT.

## CI/CD (GitHub Actions)

`.github/workflows/ci.yml` runs on every push and pull request to `main`:

1. **test**: starts a `postgres:16` service, installs the dependencies and runs `pytest`.
2. **build-and-push**: runs only after the tests pass, on pushes to `main`. It builds the image, smoke-tests it against Postgres (`GET /health`) and pushes `htankeu/fastapi-calculator:latest` and `:<commit-sha>` to Docker Hub.

Required repository secrets (*Settings → Secrets and variables → Actions*):

| Secret | Value |
|---|---|
| `DOCKERHUB_USERNAME` | your Docker Hub username |
| `DOCKERHUB_TOKEN` | a Docker Hub access token (*Account settings → Personal access tokens*, Read & Write) |

## Run the published image

```bash
docker network create calc-net
docker run -d --name calc-db --network calc-net \
  -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=fastapi_db postgres:16
docker run -d --name calc-api --network calc-net -p 8000:8000 \
  -e DATABASE_URL=postgresql+psycopg2://postgres:postgres@calc-db:5432/fastapi_db \
  htankeu/fastapi-calculator:latest
# open http://localhost:8000/docs
```

## Troubleshooting

- **`container name "/postgres_db" is already in use`**: an older project's stack is still running. Run `docker compose down` in that project's folder first.
- **500 error, `column users.password_hash does not exist`**: the database volume holds an old `users` table from an earlier assignment. Reset it with `docker compose down -v && docker compose up --build`.
- **Port 5432 already in use**: change the `db` port mapping to `"5433:5432"`, and use port 5433 in `DATABASE_URL` when you run the tests.
