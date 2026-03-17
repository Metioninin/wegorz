CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS users(
    id SERIAL PRIMARY KEY NOT NULL,
    login TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    finalist BOOLEAN DEFAULT false
);
CREATE INDEX idx_users_login ON users(login);


CREATE TABLE IF NOT EXISTS sessions(
    id VARCHAR(32) PRIMARY KEY,
    user_id INT NOT NULL REFERENCES users(id)
);


CREATE TYPE code_status AS ENUM (
    'oczekiwanie na testy',
    'testowanie',
    'błąd testowania',
    'grający lub oczekujący',
    'zarchiwizowany'
);
CREATE TYPE code_lang AS ENUM('PY', 'CPP');

CREATE TABLE IF NOT EXISTS submissions(
    id SERIAL PRIMARY KEY,

    code TEXT NOT NULL,
    lang code_lang NOT NULL,

    status code_status NOT NULL DEFAULT 'oczekiwanie na testy',
    status_msg TEXT NOT NULL DEFAULT '',

    user_id INT NOT NULL REFERENCES users(id),
    send_at TIMESTAMPTZ NOT NULL DEFAULT date_trunc('seconds', now())
);
CREATE INDEX idx_submissions_user ON submissions(user_id);


CREATE TABLE IF NOT EXISTS settings(
    starts_at TIMESTAMPTZ NOT NULL,
    ends_at TIMESTAMPTZ NOT NULL,
    subms_limit INT NOT NULL,
    CONSTRAINT starts_before_ends CHECK(starts_at < ends_at)
);


INSERT INTO settings (subms_limit, starts_at, ends_at)
VALUES (25, now() - INTERVAL '60 days', now() + INTERVAL '61 days');

REVOKE INSERT, DELETE ON settings FROM PUBLIC;


-- TODO: delete when building for production
INSERT INTO users (login, password_hash) 
VALUES ('login', crypt('password', gen_salt('bf')));