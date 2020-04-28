WITH
user_records AS (
  SELECT *
  FROM journal.records r
  WHERE r.username = '{{username}}'
),
crew AS (
  SELECT
    c.movie,
    c.directors
  FROM journal.crew c
  INNER JOIN user_records r
    USING(movie)
),
unnested_crew AS (
  SELECT
    c.movie,
    unnest(string_to_array(c.directors, ',')) AS directors
  FROM crew c
),
named_crew AS (
  SELECT
    uc.movie,
    string_agg(n.name, ',') AS directors
  FROM unnested_crew uc
  INNER JOIN journal.names n
    ON uc.directors = n.person
  GROUP BY 1
)
SELECT
  r.movie AS imdb_id,
  r.tmdb_id AS tmdb_id,
  t.title,
  t.year,
  t.genres,
  c.directors,
  ra.rating AS imdb_rating,
  ra.votes AS imdb_votes,
  r.date,
  r.grade,
  r.recent AS show_in_recent_page
FROM user_records r
INNER JOIN journal.titles t
  USING(movie)
INNER JOIN journal.ratings ra
  USING(movie)
LEFT JOIN named_crew c
  USING(movie)
