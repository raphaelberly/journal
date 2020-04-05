CREATE TABLE journal.records(
  id                    SERIAL,
  insert_datetime_utc   TIMESTAMP DEFAULT (now() AT TIME ZONE 'utc'),
  username              VARCHAR(32) NOT NULL,
  tmdb_id               INTEGER NOT NULL,
  imdb_id               VARCHAR(32) NOT NULL,
  grade                 DOUBLE PRECISION NOT NULL,
  date                  DATE DEFAULT DATE(now() AT TIME ZONE 'utc'),
  recent                BOOLEAN DEFAULT TRUE
);

ALTER TABLE journal.records
ADD CONSTRAINT "records_pkey"
PRIMARY KEY (username,tmdb_id);

ALTER TABLE journal.records
ADD CONSTRAINT "records_fkey_users"
FOREIGN KEY (username) REFERENCES journal.users (username);

ALTER TABLE journal.records
ADD CONSTRAINT "records_fkey_titles"
FOREIGN KEY (tmdb_id) REFERENCES journal.titles (tmdb_id);
