CREATE TABLE journal.titles (
  id                    INTEGER         NOT NULL,
  imdb_id               VARCHAR(32)     NOT NULL UNIQUE,
  title                 TEXT            NOT NULL,
  release_date          DATE            NOT NULL,
  original_title        TEXT            NOT NULL,
  original_language     VARCHAR(32)     NOT NULL,
  directors             VARCHAR(256)[],
  genres                VARCHAR(256)[],
  top_cast              VARCHAR(256)[],
  poster_path           TEXT,
  runtime               INTEGER,
  revenue               INTEGER,
  budget                INTEGER,
  tagline               TEXT,
  insert_datetime_utc   TIMESTAMP       NOT NULL DEFAULT (now() AT TIME ZONE 'utc'),
  update_datetime_utc   TIMESTAMP       NOT NULL DEFAULT (now() AT TIME ZONE 'utc')
);

ALTER TABLE journal.titles
ADD CONSTRAINT "titles_pkey"
PRIMARY KEY (id);
