CREATE TABLE journal.credits (
  id                    VARCHAR(128)    NOT NULL,
  tmdb_id               INTEGER         NOT NULL,
  person_id             INTEGER         NOT NULL,
  role                  VARCHAR(128)    NOT NULL,
  cast_rank             SMALLINT        NULL,
  insert_datetime_utc   TIMESTAMP       NOT NULL DEFAULT (now() AT TIME ZONE 'utc'),
  update_datetime_utc   TIMESTAMP       NOT NULL DEFAULT (now() AT TIME ZONE 'utc')
);

ALTER TABLE journal.credits
ADD CONSTRAINT "credits_pkey"
PRIMARY KEY (id);

ALTER TABLE journal.credits
ADD CONSTRAINT "credits_fkey_titles"
FOREIGN KEY (tmdb_id) REFERENCES journal.titles (id);

ALTER TABLE journal.credits
ADD CONSTRAINT "credits_fkey_persons"
FOREIGN KEY (person_id) REFERENCES journal.persons (id);
