CREATE TABLE journal.users (
  id                    SERIAL          NOT NULL,
  username              VARCHAR(32)     NOT NULL UNIQUE,
  password_hash         VARCHAR(128)    NOT NULL,
  email                 VARCHAR(256)    NOT NULL,
  grade_as_int          BOOLEAN         NOT NULL DEFAULT TRUE,
  insert_datetime_utc   TIMESTAMP       NOT NULL DEFAULT (now() AT TIME ZONE 'utc')
);

ALTER TABLE journal.users
ADD CONSTRAINT "users_pkey"
PRIMARY KEY (id);
