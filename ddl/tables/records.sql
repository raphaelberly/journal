
CREATE TABLE journal.records (
  insert_datetime TIMESTAMP DEFAULT now(),
  movie           VARCHAR(9),
  date            DATE,
  grade           DOUBLE PRECISION,
  id              SERIAL NOT NULL,
  username        VARCHAR(20) NOT NULL
);

ALTER TABLE journal.records ADD CONSTRAINT "records_pkey" PRIMARY KEY (username,movie);
