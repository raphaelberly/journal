
CREATE TABLE journal.records (
  insert_datetime TIMESTAMP DEFAULT now(),
  movie           VARCHAR(9),
  date            DATE,
  grade           DOUBLE PRECISION,
  id              SERIAL NOT NULL CONSTRAINT records_pkey PRIMARY KEY,
  username        VARCHAR(20) NOT NULL
);
