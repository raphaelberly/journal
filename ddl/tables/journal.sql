CREATE SCHEMA journal;

CREATE TABLE journal.titles (
  id                    INTEGER         NOT NULL,
  imdb_id               VARCHAR(32)     UNIQUE,
  title                 TEXT            NOT NULL,
  release_date          DATE            NOT NULL,
  original_title        TEXT            NOT NULL,
  original_language     VARCHAR(32)     NOT NULL,
  director_names        VARCHAR(256)[],
  director_ids          INTEGER[],
  genres                VARCHAR(256)[],
  top_cast_names        VARCHAR(256)[],
  top_cast_ids          INTEGER[],
  poster_path           TEXT,
  runtime               SMALLINT,
  revenue               BIGINT,
  budget                BIGINT,
  tagline               TEXT,
  imdb_rating           FLOAT,
  insert_datetime_utc   TIMESTAMP       NOT NULL DEFAULT (now() AT TIME ZONE 'utc'),
  update_datetime_utc   TIMESTAMP       NOT NULL DEFAULT (now() AT TIME ZONE 'utc'),
  CONSTRAINT "titles_pkey" PRIMARY KEY (id)
);

CREATE TABLE journal.persons (
  id                    INTEGER         NOT NULL,
  name                  VARCHAR(128)    NOT NULL,
  gender                SMALLINT        NULL,
  profile_path          TEXT            NULL,
  insert_datetime_utc   TIMESTAMP       NOT NULL DEFAULT (now() AT TIME ZONE 'utc'),
  update_datetime_utc   TIMESTAMP       NOT NULL DEFAULT (now() AT TIME ZONE 'utc'),
  CONSTRAINT "persons_pkey" PRIMARY KEY (id)
);

CREATE TABLE journal.credits (
  id                    VARCHAR(128)    NOT NULL,
  tmdb_id               INTEGER         NOT NULL,
  person_id             INTEGER         NOT NULL,
  role                  VARCHAR(128)    NOT NULL,
  cast_rank             SMALLINT        NULL,
  insert_datetime_utc   TIMESTAMP       NOT NULL DEFAULT (now() AT TIME ZONE 'utc'),
  update_datetime_utc   TIMESTAMP       NOT NULL DEFAULT (now() AT TIME ZONE 'utc'),
  CONSTRAINT "credits_pkey" PRIMARY KEY (id),
  CONSTRAINT "credits_fkey_titles" FOREIGN KEY (tmdb_id) REFERENCES imdb.titles (id),
  CONSTRAINT "credits_fkey_persons" FOREIGN KEY (person_id) REFERENCES imdb.persons (id)
);

CREATE TABLE journal.users (
  id                    SERIAL          NOT NULL,
  username              VARCHAR(32)     NOT NULL UNIQUE,
  password_hash         VARCHAR(128)    NOT NULL,
  email                 VARCHAR(256)    NOT NULL,
  grade_as_int          BOOLEAN         NOT NULL DEFAULT TRUE,
  language              VARCHAR(4)      NOT NULL DEFAULT 'fr',
  insert_datetime_utc   TIMESTAMP       NOT NULL DEFAULT (now() AT TIME ZONE 'utc'),
  update_datetime_utc   TIMESTAMP       NOT NULL DEFAULT (now() AT TIME ZONE 'utc'),
  CONSTRAINT "users_pkey" PRIMARY KEY (id)
);

CREATE TABLE journal.watchlist(
  user_id               INTEGER         NOT NULL,
  tmdb_id               INTEGER         NOT NULL,
  providers             VARCHAR(64)[]   NOT NULL,
  insert_datetime_utc   TIMESTAMP       NOT NULL DEFAULT (now() AT TIME ZONE 'utc'),
  update_datetime_utc   TIMESTAMP       NOT NULL DEFAULT (now() AT TIME ZONE 'utc'),
  CONSTRAINT "watchlist_pkey" PRIMARY KEY (user_id,tmdb_id),
  CONSTRAINT "watchlist_fkey_users" FOREIGN KEY (user_id) REFERENCES imdb.users (id),
  CONSTRAINT "watchlist_fkey_titles" FOREIGN KEY (tmdb_id) REFERENCES imdb.titles (id)
);

CREATE TABLE journal.records(
  user_id                   INTEGER             NOT NULL,
  tmdb_id                   INTEGER             NOT NULL,
  grade                     DOUBLE PRECISION    NOT NULL,
  date                      DATE                NOT NULL DEFAULT DATE(now() AT TIME ZONE 'utc'),
  include_in_recent         BOOLEAN             NOT NULL DEFAULT TRUE,
  include_in_top_persons    BOOLEAN             NOT NULL DEFAULT TRUE,
  insert_datetime_utc       TIMESTAMP           NOT NULL DEFAULT (now() AT TIME ZONE 'utc'),
  update_datetime_utc       TIMESTAMP           NOT NULL DEFAULT (now() AT TIME ZONE 'utc'),
  CONSTRAINT "records_pkey" PRIMARY KEY (user_id,tmdb_id),
  CONSTRAINT "records_fkey_users" FOREIGN KEY (user_id) REFERENCES imdb.users (id),
  CONSTRAINT "records_fkey_titles" FOREIGN KEY (tmdb_id) REFERENCES imdb.titles (id)
);
