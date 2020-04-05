CREATE TABLE journal.watchlist(
  id                    SERIAL,
  insert_datetime_utc   TIMESTAMP DEFAULT (now() AT TIME ZONE 'utc'),
  username              VARCHAR(32) NOT NULL,
  tmdb_id               INTEGER NOT NULL,
  providers             VARCHAR(64)[] NOT NULL
);

ALTER TABLE journal.watchlist
ADD CONSTRAINT "watchlist_pkey"
PRIMARY KEY (username,tmdb_id);

ALTER TABLE journal.watchlist
ADD CONSTRAINT "watchlist_fkey_users"
FOREIGN KEY (username) REFERENCES journal.users (username);

ALTER TABLE journal.watchlist
ADD CONSTRAINT "watchlist_fkey_titles"
FOREIGN KEY (tmdb_id) REFERENCES journal.titles (tmdb_id);
