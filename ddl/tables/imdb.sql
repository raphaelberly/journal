CREATE SCHEMA imdb;

CREATE TABLE imdb.persons (
  id            VARCHAR(32) NOT NULL,
  name          TEXT        NOT NULL,
  major_titles  TEXT        NULL,
  PRIMARY KEY (id)
);

CREATE TABLE imdb.titles (
  id                VARCHAR(32)  NOT NULL,
  title             TEXT         NOT NULL,
  original_title    TEXT         NULL,
  year              SMALLINT     NULL,
  type              TEXT         NOT NULL,
  genres            TEXT         NULL,
  duration          INTEGER      NULL,
  PRIMARY KEY (id)
);

CREATE TABLE imdb.crew (
  title_id  VARCHAR(32) NOT NULL,
  directors TEXT        NULL,
  writers   TEXT        NULL,
  PRIMARY KEY (title_id)
);

CREATE TABLE imdb.principals (
  title_id  VARCHAR(32) NOT NULL,
  person_id VARCHAR(32) NOT NULL,
  role      TEXT        NOT NULL
);

CREATE TABLE imdb.ratings (
  title_id  VARCHAR(32)         NOT NULL,
  rating    DOUBLE PRECISION    NOT NULL,
  votes     BIGINT              NULL,
  PRIMARY KEY (title_id)
);
