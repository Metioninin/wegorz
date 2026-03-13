CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS users(
    login TEXT PRIMARY KEY NOT NULL,
    password_hash TEXT NOT NULL
);


CREATE TABLE IF NOT EXISTS sessions(
    id VARCHAR(32) PRIMARY KEY,
    login TEXT NOT NULL REFERENCES users(login)
);

-- TODO: delete when building for production
INSERT INTO users (login, password_hash) 
VALUES ('login', crypt('password', gen_salt('bf')));