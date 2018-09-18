
CREATE TABLE journal.records (
  insert_datetime TIMESTAMP DEFAULT now(),
  movie           VARCHAR(9),
    -- CONSTRAINT records_movie_fkey
    -- REFERENCES journal.titles,
  date            DATE,
  grade           DOUBLE PRECISION,
  id              SERIAL NOT NULL
    CONSTRAINT records_pkey
    PRIMARY KEY
);
