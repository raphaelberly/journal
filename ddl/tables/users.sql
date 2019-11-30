CREATE TABLE journal.users (

  insert_datetime TIMESTAMP DEFAULT now(),
  id SERIAL NOT NULL CONSTRAINT users_pkey PRIMARY KEY,
  username VARCHAR(20) NOT NULL,
  password_hash VARCHAR(100) NOT NULL,
  email TEXT NOT NULL,
  grade_as_int BOOLEAN DEFAULT TRUE NOT NULL

);
