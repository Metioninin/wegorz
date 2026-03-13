CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS users(
    login TEXT PRIMARY KEY NOT NULL,
    password_hash TEXT NOT NULL,
    finalist BOOLEAN DEFAULT false
);


CREATE TABLE IF NOT EXISTS sessions(
    id VARCHAR(32) PRIMARY KEY,
    login TEXT NOT NULL REFERENCES users(login)
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

    user_id TEXT NOT NULL REFERENCES users(login),
    send_at TIMESTAMPTZ NOT NULL DEFAULT date_trunc('seconds', now())
);
CREATE INDEX idx_submissions_user ON submissions(user_id);


-- TODO: delete when building for production
INSERT INTO users (login, password_hash) 
VALUES ('login', crypt('password', gen_salt('bf')));