CREATE TABLE journal.watchlist(

  insert_datetime TIMESTAMP DEFAULT NOW(),
  movie VARCHAR(9) NOT NULL,
  title TEXT NOT NULL,
  year INTEGER NOT NULL,
  genres TEXT[] NOT NULL,
  directors TEXT[] NOT NULL,
  "cast" TEXT[] NOT NULL,
  duration VARCHAR(10),
  image VARCHAR(1024),
  username VARCHAR(20) NOT NULL

);

ALTER TABLE journal.watchlist ADD CONSTRAINT "watchlist_pkey" PRIMARY KEY (username,movie);
