CREATE TABLE journal.records(
  user_id               INTEGER             NOT NULL,
  tmdb_id               INTEGER             NOT NULL,
  grade                 DOUBLE PRECISION    NOT NULL,
  date                  DATE                NOT NULL DEFAULT DATE(now() AT TIME ZONE 'utc'),
  recent                BOOLEAN             NOT NULL DEFAULT TRUE,
  insert_datetime_utc   TIMESTAMP           NOT NULL DEFAULT (now() AT TIME ZONE 'utc')
);

ALTER TABLE journal.records
ADD CONSTRAINT "records_pkey"
PRIMARY KEY (user_id,tmdb_id);

ALTER TABLE journal.records
ADD CONSTRAINT "records_fkey_users"
FOREIGN KEY (user_id) REFERENCES journal.users (id);

ALTER TABLE journal.records
ADD CONSTRAINT "records_fkey_titles"
FOREIGN KEY (tmdb_id) REFERENCES journal.titles (id);
