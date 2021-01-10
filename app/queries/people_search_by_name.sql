WITH
search AS (
  SELECT
    p.id AS person_id,
    round(ts_rank(to_tsvector(p.name), to_tsquery('{query}'))::NUMERIC, 5) AS score
  FROM journal.persons p
),
search_filtered AS (
  SELECT
    s.*,
    rank() OVER (ORDER BY s.score DESC, s.person_id) AS rank
  FROM search s
  WHERE s.score > 0.05
),
credits AS (
  SELECT
    c.person_id,
    c.tmdb_id,
    array_agg(c.role) AS roles
  FROM journal.credits c
  GROUP BY 1,2
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
  AND u.id = {user_id}
WHERE s.rank = 1
ORDER BY r.date DESC, r.grade DESC
;
