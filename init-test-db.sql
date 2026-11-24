-- Runs once when the Postgres volume is first created.
-- Gives the test suite its own database so tests never touch fastapi_db.
CREATE DATABASE fastapi_test_db;
