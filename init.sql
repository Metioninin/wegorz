CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS users(
    id SERIAL PRIMARY KEY,

    login TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL
);


CREATE TABLE IF NOT EXISTS sessions(
    id VARCHAR(32) PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id)
);

-- TODO: delete when building for production
INSERT INTO users (login, password_hash) 
VALUES ('login', crypt('password', gen_salt('md5')));