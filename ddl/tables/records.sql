
CREATE TABLE journal.records (
  insert_datetime TIMESTAMP DEFAULT now(),
  movie           VARCHAR(12) NOT NULL,
  tmdb_id         INTEGER NOT NULL,
  date            DATE NOT NULL,
  grade           DOUBLE PRECISION NOT NULL,
  id              SERIAL NOT NULL,
  username        VARCHAR(20) NOT NULL,
  recent          BOOLEAN NOT NULL DEFAULT TRUE
);

ALTER TABLE journal.records ADD CONSTRAINT "records_pkey" PRIMARY KEY (username,movie);
