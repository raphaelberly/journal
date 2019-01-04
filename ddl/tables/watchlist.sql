CREATE TABLE journal.watchlist(

  insert_datetime TIMESTAMP DEFAULT NOW(),
  movie VARCHAR(9) NOT NULL PRIMARY KEY,
  title TEXT NOT NULL,
  year INTEGER NOT NULL,
  genres TEXT NOT NULL,
  directors TEXT[] NOT NULL,
  "cast" TEXT[] NOT NULL,
  image VARCHAR(1024),
  username VARCHAR(20) NOT NULL

);
