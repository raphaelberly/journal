CREATE TABLE journal.titles (
  id                    SERIAL,
  insert_datetime_utc   TIMESTAMP DEFAULT (now() AT TIME ZONE 'utc'),
  update_datetime_utc   TIMESTAMP DEFAULT (now() AT TIME ZONE 'utc'),
  tmdb_id               INTEGER NOT NULL,
  imdb_id               VARCHAR(32) NOT NULL,
  title                 TEXT NOT NULL,
  release_date          DATE NOT NULL,
  original_title        TEXT NOT NULL,
  original_language     VARCHAR(32),
  directors             VARCHAR(256)[],
  genres                VARCHAR(256)[],
  top_cast              VARCHAR(256)[],
  poster_url            TEXT,
  runtime               INTEGER,
  revenue               INTEGER,
  budget                INTEGER,
  tagline               TEXT
);

ALTER TABLE journal.titles
ADD CONSTRAINT "titles_pkey"
PRIMARY KEY (tmdb_id);
