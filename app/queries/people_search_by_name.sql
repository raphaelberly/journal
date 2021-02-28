WITH
credits AS (
  SELECT
    c.person_id,
    c.tmdb_id,
    array_agg(c.role) AS roles
  FROM journal.credits c
  GROUP BY 1,2
),
counts AS (
  SELECT
    c.person_id,
    count(DISTINCT c.tmdb_id) AS movie_count
  FROM journal.credits c
  INNER JOIN journal.records r
    ON c.tmdb_id = r.tmdb_id
    AND r.user_id = {user_id}
  GROUP BY 1
),
search AS (
  SELECT
    p.id                                                                    AS person_id,
    round(ts_rank(to_tsvector(p.name), to_tsquery('{query}'))::NUMERIC, 5)  AS score
  FROM journal.persons p
),
search_filtered AS (
  SELECT
    s.person_id
  FROM search s
  INNER JOIN counts p
    ON s.person_id = p.person_id
  ORDER BY s.score DESC, p.movie_count DESC
  LIMIT 1
)
SELECT
  s.person_id,
  c.roles,
  c.tmdb_id,
  CASE WHEN t.original_language = u.language THEN t.original_title ELSE t.title END AS title,
  date_part('year', t.release_date)::INT AS year,
  t.genres[:3] AS genres,
  r.grade,
  r.date
FROM search_filtered s
INNER JOIN credits c
  ON s.person_id = c.person_id
INNER JOIN journal.records r
  ON c.tmdb_id = r.tmdb_id
INNER JOIN journal.titles t
  ON r.tmdb_id = t.id
INNER JOIN journal.users u
  ON r.user_id = u.id
WHERE u.id = {user_id}
ORDER BY r.date DESC, r.insert_datetime_utc DESC
;
