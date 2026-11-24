# Reflection: User Authentication, Calculation BREAD and CI/CD to Docker Hub

## What I built

This module finished the back end of the calculator. I added user registration and login, with passwords hashed using bcrypt and a JWT returned on login. I added the five BREAD endpoints for calculations, each restricted to the logged-in user. I wrote 41 pytest tests that run against a real PostgreSQL database, and a GitHub Actions pipeline that tests every commit and publishes a working Docker image to Docker Hub.

## Key experiences

- **Schemas as the contract.** Keeping separate Pydantic schemas for input and output (`UserCreate` vs `UserRead`, `CalculationCreate` vs `CalculationRead`) meant the password hash can never leak into a response. Most validation also happens before my code runs. An invalid email, a weak password, an unknown operation or dividing by zero is rejected with a 422 automatically.
- **Secure password handling.** Passwords are never stored. Only a salted bcrypt hash is saved, and login compares against the hash. The login error deliberately doesn't say whether the username or the password was wrong.
- **Authorization, not just authentication.** A valid token isn't enough. Every calculation query filters on `user_id`, and asking for another user's calculation returns 404, not 403, so it doesn't reveal that the record exists. A dedicated test checks this.
- **Integration tests vs unit tests.** Unit tests check the arithmetic, but the integration tests caught the real problems: commit and refresh behavior, unique constraints, and cascade deletes. Each test can also check the database directly, for example that the stored password starts with the bcrypt `$2` prefix.
- **Pipeline gating.** The Docker push job depends on the test job (`needs: test`), so a broken commit never reaches Docker Hub. Before pushing, the pipeline also starts the built image against Postgres and calls `/health`, which proves the published image actually runs.

## Challenges and how I solved them

1. **Stale database schema.** My Postgres volume still had the `users` table from the earlier SQL assignment, which had no `password_hash` column. `create_all()` doesn't change existing tables, so registration failed with a 500 error. I fixed it by resetting the volume with `docker compose down -v`. That showed me why real projects use migrations, such as Alembic.
2. **Test isolation.** Tests that share a database can affect each other. I create the schema once per test session and run `TRUNCATE ... RESTART IDENTITY CASCADE` after each test, so every test starts empty and ids always start at 1.
3. **Partial updates and validation.** For PATCH, I couldn't check for division by zero in the schema alone, because `b` might be the only field sent while the stored type is `divide`. The route merges the update with the stored values, recomputes the result and returns 422 if it's invalid, without changing the record.
4. **Docker Hub credentials.** The pipeline needs a Docker Hub access token stored as a GitHub secret, never in the code. Creating the token with Read & Write scope and naming the secrets exactly as the workflow expects (`DOCKERHUB_USERNAME`, `DOCKERHUB_TOKEN`) fixed the login step.

## What I would improve next

- Add Alembic migrations instead of `create_all()`.
- Add refresh tokens and expiry handling on the front end (Module 13).
- Add pagination and filtering to `GET /calculations`.
