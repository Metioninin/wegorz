CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS users(
    id SERIAL PRIMARY KEY NOT NULL,

    login TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,

    qualified BOOLEAN DEFAULT false
);
CREATE INDEX idx_users_login ON users(login);


CREATE TABLE IF NOT EXISTS sessions(
    id VARCHAR(32) PRIMARY KEY,
    user_id INT NOT NULL REFERENCES users(id)
);


CREATE TABLE IF NOT EXISTS rounds(
    id SERIAL PRIMARY KEY,

    title TEXT NOT NULL,
    description TEXT NOT NULL,

    subms_limit INT NOT NULL,
    statement_name TEXT NOT NULL,

    starts_at TIMESTAMPTZ NOT NULL,
    ends_at TIMESTAMPTZ NOT NULL,
    restricted BOOLEAN NOT NULL,

    CONSTRAINT starts_before_ends CHECK(starts_at < ends_at)
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
    round_id INT NOT NULL REFERENCES rounds(id),
    send_at TIMESTAMPTZ NOT NULL DEFAULT date_trunc('seconds', now())
);
CREATE INDEX idx_submissions_user ON submissions(user_id);


-- TODO: adjust dates, times, pdfs
INSERT INTO rounds (title, description, starts_at, ends_at, subms_limit, statement_name, restricted)
VALUES 
    ('Runda próbna', '', '2026-03-29T15:00:00+01:00', '2026-03-29T23:59:59+01:00', 25, 'probna.pdf', false),
    ('Runda główna', '', '2026-03-30T15:00:00+01:00', '2026-03-31T23:59:59+01:00', 25, 'glowna.pdf', false),
    ('Finał', '', '2026-04-01T00:00:00Z', '2026-04-01T23:59:59Z', 25, 'final.pdf', true);


-- TODO: prepare this for production
INSERT INTO users (login, password_hash) 
VALUES ('login', crypt('password', gen_salt('bf')));