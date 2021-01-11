WITH
credits AS (
  SELECT
    c.person_id,
    c.tmdb_id,
    array_agg(c.role) AS roles
  FROM journal.credits c
  GROUP BY 1,2
)
SELECT
  c.person_id,
  c.roles,
  c.tmdb_id,
  CASE WHEN t.original_language = u.language THEN t.original_title ELSE t.title END AS title,
  date_part('year', t.release_date)::INT AS year,
  t.genres[:3] AS genres,
  r.grade,
  r.date
FROM credits c
INNER JOIN journal.records r
  ON c.tmdb_id = r.tmdb_id
INNER JOIN journal.titles t
  ON r.tmdb_id = t.id
INNER JOIN journal.users u
  ON r.user_id = u.id
  AND u.id = {user_id}
WHERE c.person_id = {person_id}
ORDER BY r.date DESC, r.grade DESC
;
