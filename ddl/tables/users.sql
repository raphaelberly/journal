CREATE TABLE journal.users (
  id                    SERIAL,
  insert_datetime_utc   TIMESTAMP DEFAULT (now() AT TIME ZONE 'utc'),
  username              VARCHAR(32) NOT NULL,
  password_hash         VARCHAR(128) NOT NULL,
  email                 VARCHAR(256) NOT NULL,
  grade_as_int          BOOLEAN DEFAULT TRUE
);

ALTER TABLE journal.users
ADD CONSTRAINT "users_pkey"
PRIMARY KEY (username);
