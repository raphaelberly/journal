CREATE TABLE journal.persons (
  id                    INTEGER         NOT NULL,
  name                  VARCHAR(128)    NOT NULL,
  gender                SMALLINT        NULL,
  insert_datetime_utc   TIMESTAMP       NOT NULL DEFAULT (now() AT TIME ZONE 'utc'),
  update_datetime_utc   TIMESTAMP       NOT NULL DEFAULT (now() AT TIME ZONE 'utc')
);

ALTER TABLE journal.persons
ADD CONSTRAINT "persons_pkey"
PRIMARY KEY (id);
