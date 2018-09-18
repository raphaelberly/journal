
CREATE TABLE journal.crew (
  movie     TEXT,
  directors TEXT,
  writers   TEXT
);

CREATE TABLE journal.names (
  person       TEXT,
  name         TEXT,
  major_titles TEXT
);

CREATE TABLE journal.principals (
  movie  TEXT,
  person TEXT,
  role   TEXT
);

CREATE TABLE journal.ratings (
  rating DOUBLE PRECISION,
  movie  TEXT,
  votes  BIGINT
);

CREATE TABLE journal.titles (
  year     bigint,
  movie    TEXT NOT NULL
    CONSTRAINT titles_pkey
    PRIMARY KEY,
  title    TEXT,
  genres   TEXT,
  type     TEXT,
  duration TEXT
);
