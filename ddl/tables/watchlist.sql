CREATE TABLE journal.watchlist(
  user_id               INTEGER         NOT NULL,
  tmdb_id               INTEGER         NOT NULL,
  providers             VARCHAR(64)[]   NOT NULL,
  insert_datetime_utc   TIMESTAMP       NOT NULL DEFAULT (now() AT TIME ZONE 'utc')
);

ALTER TABLE journal.watchlist
ADD CONSTRAINT "watchlist_pkey"
PRIMARY KEY (user_id,tmdb_id);

ALTER TABLE journal.watchlist
ADD CONSTRAINT "watchlist_fkey_users"
FOREIGN KEY (user_id) REFERENCES journal.users (id);

ALTER TABLE journal.watchlist
ADD CONSTRAINT "watchlist_fkey_titles"
FOREIGN KEY (tmdb_id) REFERENCES journal.titles (id);
